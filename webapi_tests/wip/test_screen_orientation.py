# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests import MinimalTestCase


class TestOrientation(MinimalTestCase):
    def check_orientation(self, mode):
        orientation = self.marionette.execute_script("return window.wrappedJSObject.screen.mozOrientation;")
        self.assertTrue(mode in orientation)

    def test_orientation_change(self):
        self.instruct("Ensure the phone is unlocked and in portrait mode")
        self.check_orientation("portrait")
        self.instruct("Now rotate the phone into landscape position and wait for the screen to adjust to landscape mode.")
        self.check_orientation("landscape")

    def test_orientation_lock(self):
        self.instruct("Ensure the phone is unlocked and in portrait mode")
        self.check_orientation("portrait")
        self.marionette.execute_script("return window.wrappedJSObject.screen.mozLockOrientation('portrait');")
        self.instruct("Now rotate the phone into landscape position. The screen should NOT adjust to the new orientation.")
        self.check_orientation("portrait")
        self.marionette.execute_script("return window.wrappedJSObject.screen.mozUnlockOrientation();")
        self.instruct("Now rotate the phone into portrait position, then back to landscape position. " \
                      "The screen should adjust to the new orientation. You may need to wait a few seconds.")
        self.check_orientation("landscape")
        self.marionette.execute_script("return window.wrappedJSObject.screen.mozLockOrientation('landscape');")
        self.instruct("Now rotate the phone into portrait mode. The screen should NOT adjust to the new orientation.")
        self.check_orientation("landscape")
        self.marionette.execute_script("return window.wrappedJSObject.screen.mozUnlockOrientation();")
        self.instruct("Now rotate the phone into landscape position, then back to portrait position. " \
                      "The screen should adjust to the new orientation. You may need to wait a few seconds.")
        self.check_orientation("portrait")
