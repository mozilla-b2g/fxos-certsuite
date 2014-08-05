# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestMmsIncoming(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Verify that an MMS can be received (sent by the test user)
    - Confirm that the associated mozMobileMessage received event is triggered
    - Verify the mozMmsMessage attributes

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestMmsIncoming, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestMmsIncoming, self).tearDown()

    def test_mms_incoming(self):
        # have user send mms to the Firefox OS device
        self.msg_type = "MMS"
        self.user_guided_incoming_msg(msg_type="MMS")

        # verify message contents
        self.assertEqual(self.in_msg['type'], 'mms', "Received MMS MozMmsMessage.type should be 'mms'")
        self.assertGreater(self.in_msg['id'], 0, "Received MMS MozMmsMessage.id should be > 0")
        self.assertGreater(self.in_msg['threadId'], 0, "Received MMS MozMmsMessage.threadId should be > 0")
        self.assertIn(self.in_msg['delivery'], ['received', 'not-download'], "Received MMS MozMmsMessage.delivery "
                        "should be 'received' or 'not-download")
        # cannot guarantee end-user didn't read message; test that specifically in a different test
        self.assertTrue(self.in_msg['read'] is False or self.in_msg['read'] is True,
                        "Received MMS MozMmsMessage.read field should be False or True")
        # for privacy, don't print/check actual receiver (Firefox OS) phone number; just ensure not empty
        self.assertGreater(len(self.in_msg['receivers']), 0, "Received MMS MozMmsMessage.receivers field should not be empty")
        # for privacy, don't print/check the actual sender's number; just ensure it is not empty
        self.assertGreater(len(self.in_msg['sender']), 0, "Received MMS MozMmsMessage.sender field should not be empty")
        # timezones and different SMSC's, don't check timestamp value; just ensure non-zero
        self.assertGreater(self.in_msg['timestamp'], 0, "Received MMS MozMmsMessage.timestamp should not be 0")
        self.assertIsNotNone(self.in_msg['smil'], "Received MMS MozMmsMessage.smil should exist")
        self.assertIsNotNone(self.in_msg['attachments'], "Received MMS MozMmsMessage.attachments should exist")
        self.assertGreater(len(self.in_msg['attachments']), 0, "Received MMS MozMmsMessage is missing the attachment")
        attachment = self.in_msg['attachments'][0]
        self.assertIsNotNone(attachment['id'], "Received MMS MozMmsMessage attachment.id should exist")
        self.assertIsNotNone(attachment['location'], "Received MMS MozMmsMessage attachment.location should exist")
        self.assertIsNotNone(attachment['content'], "Received MMS MozMmsMessage.attachment.blob should exist")
