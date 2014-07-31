# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestSmsIncomingDelete(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Receive an incoming SMS (sent by the test user)
    - Delete the SMS
    - Verify that the SMS can no longer be retrieved

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestSmsIncomingDelete, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestSmsIncomingDelete, self).tearDown()

    def test_sms_incoming_delete(self):
        # have user send sms to the Firefox OS device
        self.msg_type = "SMS"
        self.user_guided_incoming_msg()

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the SMS using the webapi
        sms_to_delete = self.in_msg['id']
        self.delete_message(sms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        sms = self.get_message(sms_to_delete)
        self.assertIsNone(sms, "The SMS should not have been found because it was deleted")
