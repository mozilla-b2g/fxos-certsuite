# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import Queue
import json
import logging
import os
import sys
import unittest
import uuid

from tornado import web
from tornado.ioloop import IOLoop
import tornado.httpserver
import tornado.websocket


static_dir = os.path.join(os.path.dirname(__file__), "static")
timeout = 3
logger = logging.getLogger(__name__)
clients = Queue.Queue()


def static_path(path):
    return os.path.join(static_dir, path)


class NoCacheStaticFileHandler(web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")


class FrontendServer(object):
    def __init__(self, addr, io_loop=None, verbose=False):
        self.addr = addr
        self.io_loop = io_loop or IOLoop.instance()
        self.started = False
        if verbose:
            logger.setLevel(logging.DEBUG)

        self.routes = tornado.web.Application(
            [(r"/tests", TestHandler),
             (r"/", web.RedirectHandler, {"url": "/app.html"}),
             (r"/(.*[html|css|js])$", NoCacheStaticFileHandler,
              {"path": static_dir})])
        self.server = tornado.httpserver.HTTPServer(
            self.routes, io_loop=self.io_loop)

    def start(self):
        """Start blocking FrontendServer."""
        self.started = True
        self.server.listen(self.addr[1])
        self.io_loop.start()

    def stop(self):
        if not self.server:
            return
        self.server.stop()

    def is_alive(self):
        return self.started


# Not currently in use, but offers a more foolproof way of emitting
# messages to connections:
class HandlerMixin(object):
    handlers = []

    def add(self, handler, callback):
        self.handlers.append(callback)

        # Hack:
        global clients
        clients.put(handler)

    def emit(self, event, data):
        for cb in self.handlers:
            cb(event, data)


class BlockingPromptMixin(object):
    def __init__(self):
        self.response = Queue.Queue()

    def get_response(self):
        # TODO(ato): Use timeout from semiauto.testcase
        return self.response.get(block=True, timeout=sys.maxint)

    def confirmation(self, question):
        self.emit("confirmPrompt", question)
        resp = self.get_response()
        return True if "confirmPromptOk" in resp else False

    def prompt(self, question):
        self.emit("prompt", question)
        resp = self.get_response()
        return resp["prompt"] if "prompt" in resp else False

    def instruction(self, instruction):
        self.emit("instructPrompt", instruction)
        resp = self.get_response()
        return True if "instructPromptOk" in resp else False


class TestHandler(tornado.websocket.WebSocketHandler,
                  BlockingPromptMixin, HandlerMixin):
    def __init__(self, *args, **kwargs):
        super(TestHandler, self).__init__(*args, **kwargs)
        self.id = None
        self.suite = unittest.TestSuite()
        self.connected = False

    def open(self, *args):
        self.id = uuid.uuid4()
        self.stream.set_nodelay(True)
        self.add(self, self.async_callback(self.emit))
        self.connected = True
        logger.info("Accepted new client: %s" % self)

    def on_close(self):
        self.connected = False
        # Confirmation prompts blocks the handler, and this will
        # release the blocking queue get in
        # BlockingPromptMixin.get_response.
        self.response.put({})
        logger.info("Client left: %s" % self)

    def emit(self, event, data=None):
        command = {event: data}
        payload = json.dumps(command)
        logger.info("Sending %s" % payload)
        self.write_message(payload)

    # TODO(ato): What does this do?
    def handle_event(self, event, data):
        print("event: %r" % event)
        print(" data: %s" % data)

    def on_message(self, payload):
        message = json.loads(payload)
        self.response.put(message)
        logger.info("Received %s" % payload)

    def __str__(self):
        return str(self.id)


def wait_for_client():
    """Wait for client to connect the host browser and return.

    Gets a reference to the WebSocket handler associated with that client that
    we can use to communicate with the browser.  This blocks until a client
    connects.

    """

    # A timeout is needed because of http://bugs.python.org/issue1360
    return clients.get(block=True, timeout=sys.maxint)
