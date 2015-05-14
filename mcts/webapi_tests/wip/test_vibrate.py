# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests import MinimalTestCase


class TestVibrate(MinimalTestCase):
    def test_vibrate_basic(self):
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate(200);")
        self.confirm("Did you feel a vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200]);")
        self.confirm("Did you feel a vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200, 1000, 200]);")
        self.confirm("Did you feel two vibrations, with about 1 second between each pulse?")
