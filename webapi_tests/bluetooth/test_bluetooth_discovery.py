# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from bluetooth import BluetoothTestCommon


class TestBluetoothDiscovery(TestCase, BluetoothTestCommon):
    def tearDown(self):
        # disable bluetooth on exit
        if self.is_bt_enabled():
            self.set_bt_enabled(False)

    def test_enabled(self):
        # start with bt disabled
        
        # seems to be a bug with the enabled property; first time always returns false
        # so get it once at the start; file a bug for this/look into further
        print self.is_bt_enabled()

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
        # get default adapter
        adapter = self.get_default_bt_adapter()
        # get default bluetooth adapter name
        name = adapter["name"]
        self.assertTrue(len(name) > 0, "BluetoothAdapter.name must not be empty")
        # set discoverable timeout
        self.set_bt_discoverable_timeout(120)
        # become discoverable

        # have user verify device by the same name is found on other phone
        self.confirm('The Firefox OS device is now in Bluetooth discoverable mode. From a different phone, please \
                      discover Bluetooth devices. Do you see the Firefox OS phone listed (with the name "%s")?' %name)

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
