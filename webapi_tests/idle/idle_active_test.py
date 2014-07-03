# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class IdleActiveTestCommon(object):

    def get_screen_brightness(self):
        result = self.marionette.execute_async_script("""
        var lock = navigator.mozSettings.createLock();
        var setting = lock.get('screen.brightness');
        setting.onsuccess = function () {
            var brightness = setting.result["screen.brightness"];
            marionetteScriptFinished(brightness);
        };
        setting.onerror = function () {
            console.log('An error occured: ' + setting.error);
            //returns -1 as brightness can range from 0 to 1 for onsuccess
            marionetteScriptFinished(-1);
        };
        """)
        return result
