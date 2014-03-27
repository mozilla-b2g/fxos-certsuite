# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from tests import TestCase, test
from tests.sms import SmsTestCommon


class TestSmsIncomingDelete(TestCase, SmsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        TestCase.tearDown(self)

    @test
    def test_sms_incoming_delete(self):
        self.setup_onreceived_listener()
        self.instruct("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive")
        self.verify_sms_received()
        self.remove_onreceived_listener()

        # verify text content
        self.confirm("Received SMS with text '%s'; does this text match what was sent to the Firefox OS phone?" %self.in_sms['body'])

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the SMS using the webapi
        sms_to_delete = self.in_sms['id']
        self.delete_message(sms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        error_message = "mozMobileMessage.getMessage found the deleted SMS but shouldn't have; delete failed"
        self.get_message(sms_to_delete, False, error_message)
