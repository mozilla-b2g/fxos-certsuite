# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.wifi import WifiTestCommon


class TestWifiBasic(TestCase, WifiTestCommon):
    """
    This is a test for the `WiFi Information API`_ which will:

    - Test enabling and disabling the device WiFi via settings
    - Use the mozWifiManager to get the available WiFi networks
    - Verify that at least one WiFi network was found, and it has SSID and BSSID values

    .. _`WiFi Information API`: https://developer.mozilla.org/en-US/docs/Web/API/WiFi_Information_API
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestWifiBasic, self).setUp()
        self.wait_for_obj("window.navigator.mozWifiManager")
        # start with wifi disabled
        if self.is_wifi_enabled():
            self.set_wifi_enabled(False)

    def test_basic_wifi_enabled(self):
        # enable wifi via settings
        self.set_wifi_enabled(True)
        self.assertTrue(self.is_wifi_enabled(), "Wifi should be enabled")
        time.sleep(10)
        # disable wifi via settings
        self.set_wifi_enabled(False)
        self.assertFalse(self.is_wifi_enabled(), "Wifi should NOT be enabled")

    def test_get_wifi_networks(self):
        # enable wifi via settings
        self.set_wifi_enabled(True)
        time.sleep(10)
        # get wifi networks
        wifi_networks = self.get_wifi_networks()
        self.assertTrue(len(wifi_networks) > 1, "Atleast one Wifi network should be available")
        # access first wifi network properties - ssid, bssid
        wifinetwork = wifi_networks[0]
        self.assertIsNotNone(wifinetwork["ssid"], "Wifi network must have a ssid value")
        self.assertEqual(len(wifinetwork["bssid"]), 17, "Wifi network bssid address should be 17 chars in length")

    def clean_up(self):
        # enable wifi
        if not self.is_wifi_enabled():
            self.set_wifi_enabled(True)
