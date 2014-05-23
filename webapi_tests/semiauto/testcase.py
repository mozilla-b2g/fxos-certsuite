# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import threading
import unittest

from marionette import Marionette, MarionetteException

from semiauto import environment
from semiauto.environment import InProcessTestEnvironment

from certapp import CertAppMixin


"""The default time to wait for a user to respond to a prompt or
instruction in a test."""
prompt_timeout = 600  # 10 minutes


class TestCase(CertAppMixin, unittest.TestCase):
    stored = threading.local()

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.stored.handler = None
        self.stored.marionette = None

        # Cleanups are run irrespective of whether setUp fails
        self.addCleanup(self.close_cert_app)

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

        self.assert_browser_connected()

        self.marionette = self.create_marionette()
        turn_screen_on(self.marionette)
        unlock_screen(self.marionette)

        # Make sure we don't reuse the certapp context from a previous
        # testrun that was interrupted and left the certapp open.
        self.close_cert_app()
        self.use_cert_app()

    def assert_browser_connected(self):
        """Asserts (and consequently fails the test if not true) that the
        browser is connected to the semiauto test harness.

        """

        self.assertTrue(self.handler.connected, "Browser disconnected")

    @staticmethod
    def create_marionette():
        """Creates a new Marionette session if one does not exist."""

        m = TestCase.stored.marionette

        if not m:
            m = Marionette()
            m.start_session()
            TestCase.stored.marionette = m

        return TestCase.stored.marionette

    def prompt(self, question):
        """Prompt the user for a response.  Returns a future which must be
        yielded.

        This will trigger an overlay in the host browser window which
        can be used to tell the user to perform an action or to input
        some manual data for us to work on.

        This will block until the user responds.

        Sample usage::

            answer = self.prompt("What's the meaning of life?")
            assert answer == "42"

        :param message: The question to ask or message to give the
            user.

        :returns: The input from the user as a string, or False if the
            user hit "Cancel".

        """

        resp = self.handler.prompt(question)
        if type(resp) == bool and not resp:
            self.fail("Failed on prompt cancel: %s" % question)
        return resp

    def confirm(self, message):
        """Ask user to confirm a physical aspect about the device or the
        testing environment that cannot be checked by the test.

        An example of this would be the phone vibrating::

            vibrate()
            did_vibrate = self.confirm("Did you feel a vibration?")
            assert did_vibrate

        If the result of the confirmation is negative (false, no) the
        test will be failed.

        :param message: The confirmation to send to the user.

        """

        success = self.handler.confirmation(message)
        if not success:
            self.fail("Failed on confirmation: %s" % message)

    def instruct(self, message):
        """Instruct the user to perform an action, such as rotating the phone.

        This will present an overlay in the host browser window where
        the user can indicate whether she was successful in carrying
        out the instruction.

        Sample usage::

            self.instruct("Rotate the phone 90 degrees")
            assert phone_rotation_changed()

        If the user informs us she failed to perform the instruction,
        the test will be failed.

        :param message: The instruction you want to give the user.

        """

        success = self.handler.instruction(message)
        if not success:
            self.fail("Failed on instruction: %s" % message)


def turn_screen_on(marionette):
    marionette.execute_script("""
        var screenManager = window.wrappedJSObject.ScreenManager;
        screenManager.turnScreenOn();
    """)


def unlock_screen(marionette):
    marionette.execute_script("""
        var lockScreen = window.wrappedJSObject.LockScreen;
        lockScreen.unlock();
    """)
