# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyOutgoing(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Ask the test user to specify a destination phone number for the test call
    - Setup mozTelephonyCall event listeners for the outgoing call
    - Use the API to initiate the outgoing call
    - Ask the test user to answer the call on the destination phone
    - Keep the call active for 5 seconds, then hang up the call via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    This test is currently only enabled in version 1.3 of the certification test suite.

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyOutgoing, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    @unittest.skip("Currently disabled in 1.4")
    def test_telephony_outgoing(self):
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

        # use the webapi to make an outgoing call to user-specified number; user answer
        self.user_guided_outgoing_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
