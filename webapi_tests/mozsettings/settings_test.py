# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class SettingsTestCommon(object):

    def vibrate_once(self):
        self.marionette.execute_script("window.navigator.vibrate([200]);")

    def is_vibration_enabled(self):
        result = self.marionette.execute_async_script("""
        var lock = navigator.mozSettings.createLock();
        var setting = lock.get('vibration.enabled');
        setting.onsuccess = function () {
            var vibration_status = setting.result["vibration.enabled"];
            marionetteScriptFinished(vibration_status);
        };
        setting.onerror = function () {
            console.log('An error occured: ' + setting.error);
            marionetteScriptFinished(0);
        };
        """)
        return result

    def set_vibration_enabled(self, enable):
        result = self.marionette.execute_async_script("""
        var enable = arguments[0];
        var lock = window.navigator.mozSettings.createLock();
        var result = (enable == true) ? lock.set({'vibration.enabled': true}):lock.set({'vibration.enabled': false});

        result.onsuccess = function() {
            console.log("Success in changing vibration.enabled setting");
            marionetteScriptFinished(1);
        };
        result.onerror = function(error) {
            console.log("Fail to change vibration.enabled setting " +
                        result.error);
            marionetteScriptFinished(0);
        };
        """, script_args=[enable])
        return result
