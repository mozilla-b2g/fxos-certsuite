# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase
from sms import SmsTestCommon


class TestSmsOutgoing(TestCase, SmsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        TestCase.tearDown(self)

    def test_sms_outgoing(self):
        # ask user to input destination phone number
        destination = self.prompt("Please enter a destination phone number where a test SMS will be sent (not the Firefox OS device)")
        destination = str(destination)
        # can't check format as different around the world, make sure not empty
        self.assertTrue(len(destination) > 1, "Destination phone number must be entered")

        # ask user to confirm destination number
        self.confirm("You entered destination number '%s', is this correct?" %destination)

        # ask user to input sms body text
        body = self.prompt("Please enter some text to be sent in the SMS message")
        self.assertTrue(len(body) > 0 & len(body) < 161,
                         "SMS message text entered must be between 1 and 160 characters long")

        self.setup_onsent_listener()
        # use the webapi to send an sms
        self.send_message(destination, body)

        # user verification that it was received on target, before continue
        self.confirm("SMS has been sent to '%s'. Was it received on the target phone?" %destination)

        self.verify_message_sent()
        self.remove_onsent_listener()

        # verify message body
        self.assertTrue(len(self.out_sms['body']) > 0, "Sent SMS event message has no message body")
        self.confirm("Sent SMS with text '%s'; does this text match what was received on the target phone?" %self.out_sms['body'])

        # verify the other message fields
        self.assertEqual(self.out_sms['type'], 'sms', "Sent SMS MozSmsMessage.type should be 'sms'")
        self.assertTrue(self.out_sms['id'] > 0, "Sent SMS MozSmsMessage.id should be > 0")
        self.assertTrue(self.out_sms['threadId'] > 0, "Sent SMS MozSmsMessage.threadId should be > 0")
        self.assertEqual(self.out_sms['delivery'], 'sent', "Sent SMS MozSmsMessage.delivery should be 'sent'")
        self.assertTrue((self.out_sms['deliveryStatus'] == 'success') | (self.out_sms['deliveryStatus'] == 'not-applicable'),
                        "Sent SMS MozSmsMessage.deliveryStatus should be 'success' or 'not-applicable'")
        # cannot guarantee end-user didn't read message; test that specifically in a different test
        self.assertTrue(((self.out_sms['read'] == False) or (self.out_sms['read'] == True)),
                        "Sent SMS MozSmsMessage.read field should be False or True")
        # can check receiver number as the user provided it above
        self.assertTrue(destination in self.out_sms['receiver'], "Sent SMS MozSmsMessage.receiver field should be %s" %destination)
        # for privacy, don't print/check the actual sender's number; just ensure it is not empty
        self.assertTrue(len(self.out_sms['sender']) > 0, "Sent SMS MozSmsMessage.sender field should not be empty")
        # timezones and different SMSC's, don't check timestamp value; just ensure non-zero
        self.assertTrue(self.out_sms['timestamp'] > 0, "Sent SMS MozSmsMessage.timestamp should not be 0")
        self.assertTrue(self.out_sms['messageClass'] in ["class-0", "class-1", "class-2", "class-3", "normal"],
                        "Sent SMS MozSmsMessage.messageClass must be a valid class")
