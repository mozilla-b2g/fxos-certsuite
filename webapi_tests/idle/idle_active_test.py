# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class IdleActiveTestCommon(object):

    def get_screen_brightness(self):
        result = self.marionette.execute_async_script("""
        var lock = navigator.mozSettings.createLock();
        var setting = lock.get('screen.brightness');
        setting.onsuccess = function () {
            window.wrappedJSObject.brightness = setting.result["screen.brightness"];
            marionetteScriptFinished(1);
        };
        setting.onerror = function () {
            console.log('An error occured: ' + setting.error);
            marionetteScriptFinished(0);
        };
        """)
        return result
