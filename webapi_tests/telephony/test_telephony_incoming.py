# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncoming(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active for 5 seconds
    - Hang up the call via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncoming, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    @unittest.skip("Currently disabled in 1.3, bug 997248")
    def test_telephony_incoming(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
