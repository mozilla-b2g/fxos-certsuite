# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import threading

from tornado import testing
import tornado

from marionette import Marionette, MarionetteException

from semiauto import environment
from semiauto.environment import InProcessTestEnvironment

from certapp import CertAppMixin


"""The default time to wait for a user to respond to a prompt or
instruction in a test."""
prompt_timeout = 600  # 10 minutes


# TODO(ato): Find better name: interaction_test? interact?
def test(*args, **kwargs):
    """Wraps ``tornado.testing.gen_test``."""
    timeout = kwargs.get("timeout", prompt_timeout)
    return tornado.testing.gen_test(timeout=timeout, *args, **kwargs)


class TestCase(tornado.testing.AsyncTestCase, CertAppMixin):
    app_management = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../../webapi_tests/app_management.js"))
    stored = threading.local()

    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop("config")
        #self.handler = kwargs.pop('handler')
        #self.io_loop = kwargs.pop('io_loop')

        super(TestCase, self).__init__(*args, **kwargs)
        self.io_loop = self.get_new_ioloop()
        self.stored.handler = None
        self.stored.marionette = None

    def setUp(self):
        """Sets up the environment for a test case.

        Retreive already running test environment, or create a new one if
        one doesn't exist.  A test environment consists of a web
        server with HTTP and WebSocket handlers which tests can access
        through ``self.handler``.

        Then set up a Marionette session to the connected device if
        one does not already exist.  This is assigned to
        ``self.marionette``.  Marionette can be used to remote control
        the device.

        """

        super(TestCase, self).setUp()
        self.environment = environment.get(InProcessTestEnvironment)
        self.server = self.environment.server
        self.handler = self.environment.handler
        self.marionette = self.create_marionette()
        self.io_loop.run_sync(self.use_cert_app)

    def tearDown(self):
        self.io_loop.run_sync(self.close_cert_app)
        super(TestCase, self).tearDown()

    @staticmethod
    def create_marionette():
        """Creates a new Marionette session if one does not exist."""

        m = TestCase.stored.marionette

        if not m:
            m = Marionette()
            m.start_session()
            TestCase.stored.marionette = m

        return TestCase.stored.marionette

    def get_new_ioloop(self):
        """Retreives the singleton ``tornado.ioloop.IOLoop`` instance."""

        if not hasattr(self, "io_loop"):
            self.io_loop = tornado.ioloop.IOLoop.instance()
        return self.io_loop

    def prompt(self, message, style=None):
        """Prompt the user for a response.  Returns a future which must be
        yielded.

        This will trigger an overlay in the host browser window which
        can be used to tell the user to perform an action or to input
        some manual data for us to work on.

        This will block until the user responds.

        Sample usage::

            answer = yield self.prompt("What's the meaning of life?")
            assert answer == "42"

        This function is a wrapper for ``tornado.gen.Task``, and is
        equivalent to the usage of that.

        :param message: The question to ask or message to give the
            user.

        :returns: A generator which must be yielded.  Once yielded,
            the return value will be the input from the user, or False
            if the user hit "Cancel".

        """

        if not style:
            style = self.handler.get_user_input
        return tornado.gen.Task(style, message)

    def confirm(self, message):
        """Ask user to confirm a physical aspect about the device or the
        testing environment that cannot be checked by the test.

        An example of this would be the phone vibrating::

            vibrate()
            did_vibrate = yield self.confirm("Did you feel a vibration?")
            assert did_vibrate

        If the result of the confirmation is negative (false, no) the
        test will be failed.

        :param message: The confirmation to send to the user.

        """

        raise NotImplemented

    def instruct(self, message):
        """Instruct the user to do an action, such as rotating the phone.

        This will trigger an overlay in the host browser window which
        can be used to tell the user to perform an action.

        Sample usage::

            self.instruct("Rotate the phone 90 degrees")
            assert phone_rotation_changed()

        If the user informs us she failed to perform the instruction,
        the test will be failed.

        This function is a simple wrapper for ``tornado.gen.Task``,
        and is equivalent to the usage of that.

        :param message: The instruction you want to give the user.

        """

        successful = yield prompt(message, style=self.handler.instruct_user)
        if not successful:
            self.fail("Failed on instruction: %s" % message)
