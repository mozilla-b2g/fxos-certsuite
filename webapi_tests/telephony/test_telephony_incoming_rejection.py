# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncomingRejection(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Reject the incoming call via the API,
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    This test is currently only enabled in version 1.3 of the certification test suite.

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingRejection, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    @unittest.skip("Currently disabled in 1.4")
    def test_telephony_incoming_rejection(self):
        # ask user to call the device and reject via webapi
        self.user_guided_incoming_call_reject()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
