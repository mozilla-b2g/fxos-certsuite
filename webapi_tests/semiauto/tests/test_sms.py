# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from tests import TestCase, test


class TestSms(TestCase):
    @test
    def test_life(self):
        answer = self.prompt("What's the meaning of life?")
        self.assertEqual(answer, "42")

    # @test
    # def test_swipe(self):
    #     def swipe_detected(marionette):
    #         # TODO(ato): Implement
    #         import time
    #         time.sleep(2)
    #         return True

    #     yield self.instruct("Swipe on the screen")
    #     detected_swipe = Wait(self.marionette).until(swipe_detected)
    #     self.assertTrue(detected_swipe)
