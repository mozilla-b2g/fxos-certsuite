# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
from marionette.wait import Wait

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncomingHoldOutgoing(TestCase, TelephonyTestCommon):
    """
    This is a test for the `WebTelephony API`_ which will:

    - Disable the default gaia dialer, so that the test app can handle calls
    - Setup a mozTelephony event listener for incoming calls
    - Ask the test user to phone the Firefox OS device from a second phone
    - Verify that the mozTelephony incoming call event is triggered
    - Answer the incoming call via the API, keep the call active for 5 seconds
    - Use the API to initiate the outgoing call from the Firefox OS device to third phone
    - Verify the first call state should be held and corresponding events were triggered
    - Ask the test user to answer the call on the third phone
    - Verify that the first call state still should be on held while second call becomes active
    - Hang up the connected call via the API
    - Verify the held call is now resumed and the only active call
    - Hang up the remaining active call via the API
    - Verify that the corresponding mozTelephonyCall events were triggered
    - Re-enable the default gaia dialer

    .. _`WebTelephony API`: https://developer.mozilla.org/en-US/docs/Web/Guide/API/Telephony
    """

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        TelephonyTestCommon.__init__(self)

    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncomingHoldOutgoing, self).setUp()
        self.wait_for_obj("window.navigator.mozTelephony")
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming_hold_outgoing(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['0'], self.incoming_call)

        self.answer_call()
        self.assertEqual(self.active_call_list[0]['state'], "connected", "Call state should be 'connected'")
        self.assertEqual(self.active_call_list[0]['number'], self.incoming_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call")

        # keep call active for a while
        time.sleep(5)

        self.hold_active_call(user_initiate_hold=False)
        # use the webapi to make an outgoing call to user-specified number
        self.user_guided_outgoing_call()

        # setup the 'onheld' event handler
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.onheld_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
        except:
            # failed to hold
            self.fail("Failed to put first active call on hold while second call becomes active")

        onholding = self.marionette.execute_script("return window.wrappedJSObject.onholding_call_ok")
        self.assertFalse(onholding, "Telephony.onholding event found, but should not have been "
                            "since the phone user did not initiate holding the call")

        # verify that there are two calls of which first incoming call is held while second is outgoing call
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 2, "There should be 2 calls")
        self.outgoing_call = self.marionette.execute_script("return window.wrappedJSObject.returnable_outgoing_call")
        self.assertEqual(self.calls['1'], self.outgoing_call)
        self.assertEqual(self.calls['0']['state'], "held", "Call state should be 'held'")

        # have user answer the call on target
        self.answer_call(incoming=False)
        # keep call active for a while
        time.sleep(5)
        # verify the active call
        self.assertEqual(self.active_call_list[1]['state'], "connected", "Call state should be 'connected'")
        self.assertEqual(self.active_call_list[1]['number'], self.outgoing_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 2, "There should be 2 active call")

        # verify call state change
        self.assertEqual(self.calls['0']['state'], "held", "Call state should be 'held'")
        self.assertEqual(self.calls['1']['state'], "connected", "Call state should be 'connected'")

        # disconnect the two active calls
        self.hangup_call(active_call_selected=1)

        # verify number of remaining calls and its state
        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return (window.wrappedJSObject.calls.length == 1)"))
            wait.until(lambda x: x.execute_script("return (window.wrappedJSObject.calls[0].state == \"connected\")"))
        except:
            self.fail("Failed to hangup the second call or change the state of first call")

        # disconnect the active call
        self.hangup_call(active_call_selected=0)
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.get_returnable_calls()")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls")

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
        self.active_call_list = []
