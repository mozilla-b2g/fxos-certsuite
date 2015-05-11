#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import threading

from mozlog.structured import structuredlog
from tornado.ioloop import IOLoop

from server import FrontendServer

"""Used to hold a TestEnvironment in a static field."""
env = None


class EnvironmentError(Exception):
    pass


def get(environ, *args, **kwargs):
    global env
    if not env:
        env = environ(*args, **kwargs)
        env.start()
    assert env.is_alive()

    timeout = kwargs.pop("timeout", 10)
    wait = 0
    if not env.server.is_alive() and wait < timeout:
        wait += 0.1
        time.sleep(wait)

    if not env.server.is_alive():
        raise EnvironmentError("Starting server failed")

    return env


class InProcessTestEnvironment(object):
    def __init__(self, addr=None, server_cls=None, io_loop=None, verbose=False):
        self.io_loop = io_loop or IOLoop()
        self.started = False
        self.handler = None
        if addr is None:
            addr = ("127.0.0.1", 0)
        if server_cls is None:
            server_cls = FrontendServer
        self.server = server_cls(addr, io_loop=self.io_loop,
                                 verbose=verbose)

    def start(self, block=False):
        """Start the test environment.

        :param block: True to run the server on the current thread,
            blocking, False to run on a separate thread.

        """

        self.started = True
        if block:
            self.server.start()
        else:
            self.server_thread = threading.Thread(target=self.server.start)
            self.server_thread.daemon = True  # don't hang on exit
            self.server_thread.start()

    def stop(self):
        """Stop the test environment. If the test environment is
        not running, this method has no effect."""
        if self.started:
            try:
                self.server.stop()
                self.server_thread.join()
                self.server_thread = None
            except AttributeError:
                pass
            self.started = False
        self.server = None

    def is_alive(self):
        return self.started


if __name__ == "__main__":
    structuredlog.set_default_logger()

    env = InProcessTestEnvironment()
    print("Listening on %s" % ":".join(str(i) for i in env.server.addr))
    # We ask the environment to block here so that the program won't
    # end immediately.
    env.start(block=True)
