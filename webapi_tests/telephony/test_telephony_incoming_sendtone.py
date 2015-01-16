# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony.telephony_test import TelephonyTestCommon


class TestTelephonyIncomingSendtone(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active for 3 seconds
    - Send a DTMF tone for one character ('0' in this test case) and ask the test user to verify
    - Stop transmitting the currently playing DTMF tone and ask the test user to verify
    - Hangup the call via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        TelephonyTestCommon.__init__(self)

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingSendtone, self).setUp()
        self.wait_for_obj("window.navigator.mozTelephony")
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming_sendtone(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['0'], self.incoming_call)

        # answer the incoming call
        self.answer_call()
        self.assertEqual(self.active_call_list[0]['state'], "connected", "Call state should be 'connected'")
        self.assertEqual(self.active_call_list[0]['number'], self.incoming_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")

        # keep call active for a while
        time.sleep(3)

        # send a DTMF tone for character '0'
        self.marionette.execute_script("window.navigator.mozTelephony.startTone(0);")
        time.sleep(2)
        self.confirm("Did you hear the DTMF tone on other (not the Firefox OS) phone?")
        self.marionette.execute_script("window.navigator.mozTelephony.stopTone();")

        # disconnect the active call
        self.hangup_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
        self.active_call_list = []
