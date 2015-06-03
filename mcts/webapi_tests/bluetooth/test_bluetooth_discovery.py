# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.bluetooth import BluetoothTestCommon


class TestBluetoothDiscovery(TestCase, BluetoothTestCommon):
    """
    This tests device discovery using the `WebBluetooth API`_ including:

    - Enabling and disabling bluetooth
    - Getting the default bluetooth adapter
    - Setting the bluetooth device name
    - Entering discoverable mode
    - Discovery of other bluetooth devices

    .. _`WebBluetooth API`: https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestBluetoothDiscovery, self).setUp()
        self.wait_for_obj("window.navigator.mozBluetooth")
        # start with bt disabled
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
        self.have_adapter = False

    def test_enabled(self):
        # enable bt via settings
        self.set_bt_enabled(True)
        self.assertTrue(self.is_bt_enabled(), "Bluetooth should be enabled")
        time.sleep(10)
        # disable bt via settings
        self.set_bt_enabled(False)
        self.assertFalse(self.is_bt_enabled(), "Bluetooth should NOT be enabled")

    def test_get_default_adapter(self):
        # enable bt via settings, get adapter
        self.set_bt_enabled(True)
        adapter = self.get_default_bt_adapter()
        self.assertIsNotNone(adapter["class"], "BluetoothAdapter.class must have a value")
        self.assertEqual(len(adapter["address"]), 17, "BluetoothAdapter.address should be 17 chars in length")
        self.assertFalse(adapter["discoverable"], "BluetoothAdapter.discoverable should be false by default")
        self.assertNotEqual(adapter["discoverableTimeout"], 0, "BluetoothAdapter.discoverableTimeout cannot be 0")
        self.assertFalse(adapter["discovering"], "BluetoothAdapter.discovering should be false by default")
        self.assertEqual(len(adapter["devices"]), 0, "BluetoothAdapter.devices should be empty by default")
        self.assertIsNotNone(adapter["name"], "BluetoothAdapter.name must exist")
        self.assertIsNotNone(adapter["uuids"], "BluetoothAdapter.uuids must exist")

    def test_discoverable(self):
        # enable bt via settings, get adapter
        self.set_bt_enabled(True)
        adapter = self.get_default_bt_adapter()
        # ensure discoverable mode is off to start
        if self.get_bt_discoverable_mode():
            self.set_bt_discoverable_mode(False)
        old_name = adapter["name"]
        # have tester input Firefox OS bt adapter name, so it can easily be found
        name = self.prompt('Current Firefox OS bluetooth adaptor name is "%s". \
                            Please enter a new name (1 to 20 characters in length).' % old_name)
        self.assertTrue(len(name) > 0 and len(name) < 21, "BluetoothAdapter.name must be between 1 and 20 characters long")
        self.set_bt_adapter_name(name)
        self.set_bt_discoverable_timeout(180)
        # become discoverable
        self.set_bt_discoverable_mode(True)
        self.confirm('The Firefox OS device is now in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. Do you see the Firefox OS device (named "%s") listed?' % name)
        # turn off discoverable mode
        self.set_bt_discoverable_mode(False)
        self.confirm('The Firefox OS device is NOT in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. IS IT TRUE that the Firefox OS device ("%s") DOES NOT appear anymore?' % name)
        self.set_bt_adapter_name(old_name)

    def test_discovering(self):
        # enable bt via settings, get adapter
        self.set_bt_enabled(True)
        adapter = self.get_default_bt_adapter()
        # ensure are not discovering already
        if self.get_bt_discovering():
            self.stop_bt_discovering()
        self.instruct("On a different phone (NOT the Firefox OS device), please enable bluetooth "\
                      "and turn ON discoverable mode, then click OK.")
        # enter discovery mode for awhile
        self.start_bt_discovery()
        time.sleep(30)
        # ensure are not discovering
        if self.get_bt_discovering():
            self.stop_bt_discovering()
        # verify at least one device was found
        self.assertTrue(self.get_num_bt_devices_found() > 0, "Failed to discover any bluetooth devices. Ensure at least one " \
                        "other non-Firefox OS device is in discoverable mode and please try again.")

    def clean_up(self):
        # disable bt
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
