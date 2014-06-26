# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


from marionette.wait import Wait
from webapi_tests.semiauto import TestCase
from webapi_tests.idle import IdleActiveTestCommon


class TestIdleActive(TestCase, IdleActiveTestCommon):

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestIdleActive, self).setUp()
        self.assertTrue(self.get_screen_brightness(), "Unable to get screen current brightness")
        #start test with bright screen
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")

    def test_idle_active(self):
        self.instruct("About to test idle. Please click OK and then watch the screen, but do not touch the screen")
        self.marionette.execute_script("""
        window.wrappedJSObject.rcvd_active = false;
        window.wrappedJSObject.rcvd_idle = false;
        window.wrappedJSObject.testObserver = {
            time : 5,
            onactive : function() {
                window.navigator.mozPower.screenBrightness = 0.5;
                window.wrappedJSObject.rcvd_active = true;
            },
            onidle : function() {
                window.navigator.mozPower.screenBrightness = 0.1;
                window.wrappedJSObject.rcvd_idle = true;
            }
        };
        navigator.addIdleObserver(window.wrappedJSObject.testObserver);
        """)

        #wait for device to go idle
        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_idle;"))
        except:
            self.fail("Failed to attain idle state")

        #confirming decrease in brightness
        self.confirm("Did you notice decrease in brightness?")

        self.instruct("Touch the device to wake it up")

        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_active;"))
        except:
            self.fail("Failed to attain active state")

        self.confirm("Did you notice increase in brightness?")

    def clean_up(self):
        self.marionette.execute_script("navigator.removeIdleObserver(window.wrappedJSObject.testObserver);")
        #restore brightness
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = window.wrappedJSObject.brightness;")
