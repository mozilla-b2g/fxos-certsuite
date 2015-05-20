# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsOutgoing(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Ask the test user to specify a destination phone number for the test SMS
    - Use the API to send an SMS message to a user-specified phone number
    - Verify that the associated mozMobileMessage events are triggered
    - Verify the mozSmsMessage attributes for the outgoing message

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestSmsOutgoing, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestSmsOutgoing, self).tearDown()

    def test_sms_outgoing(self):
        # send sms via the webapi and verify body
        self.msg_type = "SMS"
        self.user_guided_outgoing_msg()

        # verify other fields
        self.assertEqual(self.out_msg['type'], 'sms', "Sent SMS MozSmsMessage.type should be 'sms'")
        self.assertGreater(self.out_msg['id'], 0, "Sent SMS MozSmsMessage.id should be > 0")
        self.assertGreater(self.out_msg['threadId'], 0, "Sent SMS MozSmsMessage.threadId should be > 0")
        self.assertEqual(self.out_msg['delivery'], 'sent', "Sent SMS MozSmsMessage.delivery should be 'sent'")
        self.assertTrue((self.out_msg['deliveryStatus'] in ['success', 'not-applicable']),
                        "Sent SMS MozSmsMessage.deliveryStatus should be 'success' or 'not-applicable'")
        # cannot guarantee end-user didn't read message; test that specifically in a different test
        self.assertTrue(self.out_msg['read'] is False or self.out_msg['read'] is True,
                        "Sent SMS MozSmsMessage.read field should be False or True")
        # can check receiver number as the user provided it above
        self.assertTrue(self.out_destination in self.out_msg['receiver'],
                        "Sent SMS MozSmsMessage.receiver field should be %s" % self.out_destination)
        # timezones and different SMSC's, don't check timestamp value; just ensure non-zero
        self.assertGreater(self.out_msg['timestamp'], 0, "Sent SMS MozSmsMessage.timestamp should not be 0")
        self.assertTrue(self.out_msg['messageClass'] in ["class-0", "class-1", "class-2", "class-3", "normal"],
                        "Sent SMS MozSmsMessage.messageClass must be a valid class")
