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
        # enable bt via settings
        self.set_bt_enabled(True)
        self.assertTrue(self.is_bt_enabled(), "Bluetooth should be enabled")
        time.sleep(10)
        # disable bt via settings
        self.set_bt_enabled(False)
        self.assertFalse(self.is_bt_enabled(), "Bluetooth should NOT be enabled")

    def test_get_default_adapter(self):
        # enable bluetooth
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
        # enable bluetooth
        if not self.is_bt_enabled():
            self.set_bt_enabled(True)
        # get default adapter
        adapter = self.get_default_bt_adapter()
        # ensure discoverable mode is off to start
        if(self.get_bt_discoverable_mode == True):
            self.set_bt_discoverable_mode(False)
        # record default adapter name
        old_name = adapter["name"]
        # have tester input Firefox OS bt adapter name, so it can easily be found
        name = self.prompt('Current Firefox OS bluetooth adaptor name is "%s". \
                            Please enter a new name (1 to 20 characters in length).' %old_name)
        # name must be 20 chars max (that is the Firefox OS bt name limit)
        self.assertTrue(len(name) > 0 and len(name) < 21, "BluetoothAdapter.name must be between 1 and 20 characters long")
        # set name as specified, verify changed
        self.set_bt_adapter_name(name)
        # set discoverable timeout
        self.set_bt_discoverable_timeout(180)
        # become discoverable
        self.set_bt_discoverable_mode(True)
        # have user verify device by the same name is found on other phone
        self.confirm('The Firefox OS device is now in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. Do you see the Firefox OS device (named "%s") listed?' %name)
        # now turn off discoverable mode
        self.set_bt_discoverable_mode(False)
        # have user verify by checking a different device
        self.confirm('The Firefox OS device is NOT in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. IS IT TRUE that the Firefox OS device ("%s") DOES NOT appear anymore?' %name)
        # set bt adapter name back to original
        self.set_bt_adapter_name(old_name)

    def test_discovering(self):
        # enable bluetooth
        if not self.is_bt_enabled():
            self.set_bt_enabled(True)
        # get default adapter
        adapter = self.get_default_bt_adapter()
        # ensure are not discovering already
        if self.get_bt_discovering():
            self.stop_bt_discovering()
        # have user ensure other phone bt is on and in discoverable mode
        self.instruct("On a different phone (NOT the Firefox OS device), please enable bluetooth "\
                      "and turn ON discoverable mode, then click OK.")
        # start discovery
        self.start_bt_discovery()
        # wait a minute
        time.sleep(30)
        # stop discovery
        self.stop_bt_discovery()
        # verify at least one device was found
        self.assertTrue(self.get_num_bt_devices_found() > 0, "Failed to discover any bluetooth devices. Ensure at least one " \
                        "other non-Firefox OS device is in discoverable mode and please try again.")

    def clean_up(self):
        # disable bt
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
