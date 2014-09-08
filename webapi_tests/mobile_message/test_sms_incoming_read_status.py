# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncomingReadStatus(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Verify that an SMS can be received (sent by the test user)
    - Confirm that the associated mozMobileMessage received event is triggered
    - Mark the received message status as unread using API and verify read attribute
    - Mark the received message status as read using API and verify read attribute

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestSmsIncomingReadStatus, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestSmsIncomingReadStatus, self).tearDown()

    def test_sms_incoming_read_status(self):
        # have user send sms to the Firefox OS device
        self.msg_type = "SMS"
        self.user_guided_incoming_msg()

        # verify message contents
        self.assertTrue(len(self.in_msg['body']) > 0,
                        "Received message has no message body (was text included in the sent message?)")
        self.confirm('Received SMS with text "%s" does this text match what was sent to the Firefox OS phone?' % self.in_msg['body'])

        self.assertEqual(self.in_msg['type'], 'sms',
                         "Received SMS MozSmsMessage.type should be 'sms'")
        self.assertGreater(self.in_msg['id'], 0,
                           "Received SMS MozSmsMessage.id should be > 0")
        self.assertEqual(self.in_msg['delivery'], 'received',
                         "Received SMS MozSmsMessage.delivery should be 'received'")

        # mark received message status as unread and verify
        self.mark_message_status(self.in_msg['id'], is_read=False)
        sms = self.get_message(self.in_msg['id'])
        self.assertTrue(sms['read'] is False,
                        "Received SMS MozSmsMessage.read field should be False")

        # mark received message status as read and verify
        self.mark_message_status(self.in_msg['id'], is_read=True)
        sms = self.get_message(self.in_msg['id'])
        self.assertTrue(sms['read'] is True,
                        "Received SMS MozSmsMessage.read field should be True")
