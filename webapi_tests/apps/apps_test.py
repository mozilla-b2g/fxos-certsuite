# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class AppsTestCommon(object):
    def get_self(self):
        self.marionette.execute_async_script("""
        var request = window.navigator.mozApps.getSelf();
        window.wrappedJSObject.app = null;
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.error_msg = null;

        request.onsuccess = function() {
            if(request.result) {
                window.wrappedJSObject.app = request.result;
                window.wrappedJSObject.rcvd_success = true;
            }
        };

        request.onerror = function() {
            window.wrappedJSObject.rcvd_error = true;
            window.wrappedJSObject.error_msg = request.error.name;
        };
        marionetteScriptFinished(1);
        """)
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("mozApps.getSelf returned error: " + self.marionette.execute_script("return window.wrappedJSObject.error_msg"))
            else:
                self.fail("mozApps.getSelf failed. Called from outside.")
        app = self.marionette.execute_script("return window.wrappedJSObject.app")
        self.assertIsNotNone(app, "mozApps.getSelf returned none")
        return app
