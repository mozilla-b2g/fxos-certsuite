# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase


class TestIdleActive(TestCase):

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestIdleActive, self).setUp()
        #start with bright screen
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")
        self.marionette.execute_script("window.wrappedJSObject.testObserver = null;")

    def test_idle_active(self):
        self.instruct("About to test the idle functionality; phone screen would "
                      "gets dim after 5 sec.Touch the screen to make it active")

        self.marionette.execute_async_script("""
        window.wrappedJSObject.testObserver = {
            time : 5,
            onactive : function() {
                window.navigator.mozPower.screenBrightness = 1.0;
                marionetteScriptFinished(1);
            },
            onidle : function() {
                window.navigator.mozPower.screenBrightness = 0.1;
                marionetteScriptFinished(1);
            }
        };
        navigator.addIdleObserver(window.wrappedJSObject.testObserver);
        """)
        #wait for some time for user to verify active/idle functions
        time.sleep(15)
        #remove observer
        self.marionette.execute_script("navigator.removeIdleObserver(window.wrappedJSObject.testObserver);")

    def clean_up(self):
        #restore brightness
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")
        self.marionette.execute_script("window.wrappedJSObject.testObserver = null;")
