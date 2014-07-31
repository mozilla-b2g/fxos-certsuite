# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.mobile_message import MobileMessageTestCommon


class TestMmsIncomingDelete(TestCase, MobileMessageTestCommon):
    """
    This is a test for the `WebSMS API`_ which will:

    - Receive an incoming MMS (sent by the test user)
    - Delete the MMS
    - Verify that the MMS can no longer be retrieved

    .. _`WebSMS API`: https://developer.mozilla.org/en-US/docs/Web/API/WebSMS_API
    """

    def setUp(self):
        super(TestMmsIncomingDelete, self).setUp()
        self.wait_for_obj("window.navigator.mozMobileMessage")

    def tearDown(self):
        super(TestMmsIncomingDelete, self).tearDown()

    def test_mms_incoming_delete(self):
        # have user send mms to the Firefox OS device
        self.msg_type = "MMS"
        self.user_guided_incoming_msg(msg_type="MMS")

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the mms using the webapi
        mms_to_delete = self.in_msg['id']
        self.delete_message(mms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        mms = self.get_message(mms_to_delete)
        self.assertIsNone(mms, "The MMS should not have been found because it was deleted")
