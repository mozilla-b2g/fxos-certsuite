# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class TelephonyTestCommon(object):
    def __init__(self):
        self.calls = None
        self.incoming_call = None
        self.outgoing_call = None
        self.active_call = None

    def setup_incoming_call(self):
        # listen for and answer incoming call
        self.marionette.execute_async_script("""
        var telephony = window.navigator.mozTelephony;
        window.wrappedJSObject.received_incoming = false;
        telephony.onincoming = function onincoming(event) {
          log("Received 'incoming' call event.");
          window.wrappedJSObject.received_incoming = true;
          window.wrappedJSObject.incoming_call = event.call;
          window.wrappedJSObject.calls = telephony.calls;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def verify_incoming_call(self):
        try:
            received = self.marionette.execute_script("return window.wrappedJSObject.received_incoming")
            self.assertTrue(received, "Incoming call not received (Telephony.onincoming event not found)")
            self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
            self.assertEqual(self.calls['length'], 1, "There should be 1 incoming call" )
            self.incoming_call = self.marionette.execute_script("return window.wrappedJSObject.incoming_call")
            self.assertEqual(self.incoming_call['state'], "incoming", "Call state should be 'incoming'")
            self.assertEqual(self.calls['0'], self.incoming_call)
        finally:
            self.marionette.execute_script("window.navigator.mozTelephony.onincoming = null;")

    def answer_call(self, incoming=True):
        # answer incoming call via the webapi; have user answer outgoing call on target
        self.marionette.execute_async_script("""
        let incoming = arguments[0];

        if (incoming) {
          var call_to_answer = window.wrappedJSObject.incoming_call;
        } else {
          var call_to_answer = window.wrappedJSObject.outgoing_call;
        };

        window.wrappedJSObject.connecting_call_ok = false;
        call_to_answer.onconnecting = function onconnecting(event) {
          log("Received 'onconnecting' call event.");
          if (event.call.state == "connecting") {
            window.wrappedJSObject.connecting_call_ok = true;
          };
        };

        window.wrappedJSObject.connected_call_ok = false;
        call_to_answer.onconnected = function onconnected(event) {
          log("Received 'onconnected' call event.");
          if (event.call.state == "connected") {
            window.wrappedJSObject.active_call = window.navigator.mozTelephony.active;
            window.wrappedJSObject.connected_call_ok = true;
          };
        };

        // answer incoming call via webapi; outgoing will be by user interaction
        if (incoming) {
            call_to_answer.answer();
        };

        marionetteScriptFinished(1);
        """, script_args=[incoming], special_powers=True)

        # answer outgoing call via user answering on target
        if not incoming:
            self.instruct("Please answer the call on the target phone, then click 'OK'")

        # should have received both events associated with answering a call
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            if incoming: # only receive 'onconnecting' for incoming call
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.connecting_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.connected_call_ok"))
        except:
            self.fail("Failed to answer call")

        # verify the active call
        self.active_call = self.marionette.execute_script("return window.wrappedJSObject.active_call")
        self.assertTrue(self.active_call['state'], "connected")
        if incoming:
            self.assertEqual(self.active_call['number'], self.incoming_call['number'])
        else:
            self.assertEqual(self.active_call['number'], self.outgoing_call['number'])
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 1, "There should be 1 active call" )
        self.assertEqual(self.calls['0'], self.active_call)

    def user_guided_incoming_call(self):
        # ask user to call the device; answer and verify via webapi
        self.setup_incoming_call()
        self.instruct("From a different phone, call the Firefox OS device, and when you \
                      hear the ringing signal click 'OK'")
        self.verify_incoming_call()
        self.answer_call()

    def hangup_active_call(self):
        # hangup the active call, verify
        self.marionette.execute_async_script("""
        let active = window.wrappedJSObject.active_call;

        window.wrappedJSObject.disconnecting_call_ok = false;
        active.ondisconnecting = function ondisconnecting(event) {
          log("Received 'ondisconnecting' call event.");
          if (event.call.state == "disconnecting") {
            window.wrappedJSObject.disconnecting_call_ok = true;
          };
        };

        window.wrappedJSObject.disconnected_call_ok = false;
        active.ondisconnected = function ondisconnected(event) {
          log("Received 'ondisconnected' call event.");
          if (event.call.state == "disconnected") {
            window.wrappedJSObject.disconnected_call_ok = true;
          };
        };

        active.hangUp();
        marionetteScriptFinished(1);
        """, special_powers=True)

        # should have received both events associated with a call hangup
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.disconnecting_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.disconnected_call_ok"))
        except:
            # failed to hangup
            self.fail("Failed to hangup call")

        # verify no active call
        self.active_call = self.marionette.execute_script("return window.wrappedJSObject.active_call")
        self.assertTrue(self.active_call, None)
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 0, "There should be 0 calls" )

    def initiate_outgoing_call(self, destination):
        # use the webapi to initiate a call to the specified number
        self.marionette.execute_async_script("""
        var telephony = window.navigator.mozTelephony;
        var destination = arguments[0]
        var out_call = telephony.dial(destination);

        window.wrappedJSObject.received_dialing = false;
        if (out_call.state == "dialing") {
            window.wrappedJSObject.received_dialing = true;
        };

        window.wrappedJSObject.received_statechange = false;
        out_call.onstatechange = function onstatechange(event) {
          log("Received TelephonyCall 'onstatechange' event.");
          if (event.call.state == "alerting") {
            window.wrappedJSObject.received_statechange = true;
          };
        };

        window.wrappedJSObject.received_alerting = false;
        out_call.onalerting = function onalerting(event) {
          log("Received TelephonyCall 'onalerting' event.");
          if (event.call.state == "alerting") {
            window.wrappedJSObject.received_alerting = true;
            window.wrappedJSObject.outgoing_call = out_call;
            window.wrappedJSObject.calls = telephony.calls;
          };
        };

        window.wrappedJSObject.received_busy = false;
        out_call.onbusy = function onbusy(event) {
          log("Received TelephonyCall 'onbusy' event.");
          if (event.call.state == "busy") {
            window.wrappedJSObject.received_busy = true;
          };
        };

        marionetteScriptFinished(1);
        """, script_args=[destination], special_powers=True)

        # should have received all events associated with an outgoing call
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_dialing"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_alerting"))
        except:
            # failed to initiate call; check if the destination phone's line was busy
            busy = self.marionette.execute_script("return window.wrappedJSObject.received_busy")
            self.assertFalse(busy, "Received busy signal; ensure target phone is available and try again")
            self.fail("Failed to initiate call; mozTelephony.dial is broken -or- there is no network signal. Try again")

        # verify one outgoing call
        self.calls = self.marionette.execute_script("return window.wrappedJSObject.calls")
        self.assertEqual(self.calls['length'], 1, "There should be 1 call" )
        self.outgoing_call = self.marionette.execute_script("return window.wrappedJSObject.outgoing_call")
        self.assertEqual(self.outgoing_call['state'], "alerting", "Call state should be 'alerting'")
        self.assertEqual(self.calls['0'], self.outgoing_call)

    def user_guided_outgoing_call(self):
        # ask user to input destination phone number
        destination = self.prompt("Please enter a destination phone number (not the Firefox OS device) which will receive a test call")

        # can't check format as different around the world, just ensure not empty
        if destination is None:
            self.fail("Must enter a destination phone number")

        destination = destination.strip()
        self.assertGreater(len(destination), 3, "Destination phone number entered is incomplete")

        # ask user to confirm destination number
        self.confirm('Warning: A test call will be made from the Firefox OS device to "%s" is this number correct?' %destination)

        # make the call via webapi
        self.initiate_outgoing_call(destination)

        # have user answer the call on target, verify
        self.answer_call(incoming=False)

    def disable_dialer(self):
        # disable system dialer agent so it doesn't steal the
        # incoming/outgoing calls away from the certest app
        cur_frame = self.marionette.get_active_frame()
        self.marionette.switch_to_frame() # system app
        try:
            self.marionette.execute_async_script("""
            log("disabling system dialer agent");
            window.wrappedJSObject.dialerAgent.stop();
            marionetteScriptFinished(1);
            """, special_powers=True)
        except:
            self.fail("failed to disable dialer agent")
        finally:
            self.marionette.switch_to_frame(cur_frame)

    def enable_dialer(self):
        # enable system dialer agent to handle calls
        cur_frame = self.marionette.get_active_frame()
        self.marionette.switch_to_frame() # system app
        try:
            self.marionette.execute_async_script("""
            log("enabling system dialer agent");
            window.wrappedJSObject.dialerAgent.start();
            marionetteScriptFinished(1);
            """, special_powers=True)
        except:
            self.fail("failed to disable dialer agent")
        finally:
            self.marionette.switch_to_frame(cur_frame)
