# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from sms import SmsTestCommon


class TestSmsIncomingDelete(TestCase, SmsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        TestCase.tearDown(self)

    def test_sms_incoming_delete(self):
        # have user send sms to the Firefox OS device, verify body
        self.user_guided_incoming_sms()

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the SMS using the webapi
        sms_to_delete = self.in_sms['id']
        self.delete_message(sms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        error_message = "mozMobileMessage.getMessage found the deleted SMS but shouldn't have; delete failed"
        self.get_message(sms_to_delete, False, error_message)
