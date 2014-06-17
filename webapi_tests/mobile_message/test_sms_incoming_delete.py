# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncomingDelete(TestCase, MobileMessageTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        super(TestSmsIncomingDelete, self).tearDown()

    def test_sms_incoming_delete(self):
        # have user send sms to the Firefox OS device
        self.user_guided_incoming_sms()

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the SMS using the webapi
        sms_to_delete = self.in_msg['id']
        self.delete_message(sms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        sms = self.get_message(sms_to_delete)
        self.assertIsNone(sms, "The SMS should not have been found because it was deleted")
