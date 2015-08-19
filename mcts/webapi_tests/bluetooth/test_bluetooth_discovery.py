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
        self.have_adapter = False

    def test_get_default_adapter(self):
        self.get_default_bt_adapter()
        self.assertIsNotNone(self.get_adapter_state, "BluetoothAdapter.state must exist")

    def test_enabled(self):
        self.get_default_bt_adapter()
        self.set_bt_enabled(True)
        time.sleep(5)

        self.assertIsNotNone(self.get_adapter_state, "BluetoothAdapter.state must exist")
        self.assertEqual(len(self.get_adapter_address), 17, "BluetoothAdapter.address should be 17 chars in length")
        self.assertFalse(self.get_adapter_discoverable, "BluetoothAdapter.discoverable should be false by default")
        # Discovering can be True in the first few seconds and then switch back to False
        self.assertIsNotNone(self.get_adapter_discovering, "BluetoothAdapter.discovering should have a value by default")
        self.assertIsNotNone(self.get_adapter_name, "BluetoothAdapter.name must exist")
        self.assertTrue(self.is_bt_enabled, "Bluetooth should be enabled")

        self.set_bt_enabled(False)
        time.sleep(5)

        self.assertFalse(self.is_bt_enabled, "Bluetooth should NOT be enabled")


    def test_discoverable(self):
        # enable bt via adapter
        self.get_default_bt_adapter()
        self.set_bt_enabled(True)

        # ensure discoverable mode is off to start
        if self.get_adapter_discoverable:
            self.set_bt_discoverable_mode(False)
        name = self.get_adapter_name

        # become discoverable
        self.set_bt_discoverable_mode(True)
        self.confirm('The Firefox OS device is now in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. Do you see the Firefox OS device (named "%s") listed?' % name)

        # turn off discoverable mode
        self.set_bt_discoverable_mode(False)
        self.confirm('The Firefox OS device is NOT in Bluetooth discoverable mode. From a different phone, please '\
                     'discover Bluetooth devices. IS IT TRUE that the Firefox OS device ("%s") DOES NOT appear anymore?' % name)

    def test_discovering(self):
        # enable bt via adapter
        self.get_default_bt_adapter()
        self.set_bt_enabled(True)

        # ensure are not discovering already
        if self.get_adapter_discovering:
            self.bt_discovery(False)
        self.instruct("On a different phone (NOT the Firefox OS device), please enable bluetooth "\
                      "and turn ON discoverable mode, then click OK.")

        # enter discovery mode for awhile
        self.bt_discovery(True)
        time.sleep(30)

        # ensure are not discovering
        if self.get_adapter_discovering:
            self.bt_discovery(False)

        # verify at least one device was found
        self.assertTrue(self.get_num_bt_devices_found() > 0, "Failed to discover any bluetooth devices. Ensure at least one " \
                        "other non-Firefox OS device is in discoverable mode and please try again.")

    def clean_up(self):
        # disable bt
        if self.is_bt_enabled:
            self.set_bt_enabled(False)
