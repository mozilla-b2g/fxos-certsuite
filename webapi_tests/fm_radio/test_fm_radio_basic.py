# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from fm_radio import FMRadioTestCommon


class TestFMRadioBasic(TestCase, FMRadioTestCommon):
    def tearDown(self):
        # ensure fm radio is off and listeners removed
        if (self.is_radio_enabled()):
            self.change_radio_state(False)
        self.remove_antenna_change_listener()
        self.remove_radio_change_listeners()
        TestCase.tearDown(self)

    def test_insert_antenna(self):
        # ensure antenna is not attached at start
        self.ensure_antenna_connected(False)
        # user insert headset; verify via api
        self.ensure_antenna_connected(False)
        self.setup_antenna_change_listener()
        self.instruct("Insert the headset into the Firefox OS device, then click 'OK'")
        self.wait_for_antenna_change()
        self.assertTrue(self.is_antenna_available(), "Expected FMRadio.antennaAvailable to return true")
        self.remove_antenna_change_listener()

    def test_turn_radio_on(self):
        # ensure radio is off at start
        if (self.is_radio_enabled()):
            self.change_radio_state(False)
        self.ensure_antenna_connected()
        # turn radio on
        self.setup_radio_change_listeners()
        self.change_radio_state(True)
        self.assertTrue(self.got_radio_on())
        self.assertTrue(self.is_radio_enabled())
        self.remove_radio_change_listeners()
        self.confirm("The fm radio is ON. There may just be static. Turn up the device \
                    volume and listen in the headphones. Do you hear the radio audio?")
        # turn radio off
        self.change_radio_state(False)

    def test_turn_radio_off(self):
        self.ensure_antenna_connected()
        # ensure radio is on at start
        if (not self.is_radio_enabled()):
            self.change_radio_state(True)
        # turn radio off
        self.setup_radio_change_listeners()
        self.change_radio_state(False)
        self.assertTrue(self.got_radio_off())
        self.assertFalse(self.is_radio_enabled())
        self.remove_radio_change_listeners()
        self.confirm("The fm radio is OFF. Turn up the device volume and listen in the headphones. \
                    You should NOT hear any audio in the headphones. Is this the case/correct?")

    def test_remove_antenna(self):
        # ensure antenna is attached at start
        self.ensure_antenna_connected()
        # remove headset and verify
        self.setup_antenna_change_listener()        
        self.instruct("Remove the headset from the Firefox OS device, then click 'OK'")
        self.wait_for_antenna_change()
        self.assertFalse(self.is_antenna_available(), "Expected FMRadio.antennaAvailable to return false")
        self.remove_antenna_change_listener()
