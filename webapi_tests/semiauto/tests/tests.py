# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from tornado import testing
import sys
import threading
import tornado

from marionette import Marionette, MarionetteException

from semiauto import environment
from semiauto.environment import InProcessTestEnvironment


"""The default time to wait for a user to respond to a prompt or
instruction in a test."""
prompt_timeout = 600  # 10 minutes


# TODO(ato): Find better name: interaction_test? interact?
def test(*args, **kwargs):
    """Wraps ``tornado.testing.gen_test``."""
    timeout = kwargs.get("timeout", prompt_timeout)
    return tornado.testing.gen_test(timeout=timeout, *args, **kwargs)


class TestCase(tornado.testing.AsyncTestCase):
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

    @tornado.gen.coroutine
    def use_cert_app(self):
        # app management is done in the system app
        self.marionette.switch_to_frame()
        self.marionette.import_script("semiauto/tests/app_management.js")
        script = "GaiaApps.launchWithName('CertTest App');"
        try:
            self.cert_test_app = self.marionette.execute_async_script(script, script_timeout=5000)
            self.marionette.switch_to_frame(self.cert_test_app["frame"])
            self.assertTrue('certtest' in self.marionette.get_url())
        except MarionetteException as e:
            ok = yield self.instruct("Could not launch CertTest app automatically." \
                                     "Please launch by hand then hit OK to continue.")
            self.assertTrue(ok, "Could not launch CertTest app")
        except Exception as e:
            message = "Unexpected exception: %s" % e
            yield self.instruct(message)
            self.fail(message)

    # TODO(ato): Cross reference and update against fxos-certsuite
    @tornado.gen.coroutine
    def close_cert_app(self):
        self.marionette.import_script("semiauto/tests/app_management.js")
        # app management is done in the system app
        self.marionette.switch_to_frame()
        script = "GaiaApps.kill('%s');" % self.cert_test_app["origin"]
        try:
            self.marionette.execute_async_script(script, script_timeout=5000)
            self.assertTrue('certtest' not in self.marionette.get_url())
        except MarionetteException as e:
            ok = yield self.instruct("Could not close CertTest app automatically." \
                                     "Please close by hand then hit OK to continue.")
            self.assertTrue(ok, "Could not close CertTest app")
        except Exception as e:
            message = "Unexpected exception: %s" % e
            yield self.instruct(message)
            self.fail(message)

    def get_new_ioloop(self):
        """Retreives the singleton ``tornado.ioloop.IOLoop`` instance."""

        if not hasattr(self, "io_loop"):
            self.io_loop = tornado.ioloop.IOLoop.instance()
        return self.io_loop

    def prompt(self, message):
        """Prompt the user for a reply.  Returns a future which must be
        yielded.

        This will trigger an overlay  in the host browser window
        which can be used to tell the user to perform an action or to
        input some manual data for us to work on.

        Sample usage::

            answer = yield prompt("What's the meaning of life?")
            assert answer == 42

        This function is a simple wrapper for ``tornado.gen.Task``,
        and is equivalent to the usage of that.

        :param message: The question to ask or message to give the
            user.

        :returns: A generator which must be yielded. Once yielded,
                  the return value will be the value of the prompt,
                  or False if the user hit 'Cancel'

        """

        return tornado.gen.Task(self.handler.get_user_input, message)

    def instruct(self, message):
        """Presents the user with an instruction.  Returns a future which
        must be yielded.

        This will trigger an overlay in the host browser window
        which can be used to tell the user to perform an action or to
        input some manual data for us to work on.

        Sample usage::

            answer = yield prompt("What's the meaning of life?")
            assert answer == 42

        This function is a simple wrapper for ``tornado.gen.Task``,
        and is equivalent to the usage of that.

        :param message: The instruction you want to give the user

        :returns: A generator which must be yielded. Once yielded,
                  the reutrn value will be either True if they
                  succeeded or False if they did not.

        """

        return tornado.gen.Task(self.handler.instruct_user, message)
