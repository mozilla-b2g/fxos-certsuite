# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import threading
import unittest

import mozdevice
from marionette import Marionette
from marionette.wait import Wait
from marionette import errors

from mcts.webapi_tests import certapp
from mcts.webapi_tests.semiauto import environment
from mcts.webapi_tests.semiauto.environment import InProcessTestEnvironment


"""The default time to wait for a user to respond to a prompt or
instruction in a test."""
prompt_timeout = 600  # 10 minutes

# local variable for marionette
_host = 'localhos'
_port = 2828

class TestCase(unittest.TestCase):
    stored = threading.local()

    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version')
        super(TestCase, self).__init__(*args, **kwargs)
        self.stored.handler = None
        self.stored.marionette = None

        self.marionette, self.server, self.handler, self.app = None, None, None, None

        device = mozdevice.DeviceManagerADB()
        device.forward("tcp:2828", "tcp:2828")

        # Cleanups are run irrespective of whether setUp fails
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.marionette is not None:
            certapp.kill(self.marionette, app=self.app)

    def check_skip(self, skiplist):
        self.test_name = str(self.__class__).split('.')[1]
        if self.test_name in skiplist:
            self.skipTest('Skipped by device profile')

    def showTestStatusInDevice(self, marionette):
        marionette.execute_async_script("""
            document.getElementsByTagName('body')[0].innerHTML =
                '<center><h1>WebAPI<h1><h2>%s</h2><h3>%s</h3><br>running</center>';
            marionetteScriptFinished();
            """ % (self.test_name, self._testMethodName))

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

        env = environment.get(InProcessTestEnvironment)

        if env.device_profile:
            self.check_skip(env.device_profile['webapi'])

        self.server = env.server
        self.handler = env.handler

        self.assert_browser_connected()
        self.marionette = TestCase.create_marionette()

        if not certapp.is_installed():
            certapp.install(marionette=self.marionette, version=self.version)

        # Make sure we don't reuse the certapp context from a previous
        # testrun that was interrupted and left the certapp open.
        try:
            certapp.kill(self.marionette)
        except certapp.CloseError:
            self.close_app_manually()

        try:
            self.app = certapp.launch(self.marionette)
            self.showTestStatusInDevice(self.marionette)
        except certapp.LaunchError:
            self.launch_app_manually()

    def assert_browser_connected(self):
        """Asserts (and consequently fails the test if not true) that the
        browser is connected to the semiauto test harness.

        """

        self.assertTrue(self.handler.connected, "Browser disconnected")

    @staticmethod
    def create_marionette():
        """Returns current Marionette session, or creates one if
        one does not exist.

        """

        m = TestCase.stored.marionette
        if m is None:
            m = Marionette(host=_host, port=_port)
            m.wait_for_port()
            m.start_session()
            TestCase.stored.marionette = m

        return TestCase.stored.marionette

    def prompt(self, question, image_path=""):
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

        resp = self.handler.prompt(question, image_path)
        if type(resp) == bool and not resp:
            self.fail("Failed on prompt cancel: %s" % question)
        return resp

    def confirm(self, message, image_path=""):
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

        success = self.handler.confirmation(message, image_path)
        if not success:
            self.fail("Failed on confirmation: %s" % message)

    def instruct(self, message, image_path=""):
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

        success = self.handler.instruction(message, image_path)
        if not success:
            self.fail("Failed on instruction: %s" % message)

    def close_app_manually(self):
        success = self.instruct("Could not close %s automatically. "
            "Please close the app manually by holding down the Home button "
            "and pressing the X above the %s card." % (certapp.name, certapp.name))
        if not success:
            device = mozdevice.DeviceManagerADB()
            device.reboot(wait=True)
            self.instruct("Please unlock the lockscreen (if present) after device reboots")
            self.fail("Failed attempts at closing certapp")

    def launch_app_manually(self):
        self.instruct("Could not launch %s automatically. Please launch by hand." % certapp.name)
        certapp.activate(self.marionette)

    def wait_for_obj(self, object):
        wait = Wait(self.marionette, timeout=5, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return !!%s;" % object))
        except errors.TimeoutException:
            self.fail("Object '%s' does not exist" % object)


def wait_for_homescreen(marionette):
    marionette.set_context(marionette.CONTEXT_CONTENT)
    marionette.execute_async_script("""
        let manager = window.wrappedJSObject.AppWindowManager || window.wrappedJSObject.WindowManager;
        log(manager);
        let app = null;
        if (manager) {
            app = manager.getActiveApp();
        }
        log(app);
        if (app) {
            log('Already loaded home screen');
            marionetteScriptFinished();
        } else {
            log('waiting for mozbrowserloadend');
            window.addEventListener('mozbrowserloadend', function loaded(aEvent) {
                log('received mozbrowserloadend for ' + aEvent.target.src);
                if (aEvent.target.src.indexOf('ftu') != -1 || aEvent.target.src.indexOf('homescreen') != -1) {
                    window.removeEventListener('mozbrowserloadend', loaded);
                    marionetteScriptFinished();
                }
            });
        }""", script_timeout=30000)
