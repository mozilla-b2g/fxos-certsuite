# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncomingGetMessage(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Receive an incoming SMS (sent by the test user)
    - Verify that the SMS can be retrieved
    - Verify the retrieved mozSmsMessage attributes

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestSmsIncomingGetMessage, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestSmsIncomingGetMessage, self).tearDown()

    def test_sms_incoming_get_message(self):
        # have user send an sms to the Firefox OS device
        self.msg_type = "SMS"
        self.user_guided_incoming_msg()

        # test mozMobileMessage.getMessage with valid id
        sms = self.get_message(self.in_msg['id'])
        self.assertIsNotNone(sms, "The incoming SMS was not found but should have been")

        # verify the message fields
        self.assertEqual(sms['id'], self.in_msg['id'], "MozMobileMessage.id of found SMS should match the received SMS")
        self.assertEqual(sms['body'], self.in_msg['body'], "Message body of the found SMS should match the received SMS")

        self.assertEqual(sms['type'], self.in_msg['type'], "Found SMS MozSmsMessage.type should match")
        self.assertEqual(sms['id'], self.in_msg['id'], "Found SMS MozSmsMessage.id should match")
        self.assertEqual(sms['threadId'], self.in_msg['threadId'], "Found SMS MozSmsMessage.threadId should match")
        self.assertEqual(sms['delivery'], self.in_msg['delivery'], "Found SMS MozSmsMessage.delivery should match")
        self.assertEqual(sms['deliveryStatus'], self.in_msg['deliveryStatus'],
                          "Found SMS MozSmsMessage.deliveryStatus should match")
        # can't guarantee user didn't read message; just ensure is valid
        self.assertTrue(sms['read'] is False or sms['read'] is True,
                        "Found SMS MozSmsMessage.read field should be False or True")
        self.assertEqual(sms['receiver'], self.in_msg['receiver'], "Found SMS MozSmsMessage.receiver should match")
        self.assertEqual(sms['sender'], self.in_msg['sender'], "Found SMS MozSmsMessage.sender field should match")
        self.assertEqual(sms['timestamp'], self.in_msg['timestamp'], "Found SMS MozSmsMessage.timestamp should match")
        self.assertEqual(sms['messageClass'], self.in_msg['messageClass'],
                         "Found SMS MozSmsMessage.messageClass should match")

        # test mozMobileMessage.getMessage with invalid message object; should fail
        invalid_sms = self.in_msg['id'] + 999  # no chance of receiving 999 more SMS between test cases
        sms = self.get_message(invalid_sms)
        self.assertIsNone(sms, "The SMS should not have been found because an invalid SMS id was used in getMessage")
