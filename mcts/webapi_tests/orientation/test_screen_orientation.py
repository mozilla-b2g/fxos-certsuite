# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase


class TestScreenOrientation(TestCase):
    """
    This is a test for the `Screen Orientation API`_ which will:

    - Ask the test user to move the device into various positions
    - Verify that the corresponding mozOrientation values are correct
    - Lock the screen orientation in portrait, ask the test user to verify
    - Lock the screen orientation in landscape, ask the test user to verify

    .. _`Screen Orientation API`: https://developer.mozilla.org/en-US/docs/Web/API/CSS_Object_Model/Managing_screen_orientation
    """

    def setUp(self):
        super(TestScreenOrientation, self).setUp()
        self.wait_for_obj("window.wrappedJSObject.screen")
        # New Screen Orientation API: https://w3c.github.io/screen-orientation/
        # Old Screen Orientation API: https://wiki.mozilla.org/index.php?title=WebAPI/ScreenOrientation&direction=next&oldid=418898
        self.is_support_new_api = self.marionette.execute_script("if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {return true;} else {return false;}")
        if not self.is_support_new_api:
            self.wait_for_obj("window.wrappedJSObject.screen.mozOrientation")

    def check_orientation(self, mode):
        orientation = self.marionette.execute_script("""
        if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {
            return window.wrappedJSObject.screen.orientation.type;
        } else {
            return window.wrappedJSObject.screen.mozOrientation;
        }
        """)
        self.assertTrue(mode in orientation, "the " + ("screen.orientation.type" if self.is_support_new_api else "screen.mozOrientation") + " value is incorrect/not what was expected")

    def test_orientation_change(self):
        self.instruct("Ensure the phone is unlocked and in portrait mode " + ("(new API)" if self.is_support_new_api else "(Old API)"))
        self.check_orientation("portrait")
        self.instruct("Now rotate the phone into landscape position and wait for the screen to adjust to landscape mode \
                      (watch the notifications ribbon at the top).")
        self.check_orientation("landscape")

    def test_orientation_lock(self):
        self.instruct("Ensure the phone is unlocked and in portrait mode " + ("(new API)" if self.is_support_new_api else "(Old API)"))
        self.check_orientation("portrait")
        self.marionette.execute_script("""
        if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {
            return window.wrappedJSObject.screen.orientation.lock('portrait');
        } else {
            return window.wrappedJSObject.screen.mozLockOrientation('portrait');
        }
        """)
        self.instruct("Now rotate the phone into landscape position. The screen should NOT adjust to the new orientation.")
        self.check_orientation("portrait")
        self.marionette.execute_script("""
        if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {
            return window.wrappedJSObject.screen.orientation.unlock();
        } else {
            return window.wrappedJSObject.screen.mozUnlockOrientation();
        }
        """)
        self.instruct("Now rotate the phone into portrait position, then back to landscape position. " \
                      "The screen should adjust to the new orientation. You may need to wait a few seconds.")
        self.check_orientation("landscape")
        self.marionette.execute_script("""
        if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {
            return window.wrappedJSObject.screen.orientation.lock('landscape');
        } else {
            return window.wrappedJSObject.screen.mozLockOrientation('landscape');
        }
        """)
        self.instruct("Now rotate the phone into portrait mode. The screen should NOT adjust to the new orientation.")
        self.check_orientation("landscape")
        self.marionette.execute_script("""
        if ('orientation' in window.wrappedJSObject.screen && 'angle' in window.wrappedJSObject.screen.orientation) {
            return window.wrappedJSObject.screen.orientation.unlock();
        } else {
            return window.wrappedJSObject.screen.mozUnlockOrientation();
        }
        """)
        self.instruct("Now rotate the phone into landscape position, then back to portrait position. " \
                      "The screen should adjust to the new orientation. You may need to wait a few seconds.")
        self.check_orientation("portrait")
