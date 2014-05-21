# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from bluetooth import BluetoothTestCommon


class TestBluetoothDiscovery(TestCase, BluetoothTestCommon):
    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestBluetoothDiscovery, self).setUp()
        # start with bt disabled
        if self.is_bt_enabled():
            self.set_bt_enabled(False)

    def test_enabled(self):
        # start with bt disabled
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
        # enable bt via settings
        self.set_bt_enabled(True)
        self.assertTrue(self.is_bt_enabled(), "Bluetooth should be enabled")
        time.sleep(10)
        # disable bt via settings
        self.set_bt_enabled(False)
        self.assertFalse(self.is_bt_enabled(), "Bluetooth should NOT be enabled")

    def test_get_default_adapter(self):
        # ensure enabled
        if not self.is_bt_enabled():
            self.set_bt_enabled(True)
        # get default adapter
        adapter = self.get_default_bt_adapter()
        self.assertNotEqual(adapter["class"], None, "BluetoothAdapter.class must have a value")
        self.assertEqual(len(adapter["address"]), 17, "BluetoothAdapter.address should be 17 chars in length")
        self.assertFalse(adapter["discoverable"], "BluetoothAdapter.discoverable should be false by default")
        self.assertNotEqual(adapter["discoverableTimeout"], 0, "BluetoothAdapter.discoverableTimeout cannot be 0")
        self.assertFalse(adapter["discovering"], "BluetoothAdapter.discovering should be false by default")
        self.assertEqual(len(adapter["devices"]), 0, "BluetoothAdapter.devices should be empty by default")
        self.assertNotEqual(adapter["name"], None, "BluetoothAdapter.name must exist")
        self.assertNotEqual(adapter["uuids"], None, "BluetoothAdapter.uuids must exist")

    def test_discoverable(self):
        # ensure enabled
        if not self.is_bt_enabled():
            self.set_bt_enabled(True)
            time.sleep(5)
        # get default adapter
        adapter = self.get_default_bt_adapter()
        # ensure discoverable mode is off to start
        if(self.get_bt_discoverable_mode == True):
            self.set_bt_discoverable_mode(False)
            time.sleep(5)
#        # get default bluetooth adapter name
#        name = adapter["name"]
#        self.assertTrue(len(name) > 0, "BluetoothAdapter.name must not be empty")
#        # set discoverable timeout
#        self.set_bt_discoverable_timeout(180)
#        # become discoverable
#        self.set_bt_discoverable_mode(True)
#        time.sleep(5)
#        # have user verify device by the same name is found on other phone
#        self.confirm('The Firefox OS device is now in Bluetooth discoverable mode. From a different phone, please \
#                     discover Bluetooth devices. Do you see the Firefox OS device ("%s") listed?' %name)
#        # now turn off discoverable mode
#        self.set_bt_discoverable_mode(False)
#        time.sleep(5)
#        # have user verify by checking a different device
#        self.confirm('The Firefox OS device is NOT in Bluetooth discoverable mode. From a different phone, please \
#                     discover Bluetooth devices. IS IT TRUE that the Firefox OS device ("%s") DOES NOT appear anymore?' %name)

    def test_discovering(self):
        # ensure enabled
        if not self.is_bt_enabled():
            self.set_bt_enabled(True)
        # get default adapter
        adapter = self.get_default_bt_adapter()
        # have user ensure other phone bt is on and in discoverable mode
        # start discovery
        # stop discovery
        # show user list of found devices, verify theirs is there
        self.assertTrue(True)

    def test_name(self):
        pass

    def clean_up(self):
        # disable bluetooth on exit
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
