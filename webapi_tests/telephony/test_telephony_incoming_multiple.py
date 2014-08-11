# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony.telephony_test import TelephonyTestCommon


class TestTelephonyIncomingMultiple(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active for 5 seconds
    - While first call is active, ask the test user to phone the Firefox OS device from third phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the second incoming call via the API
    - Verify that the first call state should be on held while second call becomes active
    - Hangup both calls via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        TelephonyTestCommon.__init__(self)

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingMultiple, self).setUp()
        self.wait_for_obj("window.navigator.mozTelephony")
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming_multiple(self):
        # ask user to make first call to the device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['0'], self.incoming_call)

        self.answer_call()
        self.assertTrue(self.active_call_list[0]['state'], "connected")
        self.assertEqual(self.active_call_list[0]['number'], self.incoming_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")
        self.assertEqual((self.calls['0'])['state'], "connected", "Call state should be 'connected'")

        # keep call active for a while
        time.sleep(5)

        # ask user to again call to the test device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['1'], self.incoming_call)
        self.assertEqual(self.calls['0'], self.active_call_list[0])

        self.answer_call()
        self.assertTrue(self.active_call_list[1]['state'], "connected")
        self.assertEqual(self.active_call_list[1]['number'], self.incoming_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 2, "There should be 2 active calls")

        # keep call active for a while
        time.sleep(5)

        # verify call state change
        self.assertEqual((self.calls['0'])['state'], "held", "Call state should be 'held'")
        self.assertEqual((self.calls['1'])['state'], "connected", "Call state should be 'connected'")

        # disconnect the two active calls
        self.hangup_call(active_call_selected=1)

        # keep a delay to get the change in call state
        time.sleep(2)

        # verify number of remaining calls and its state
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")
        self.assertEqual((self.calls['0'])['state'], "connected", "Call state should be 'connected'")

        self.hangup_call(active_call_selected=0)
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
        self.active_call_list = []
