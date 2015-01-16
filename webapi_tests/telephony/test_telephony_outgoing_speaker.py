# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyOutgoingSpeaker(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Ask the test user to specify a destination phone number for the test call
    - Setup mozTelephonyCall event listeners for the outgoing call
    - Use the API to initiate the outgoing call
    - Ask the test user to answer the call on the destination phone
    - Keep the call active for 5 seconds
    - Turn on speaker using the API and ask the test user to verify
    - Turn off speaker using the API and ask the test user to verify
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
        super(TestTelephonyOutgoingSpeaker, self).setUp()
        self.wait_for_obj("window.navigator.mozTelephony")
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_outgoing_speaker(self):
        # use the webapi to make an outgoing call to user-specified number; user answer
        self.user_guided_outgoing_call()
        # verify one outgoing call
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 1, "There should be 1 call")
        self.assertEqual(self.calls['0'], self.outgoing_call)

        # have user answer the call on target
        self.answer_call(incoming=False)

        # keep call active for a while
        time.sleep(5)

        # verify the active call
        self.assertEqual(self.active_call_list[0]['number'], self.outgoing_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")
        self.assertEqual(self.active_call_list[0]['state'], "connected", "Call state should be 'connected'")

        # enable speaker
        self.set_speaker(enable=True)
        self.confirm("Is the call now on speaker mode?")

        # keep a delay for speaker turn off confirmation
        time.sleep(2)
        # disable speaker
        self.set_speaker(enable=False)
        self.confirm("Is the call 'not' on speaker mode now?")

        # disconnect the active call
        self.hangup_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
        self.active_call_list = []
