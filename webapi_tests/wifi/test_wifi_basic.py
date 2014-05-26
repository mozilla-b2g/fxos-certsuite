# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase


class TestWifi(TestCase):
    def tearDown(self):
        self.marionette.execute_script("""
        window.navigator.mozWifiManager = null;
        """)
        TestCase.tearDown(self)

    def test_wifi_basic(self):
        self.instruct("Switch on Wifi and note down the " \
                        "number of wifi-networks avaiable.")
        nwkslist_count = None
        nwkslist_count = self.prompt("Please enter number of " \
                                     "available wifi-netwokrs")
        if nwkslist_count is None:
            self.fail("Must enter the number of wifi-networks")
        find_networks = """
            var nwkslist_count = arguments[0];
            var wifi = navigator.mozWifiManager;
            var data = false;
            var request = wifi.getNetworks();
            request.onsuccess = function() {
                var networks = this.result;
                data = (networks.length == nwkslist_count) ? true : false;
                marionetteScriptFinished(data);
            };
            request.onerror = function(event) {
                marionetteScriptFinished(data);
            };
        """
        foundnwks_status = self.marionette.execute_async_script(find_networks,
                                  script_args=[nwkslist_count])
        self.assertTrue(foundnwks_status, "Mismatch of entered " \
                                     "and available wifi networks")
