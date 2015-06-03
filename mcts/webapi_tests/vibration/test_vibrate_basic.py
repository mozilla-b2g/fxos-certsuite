# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from mcts.webapi_tests.semiauto import TestCase


class TestVibrateBasic(TestCase):
    """
    This is a test for the `Vibration API`_ which will:

    - Initiate a single 200ms vibration, and ask the test user to verify
    - Initiate a second single 200ms vibration, and ask the test user to verify
    - Initiate a vibration pattern and ask the test user to verify

    .. _`Vibration API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Vibration
    """

    def setUp(self):
        super(TestVibrateBasic, self).setUp()
        self.wait_for_obj("window.navigator.vibrate")

    def test_vibrate_basic(self):
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate(200);")
        self.confirm("Did you feel a single vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200]);")
        self.confirm("Did you feel a single vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200, 1000, 200]);")
        time.sleep(1)
        self.confirm("Did you feel two vibrations, with about 1 second between each pulse?")
