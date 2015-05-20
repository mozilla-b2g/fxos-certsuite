# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class GeolocationTestCommon(object):
    permission = False

    def is_geolocation_enabled(self):
        self.marionette.execute_async_script("""
        window.wrappedJSObject.geo_enabled = null;
        window.wrappedJSObject.get_success = false;
        var lock = navigator.mozSettings.createLock();
        var setting = lock.get('geolocation.enabled');
        setting.onsuccess = function () {
          console.log('geolocation.enabled: ' + setting.result);
          window.wrappedJSObject.get_success = true;
          window.wrappedJSObject.geo_enabled = setting.result["geolocation.enabled"];
        }
        setting.onerror = function () {
          console.log('An error occured: ' + setting.error);
        }
        marionetteScriptFinished(1);
        """)
        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.get_success"))
        except:
            self.fail("Failed to get the geolocation.enabled setting")
        return self.marionette.execute_script("return window.wrappedJSObject.geo_enabled")

    def set_geolocation_enabled(self, enable):
        # turn on geolocation via the device settings
        self.marionette.execute_async_script("""
        var enable = arguments[0];
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        if (enable) {
            console.log("Enabling geolocation via settings");
        } else {
            console.log("Disabling geolocation via settings");
        }
        var lock = window.navigator.mozSettings.createLock();
        var result = lock.set({
            'geolocation.enabled': enable
        });
        result.onsuccess = function() {
            console.log("Success changing geolocation.enabled setting");
            window.wrappedJSObject.rcvd_success = true;
        };
        result.onerror = function(error) {
            console.log("Failed to change geolocation.enabled setting " + error);
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[enable])

        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error;"):
                self.fail("Error received while changing the geolocation enabled setting")
            else:
                self.fail("Failed to change the geolocation.enabled setting")

    def is_geolocation_available(self):
        return self.marionette.execute_script("return 'geolocation' in navigator")

    def get_current_position(self):
        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.position = null;
        var mozGeo = window.navigator.geolocation;
        function success(position) {
            console.log("geolocation.getCurrentPosition success");
            window.wrappedJSObject.position = position;
            window.wrappedJSObject.rcvd_success = true;
        }
        function error(error) {
            console.log("Error " + error.code + " when requesting location");
            window.wrappedJSObject.rcvd_error = true;
        }
        console.log("Getting current position");
        mozGeo.getCurrentPosition(success, error);
        marionetteScriptFinished(1);
        """)

        # ask user to accept and dismiss the default gaia app location share prompt
        self.instruct("On the Firefox OS device, if a location request dialog is displayed, please "
                      "click the 'Share' button. If there is no dialog on the device, just continue.")

        # wait for the position request to finish
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("geolocation.getCurrentPosition returned error")
            else:
                self.fail("Failed to get position; either geolocation is broken -or- WiFi is not connected")

        position = self.marionette.execute_script("return window.wrappedJSObject.position")
        self.assertIsNotNone(position, "mozBluetooth.getCurrentPosition returned none")
        return position
