# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncoming(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Verify that an SMS can be received (sent by the test user)
    - Confirm that the associated mozMobileMessage received event is triggered
    - Verify the mozSmsMessage attributes

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestSmsIncoming, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestSmsIncoming, self).tearDown()

    def test_sms_incoming(self):
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
        self.assertGreater(self.in_msg['threadId'], 0,
                           "Received SMS MozSmsMessage.threadId should be > 0")
        self.assertEqual(self.in_msg['delivery'], 'received',
                         "Received SMS MozSmsMessage.delivery should be 'received'")
        # cannot guarantee end-user didn't read message; test that specifically in a different test
        self.assertTrue(self.in_msg['read'] is False or self.in_msg['read'] is True,
                        "Received SMS MozSmsMessage.read field should be False or True")
        # for privacy, don't print/check the actual sender's number; just ensure it is not empty
        self.assertGreater(len(self.in_msg['sender']), 0,
                           "Received SMS MozSmsMessage.sender field should not be empty")
        # timezones and different SMSC's, don't check timestamp value; just ensure non-zero
        self.assertGreater(self.in_msg['timestamp'], 0,
                           "Received SMS MozSmsMessage.timestamp should not be 0")
        self.assertTrue(self.in_msg['messageClass'] in ["class-0", "class-1", "class-2", "class-3", "normal"],
                        "Received SMS MozSmsMessage.messageClass must be a valid class")
