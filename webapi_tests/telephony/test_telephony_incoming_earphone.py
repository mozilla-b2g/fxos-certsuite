# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncomingEarphone(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active
    - Ask the user to use earphone for talking
    - Ask the user to remove earphone and continue talking
    - Hang up the call via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingEarphone, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming_earphone(self):
        # ask user to call the device
        self.user_guided_incoming_call()

        # answer and verify via webapi
        self.answer_call()
        self.instruct("Connect the earphone to Firefox OS device to talk and press Ok")
        self.confirm("Are you able to hear through earphone?")

        time.sleep(5)

        self.instruct("Remove the earphone from Firefox OS device to continue talking and press Ok")
        self.confirm("Are you able talk through phone?")
        # disconnect the call
        self.hangup_call(self.active_call)

        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
