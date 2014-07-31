# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from marionette.wait import Wait
from webapi_tests.semiauto import TestCase
from webapi_tests.idle import IdleActiveTestCommon


class TestIdleActive(TestCase, IdleActiveTestCommon):

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestIdleActive, self).setUp()
        self.wait_for_obj("window.navigator.mozPower")
        self.marionette.execute_script("window.wrappedJSObject.rcvd_idle = false;")
        self.marionette.execute_script("window.wrappedJSObject.rcvd_active = false;")
        #get screen current brightness
        brightness = self.get_screen_brightness()
        self.marionette.execute_script("window.wrappedJSObject.brightness = arguments[0];", script_args=[brightness])
        self.assertNotEqual(brightness, -1, "Unable to get screen current brightness")
        #start test with bright screen
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")

    def test_idle_state(self):
        self.instruct("About to test idle state. Please click OK and then watch the screen, but do not touch the screen")

        self.marionette.execute_script("""
        window.wrappedJSObject.testIdleObserver = {
            time : 5,
            onidle : function() {
                window.navigator.mozPower.screenBrightness = 0.1;
                window.wrappedJSObject.rcvd_idle = true;
            }
        };
        navigator.addIdleObserver(window.wrappedJSObject.testIdleObserver);
        """)

        #wait for device to go idle
        wait = Wait(self.marionette, timeout=15, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_idle;"))
        except:
            self.fail("Failed to attain idle state")

        self.confirm("Did you notice decrease in brightness?")

    @unittest.skip("Bug 1033248 - Device does not enter from idle state to active state")
    def test_active_state(self):
        self.instruct("About to test active state. Please click OK and then watch the screen")

        self.marionette.execute_script("""
        window.wrappedJSObject.testActiveObserver = {
            time : 5,
            onidle : function() {
                window.navigator.mozPower.screenBrightness = 0.1;
                window.wrappedJSObject.rcvd_idle = true;
            },
            onactive : function() {
                window.navigator.mozPower.screenBrightness = 0.5;
                window.wrappedJSObject.rcvd_active = true;
            }
        };
        navigator.addIdleObserver(window.wrappedJSObject.testActiveObserver);
        """)

        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_idle;"))
        except:
            self.fail("Failed to attain idle state")

        self.confirm("Did you notice decrease in brightness?")
        self.instruct("Touch on the screen to wake up the device")

        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_active;"))
        except:
            self.fail("Failed to attain active state")

        self.confirm("Did you notice increase in brightness?")

    def clean_up(self):
        if self.marionette.execute_script("return window.wrappedJSObject.testIdleObserver;") is not None:
            self.marionette.execute_script("navigator.removeIdleObserver(window.wrappedJSObject.testIdleObserver);")
        if self.marionette.execute_script("return window.wrappedJSObject.testActiveObserver;") is not None:
            self.marionette.execute_script("navigator.removeIdleObserver(window.wrappedJSObject.testActiveObserver);")
        #restore brightness
        if self.marionette.execute_script("return window.wrappedJSObject.brightness;") != -1:
            self.marionette.execute_script("window.navigator.mozPower.screenBrightness = window.wrappedJSObject.brightness;")
            self.marionette.execute_script("window.wrappedJSObject.brightness = -1;")
