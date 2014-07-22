# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncomingHangup(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active for 5 seconds
    - Ask the test user to hang up the call from second phone
    - Verify that the corresponding mozTelephonyCall event is triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingHangup, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.answer_call()

        # keep call active for awhile
        time.sleep(5)

        #set up the event handler for disconnect
        self.hangup_call(terminate_from_secondary_caller=True)

        self.instruct("Hangup the call from secondary phone and press 'OK'")
        self.verify_call_terminated_from_secondary_device()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
