# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class AppsTestCommon(object):
    def get_selfapp(self):
        self.marionette.execute_async_script("""
        var request = window.navigator.mozApps.getSelf();

        request.onsuccess = function() {
            if(request.result) {
                window.wrappedJSObject.rcvd_app_name = request.result.manifest.name;
                console.log("Application Name : " + window.wrappedJSObject.rcvd_app_name);
            } else {
                console.log("Failed to get the self app manifest info. Called from outside.");
            }
        };

        request.onerror = function() {
            console.log("Failed to get self app manifest: " + request.error.name);
            window.wrappedJSObject.error_msg = request.error.name;
        };
        marionetteScriptFinished(1);
        """)
        if self.marionette.execute_script("return window.wrappedJSObject.rcvd_app_name"):
            return self.marionette.execute_script("return window.wrappedJSObject.rcvd_app_name")
        else:
            if self.marionette.execute_script("return window.wrappedJSObject.error_msg"):
                self.fail("window.navigator.mozApps.getSelf returned error: " + self.marionette.execute_script("return window.wrappedJSObject.error_msg"))
            else:
                self.fail("Failed to get the self app manifest info. Called from outside.")
