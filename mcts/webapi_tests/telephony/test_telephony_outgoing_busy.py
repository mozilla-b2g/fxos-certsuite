# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest
from marionette.wait import Wait

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyOutgoingBusy(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Make a call to the second non firefox OS phone from third non firefox OS phone
    - Answer the call on second phone to make it a busy line
    - Ask the test user to specify a phone number of second phone for the test call from firefox phone
    - Setup mozTelephonyCall event listeners for the outgoing call
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyOutgoingBusy, self).setUp()
        self.wait_for_obj("window.navigator.mozTelephony")
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    @unittest.skip("Skipping this test as 'BusyError' error name is not received while making call to busy line, "
                   "Instead receiving 'UnspecifiedError', refer Bug-1060129")
    def test_telephony_outgoing_busy(self):
        self.instruct("Make a call to second non firefox OS phone from third non firefox "
                       "OS phone, answer the call on second phone and press OK")
        # keep a short delay before making an outgoing call to second phone
        time.sleep(2)

        # use the webapi to make an outgoing call to user-specified number
        self.user_guided_outgoing_call()
        # verify one outgoing call
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 1, "There should be 1 call")
        self.assertEqual(self.calls['0'], self.outgoing_call)

        # should have received busy event associated with an outgoing call
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_busy"))
        except:
            self.fail("Busy event is not found, but should have been, since the outgoing call "
                      "is initiated to busy line")

        # keep call ringing for a while
        time.sleep(1)

        # disconnect the outgoing call
        self.hangup_call(call_type="Outgoing")
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
