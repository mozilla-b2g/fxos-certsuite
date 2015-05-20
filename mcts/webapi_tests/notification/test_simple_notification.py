# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.notification import NotificationTestCommon


class TestSimpleNotification(TestCase, NotificationTestCommon):
    """
    This is a test for the `Web Notifications API`_ which will:

    - Check if the app has notification permission, if not ask the test user for permission
    - Create a new device notification
    - Ask the test user to verify that the notification appears correctly

    .. _`Web Notifications API`: https://developer.mozilla.org/en-US/docs/Web/API/Notification/Using_Web_Notifications
    """

    def setUp(self):
        super(TestSimpleNotification, self).setUp()
        self.wait_for_obj("Notification")
        result = self.request_permission()
        self.assertEqual(result, "granted", "User must grant permission on device for notifications")

    def test_simple_notification(self):
        text = "Hello from Firefox OS"
        self.instruct("About to create a new device notification. Please watch the Firefox device's "
                    "notifcation ribbon at the top of the screen.")
        self.create_notification(text)
        self.confirm("A new notification (with the text '%s') should appear on the Firefox OS device's "
                    "notification ribbon. Did the notification appear and contain the correct text?" % text)
