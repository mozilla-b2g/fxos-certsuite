# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony.telephony_test import TelephonyTestCommon


class TestTelephonyIncomingTwoCallsAutoSwap(TestCase, TelephonyTestCommon):

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingTwoCallsAutoSwap, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming_twocalls_autoswap(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['0'], self.incoming_call)

        self.answer_call()
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")

        # keep call active for a while
        time.sleep(5)

        # ask user to again call to the test device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['1'], self.incoming_call)

        self.answer_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 2, "There should be 2 active calls")

        # keep call active for a while
        time.sleep(5)

        #verify call state change
        self.assertEqual((self.calls['0'])['state'], "held", "Call state should be 'held'")
        self.assertEqual((self.calls['1'])['state'], "connected", "Call state should be 'connected'")

        # disconnect the two active calls
        self.hangup_call(active_calls_list=1)
        time.sleep(10)
        self.hangup_call(active_calls_list=0)

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
