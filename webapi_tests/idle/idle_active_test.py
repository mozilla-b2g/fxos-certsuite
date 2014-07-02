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

    def is_idle_state(self):
        self.marionette.execute_script("""
        window.wrappedJSObject.rcvd_idle = false;
        window.wrappedJSObject.testIdleObserver = {
            time : 5,
            onidle : function() {
                window.navigator.mozPower.screenBrightness = 0.1;
                window.wrappedJSObject.rcvd_idle = true;
            }
        };
        navigator.addIdleObserver(window.wrappedJSObject.testIdleObserver);
        """)

    def is_active_state(self):
        self.marionette.execute_script("""
        window.wrappedJSObject.rcvd_active = false;
        window.wrappedJSObject.rcvd_idle = false;
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
