# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncomingGetMessage(TestCase, MobileMessageTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        super(TestSmsIncomingGetMessage, self).tearDown()

    def test_sms_incoming_get_message(self):
        # have user send sms to the Firefox OS device, verify body
        self.user_guided_incoming_sms()

        # test mozMobileMessage.getMessage with valid id
        sms_to_get = self.in_msg['id']
        error_message = "mozMobileMessage.getMessage should have found the SMS message"
        self.get_message(sms_to_get, True, error_message)

        # verify the other found message fields
        event_sms = self.marionette.execute_script("return window.wrappedJSObject.event_sms")
        self.assertEqual(event_sms['id'], sms_to_get, "MozMobileMessage.id of found SMS should match the received SMS")
        self.assertEqual(event_sms['body'], self.in_msg['body'], "Message body of the found SMS should match the received SMS")

        self.assertEqual(event_sms['type'], self.in_msg['type'], "Found SMS MozSmsMessage.type should match")
        self.assertEqual(event_sms['id'], self.in_msg['id'], "Found SMS MozSmsMessage.id should match")
        self.assertEqual(event_sms['threadId'], self.in_msg['threadId'], "Found SMS MozSmsMessage.threadId should match")
        self.assertEqual(event_sms['delivery'], self.in_msg['delivery'], "Found SMS MozSmsMessage.delivery should match")
        self.assertEqual(event_sms['deliveryStatus'], self.in_msg['deliveryStatus'],
                          "Found SMS MozSmsMessage.deliveryStatus should match")
        # cant guarantee user didn't read message; just ensure is valid
        self.assertTrue(event_sms['read'] is False or event_sms['read'] is True,
                        "Found SMS MozSmsMessage.read field should be False or True")
        self.assertEqual(event_sms['receiver'], self.in_msg['receiver'], "Found SMS MozSmsMessage.receiver should match")
        self.assertEqual(event_sms['sender'], self.in_msg['sender'], "Found SMS MozSmsMessage.sender field should match")
        self.assertEqual(event_sms['timestamp'], self.in_msg['timestamp'], "Found SMS MozSmsMessage.timestamp should match")
        self.assertEqual(event_sms['messageClass'], self.in_msg['messageClass'],
                         "Found SMS MozSmsMessage.messageClass should match")

        # test mozMobileMessage.getMessage with invalid message object; should fail
        sms_to_get = self.in_msg['id'] + 999 # no chance of receiving 999 more SMS between test cases
        error_message = "mozMobileMessage.getMessage should NOT have found the SMS message"
        self.get_message(sms_to_get, False, error_message)
