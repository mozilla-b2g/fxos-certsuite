# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import Queue
import json
import os
import sys
import unittest
import uuid
import time

from tornado import web
from tornado.ioloop import IOLoop
import tornado.httpserver
import tornado.websocket

from mozlog.structured import get_default_logger
from mozlog.structured import handlers

static_dir = os.path.join(os.path.dirname(__file__), "static")
clients = Queue.Queue()
connect_timeout = 30
logger = None

class WSHandler(handlers.BaseHandler):
    """Sends test results over WebSocket to the host browser."""

    def __init__(self, transport):
        self.transport = transport

    def __call__(self, data):
        if (("component" not in data or data["component"] is None)
            and data["action"] != "log"):
            self.transport.emit(data)

def static_path(path):
    return os.path.join(static_dir, path)


class NoCacheStaticFileHandler(web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")


class FrontendServer(object):
    def __init__(self, addr, io_loop=None, verbose=False):
        self._addr = addr
        self.io_loop = io_loop or IOLoop.instance()
        self.started = False
        global logger
        logger = get_default_logger()

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
        self.server.listen(self._addr[1], address=self._addr[0])
        self.io_loop.start()

    def stop(self):
        if not self.server:
            return
        self.server.stop()

    def is_alive(self):
        return self.started

    @property
    def addr(self):
        # tornado doesn't guarantee that HTTPServer.listen listens
        # before it returns, hence leaving its _socket property
        # unpopulated until its subprocesses have bound properly.
        assert self.is_alive()
        while len(self.server._sockets) == 0:
            time.sleep(0.01)
        return self.server._sockets.itervalues().next().getsockname()


class BlockingPromptMixin(object):
    def __init__(self):
        self.response = Queue.Queue()

    def get_response(self):
        # TODO(ato): Use timeout from webapi_tests.semiauto.testcase
        return self.response.get(block=True, timeout=sys.maxint)

    def confirmation(self, question):
        self.emit({"action": "confirm_prompt", "question": question})
        resp = self.get_response()
        return True if "confirm_prompt_ok" in resp else False

    def prompt(self, message):
        self.emit({"action": "prompt", "message": message})
        resp = self.get_response()
        return resp["prompt"] if "prompt" in resp else False

    def instruction(self, instruction):
        self.emit({"action": "instruct_prompt", "instruction": instruction})
        resp = self.get_response()
        return True if "instruct_prompt_ok" in resp else False


class TestHandler(tornado.websocket.WebSocketHandler,
                  BlockingPromptMixin):
    def __init__(self, *args, **kwargs):
        super(TestHandler, self).__init__(*args, **kwargs)
        self.id = None
        self.suite = unittest.TestSuite()
        self.connected = False
        self.msg_handler = WSHandler(self)

    def open(self, *args):
        self.id = uuid.uuid4()
        self.stream.set_nodelay(True)
        self.connected = True

        # Hack:
        global clients
        clients.put(self)

        logger.add_handler(self.msg_handler)

        logger.debug("Accepted new client: %s" % self)

    def on_close(self):
        logger.remove_handler(self.msg_handler)
        self.connected = False
        # Confirmation prompts blocks the handler, and this will
        # release the blocking queue get in
        # BlockingPromptMixin.get_response.
        self.response.put({})
        logger.debug("Client left: %s" % self)

    def emit(self, message):
        # Note: don't log here since this function is called from a
        # log handler and the logger will deadlock.
        payload = json.dumps(message)
        self.write_message(payload)

    def on_message(self, payload):
        message = json.loads(payload)
        self.response.put(message)
        logger.debug("Received %s" % payload)

    def __str__(self):
        return str(self.id)


class ConnectError(RuntimeError):
    pass


def wait_for_client():
    """Wait for client to connect the host browser and return.

    Gets a reference to the WebSocket handler associated with that client that
    we can use to communicate with the browser.  This blocks until a client
    connects, or ``server.connect_timeout`` is reached and a ``ConnectError``
    is raised."""

    try:
        logger.debug("Waiting for client")
        rv = clients.get(block=True, timeout=connect_timeout)
        logger.debug("Got client")
        return rv
    except Queue.Empty:
        raise ConnectError("Browser connection not made in time")
