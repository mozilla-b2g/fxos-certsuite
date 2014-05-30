# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase


class TestWifi(TestCase):
    def tearDown(self):
        self.marionette.execute_script("window.navigator.mozWifiManager = null;")
        TestCase.tearDown(self)

    def test_wifi_basic(self):
        self.instruct("This test requires a local WiFi network to be"
                 " available and visible. Please ensure a local WiFi network"
                 " is visible before continuing")
        foundnwks_status = None
        find_networks = """
            var wifi = navigator.mozWifiManager;
            var request = wifi.getNetworks();
            request.onsuccess = function() {
                var network = this.result[0];
                var networkinfo;
                if(network.security.length > 0) {
                    networkinfo = "ssid: " + network.ssid + " security: " + network.security;
                } else {
                    networkinfo = "ssid: " + network.ssid + " security: None";
                }
                marionetteScriptFinished(networkinfo);
            };
            request.onerror = function(event) {
                marionetteScriptFinished();
            };
        """
        foundnwks_status = self.marionette.execute_async_script(find_networks)
        if foundnwks_status is None:
            self.fail("No Wifi networks found")
        self.confirm('Found a Wifi network with following info: "%s"' %foundnwks_status)

