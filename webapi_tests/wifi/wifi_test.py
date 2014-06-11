# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class WifiTestCommon(object):

    def is_wifi_enabled(self):
        return self.marionette.execute_script("return window.navigator.mozWifiManager.enabled;")

    def set_wifi_enabled(self, enable):
        self.marionette.execute_async_script("""
        var enable = arguments[0];
        window.wrappedJSObject.rcvd_enabled_event = false;
        window.wrappedJSObject.rcvd_disabled_event = false;
        window.wrappedJSObject.rcvd_error = false;
        var mozWifi = window.navigator.mozWifiManager;

        mozWifi.onenabled = function() {
           console.log("Received mozWifiManager.onenabled event");
           window.wrappedJSObject.rcvd_enabled_event = true;
        };

        mozWifi.ondisabled = function() {
           console.log("Received mozWifiManager.ondisabled event");
           window.wrappedJSObject.rcvd_disabled_event = true;
        };

        if (enable) {
            console.log("Turning on Wifi via settings");
        } else {
            console.log("Turning off Wifi via settings");
        }
        var lock = window.navigator.mozSettings.createLock();

        var result = lock.set({
            'wifi.enabled': enable
        });

        result.onerror = function() {
            if (enable) {
                console.log("Failed to changed Wifi setting to ON");
            } else {
                console.log("Failed to changed Wifi setting to OFF");
            }
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[enable])

        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            if enable:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_enabled_event;"))
            else:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_disabled_event;"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error;"):
                self.fail("Error received while changing the wifi enabled setting")
            else:
                if enable:
                    self.fail("Failed to enable wifi via mozSettings")
                else:
                    self.fail("Failed to disable wifi via mozSettings")

    def get_wifi_networks(self):
        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.wifi_networks = null;
        window.wrappedJSObject.error_msg = null;
        var mozWifi = window.navigator.mozWifiManager;

        console.log("Getting wifi networks");
        var request = mozWifi.getNetworks();

        request.onsuccess = function() {
            console.log("mozWifiManager.getNetworks request success");
            window.wrappedJSObject.rcvd_success = true;
            window.wrappedJSObject.wifi_networks = this.result;
        };

        request.onerror = function() {
            console.log("mozWifiManager.getNetworks request returned error: " + this.error.name);
            window.wrappedJSObject.rcvd_error = true;
            window.wrappedJSObject.error_msg = this.error.name;
        };
        marionetteScriptFinished(1);
        """)

        # wait for wifi networks to be found
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("mozWifiManager.getNetworks returned error: " + self.marionette.execute_script("return window.wrappedJSObject.error_msg"))
            else:
                self.fail("mozWifiManager.getNetworks failed")

        wifi_networks = self.marionette.execute_script("return window.wrappedJSObject.wifi_networks")
        self.assertIsNotNone(wifi_networks, "mozWifiManager.getNetowrk returned none")
        return wifi_networks
