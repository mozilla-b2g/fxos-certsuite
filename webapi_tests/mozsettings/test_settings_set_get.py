# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


from semiauto import TestCase
from mozsettings.settings_test import SettingsTestCommon


class TestVibrationSettings(TestCase, SettingsTestCommon):

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestVibrationSettings, self).setUp()
        # Disabling vibration during start of test
        if self.is_vibration_enabled():
            self.set_vibration_enabled(False)

    def test_get_vibration_settings(self):
        self.assertEqual(False, self.is_vibration_enabled(), "Vibration should be disabled")

    def test_set_vibration_settings(self):
        if self.set_vibration_enabled(True):
            self.assertEqual(True, self.is_vibration_enabled(), "Vibration should be enabled")
            self.instruct("Hold the phone; about to test vibration enable functionality")
            self.vibrate_once()
            self.confirm("Did you feel a single vibration?")
        else:
            self.fail("An error in enabling vibration")
        if self.set_vibration_enabled(False):
            self.assertEqual(False, self.is_vibration_enabled(), "Vibration should be disabled")
            self.instruct("Hold the phone; about to test vibration disable functionality")
            self.vibrate_once()
            self.confirm("Please confirm if vibration didn't happen")
        else:
            self.fail("An error in disabling vibration")

    def clean_up(self):
        if self.is_vibration_enabled():
            self.set_vibration_enabled(False)
