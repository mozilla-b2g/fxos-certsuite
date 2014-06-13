# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class NotificationTestCommon(object):
    def get_permission_setting(self):
        return self.marionette.execute_script("return Notification.permission")

    def request_permission(self):
        return self.marionette.execute_async_script("""
        console.log("Notification permission is: " + Notification.permission);
        console.log("Requesting user permission for notifications");
        Notification.requestPermission(function (perm) { marionetteScriptFinished(perm); })
    """)

    def create_notification(self, text):
        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_onshow = false;
        var text = arguments[0];

        console.log("Creating new notification");
        var notification = new Notification(text);

        // setup callback
        notification.onshow = function() {
            console.log("Received Notification.onshow event");
            window.wrappedJSObject.rcvd_onshow = true;
        }

        marionetteScriptFinished(1);
    """, script_args=[text])

        # wait for notification to be displayed
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_onshow"))
        except:
            self.fail("Did not receive the Notification.onshow event")
