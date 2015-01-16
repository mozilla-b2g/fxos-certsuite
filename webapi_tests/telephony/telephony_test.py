# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class TelephonyTestCommon(object):

    returnable_calls = """
        window.wrappedJSObject.get_returnable_calls = function() {
          let calls = {};
          for (let i in window.navigator.mozTelephony.calls) {
            let call = {
              number: window.navigator.mozTelephony.calls[i].number,
              state: window.navigator.mozTelephony.calls[i].state
            }
            calls[i] = call;
          }
          calls['length'] = window.navigator.mozTelephony.calls['length'];
          return calls;
        }
    """

    def __init__(self):
        self.active_call_list = []

    def setup_incoming_call(self):
        self.marionette.execute_script(self.returnable_calls)

        # listen for and answer incoming call
        self.marionette.execute_async_script("""
        var telephony = window.navigator.mozTelephony;
        window.wrappedJSObject.received_incoming = false;
        telephony.onincoming = function onincoming(event) {
          log("Received 'incoming' call event.");
          window.wrappedJSObject.received_incoming = true;
          window.wrappedJSObject.incoming_call = event.call;
          window.wrappedJSObject.returnable_incoming_call = {
            number: event.call.number,
            state: event.call.state
          };
          window.wrappedJSObject.calls = telephony.calls;
        };

        window.wrappedJSObject.received_callschanged = false;
        telephony.oncallschanged = function oncallschanged(event) {
          log("Received Telephony 'oncallschanged' event.");
          window.wrappedJSObject.received_callschanged = true;
        };

        marionetteScriptFinished(1);
        """, special_powers=True)

        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_callschanged"))
        except:
            self.fail("Telephony.oncallschanged event not found, but should have been "
                      "since initiated incoming call to firefox OS device")

    def verify_incoming_call(self):
        try:
            received = self.marionette.execute_script("return window.wrappedJSObject.received_incoming")
            self.assertTrue(received, "Incoming call not received (Telephony.onincoming event not found)")
            self.incoming_call = self.marionette.execute_script("return window.wrappedJSObject.returnable_incoming_call")
            self.assertEqual(self.incoming_call['state'], "incoming", "Call state should be 'incoming'")
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

        window.wrappedJSObject.received_statechange = false;
        call_to_answer.onstatechange = function onstatechange(event) {
        log("Received TelephonyCall 'onstatechange' event.");
          if (event.call.state == "connected") {
            window.wrappedJSObject.received_statechange = true;
          };
        };

        window.wrappedJSObject.connected_call_ok = false;
        call_to_answer.onconnected = function onconnected(event) {
          log("Received 'onconnected' call event.");
          if (event.call.state == "connected") {
            window.wrappedJSObject.active_call = window.navigator.mozTelephony.active;
            window.wrappedJSObject.returnable_active_call = {
                state: window.navigator.mozTelephony.active.state,
                number: window.navigator.mozTelephony.active.number
            };
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
            if incoming:  # only receive 'onconnecting' for incoming call
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.connecting_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.connected_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
        except:
            self.fail("Failed to answer call")

        # append new call to the active call list
        self.active_call_list.append(self.marionette.execute_script("return window.wrappedJSObject.returnable_active_call"))

    def user_guided_incoming_call(self):
        # ask user to call the device; answer and verify via webapi
        self.setup_incoming_call()
        self.instruct("From a different phone, call the Firefox OS device, and when you \
                      hear the ringing signal click 'OK'")
        self.verify_incoming_call()

    def hangup_call(self, call_type="Active", remote_hangup=False, active_call_selected=0):
        # hangup the active/incoming call, verify
        self.marionette.execute_async_script("""
        var call_type = arguments[0];
        var remote_hangup = arguments[1];
        var active_call_selected = arguments[2];
        window.wrappedJSObject.rcvd_error = false;
        if (call_type == "Incoming") {
          var call_to_hangup = window.wrappedJSObject.incoming_call;
        } else if (call_type == "Outgoing") {
          var call_to_hangup = window.wrappedJSObject.outgoing_call;
        } else {
          if (active_call_selected >=0 && active_call_selected < window.wrappedJSObject.calls.length) {
            var call_to_hangup = window.wrappedJSObject.calls[active_call_selected];
          } else {
            window.wrappedJSObject.rcvd_error = true;
            marionetteScriptFinished(0);
          }
        };

        window.wrappedJSObject.disconnecting_call_ok = false;
        call_to_hangup.ondisconnecting = function ondisconnecting(event) {
          log("Received 'ondisconnecting' call event.");
          if (event.call.state == "disconnecting") {
            window.wrappedJSObject.disconnecting_call_ok = true;
          };
        };

        window.wrappedJSObject.received_statechange = false;
        call_to_hangup.onstatechange = function onstatechange(event) {
        log("Received TelephonyCall 'onstatechange' event.");
          if (event.call.state == "disconnected") {
            window.wrappedJSObject.received_statechange = true;
          };
        };

        window.wrappedJSObject.disconnected_call_ok = false;
        call_to_hangup.ondisconnected = function ondisconnected(event) {
          log("Received 'ondisconnected' call event.");
          if (event.call.state == "disconnected") {
            window.wrappedJSObject.disconnected_call_ok = true;
          };
        };

        if (!remote_hangup) {
          call_to_hangup.hangUp();
        }

        marionetteScriptFinished(1);
        """, script_args=[call_type, remote_hangup, active_call_selected], special_powers=True)

        if remote_hangup == False:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error;"):
                self.fail("Received invalid value for active_call_selected")

            # should have received both events associated with a active call hangup
            wait = Wait(self.marionette, timeout=90, interval=0.5)
            try:
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.disconnecting_call_ok"))
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.disconnected_call_ok"))
            except:
                # failed to hangup
                self.fail("Failed to hangup call")
        else:
            self.instruct("Hangup the call from secondary phone and press 'OK'")
            # should have received only disconnected event associated with a active call hangup
            wait = Wait(self.marionette, timeout=90, interval=0.5)
            try:
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.disconnected_call_ok"))
            except:
                # failed to hangup
                self.fail("Failed to hangup call")

            # verify that the call disconnected from phone which is not the device under test
            disconnecting = self.marionette.execute_script("return window.wrappedJSObject.disconnecting_call_ok")
            self.assertFalse(disconnecting, "Telephony.ondisconnecting event found, but should not have been "
                            "since the call was terminated remotely")

        # should have received events associated with a state and calls change for with or without remote hangup
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_callschanged"))
        except:
            self.fail("Failed to receive either statechange or callschanged events")

        # remove the call from list
        if call_type == "Active":
            self.active_call_list.pop(active_call_selected)

    def hold_active_call(self, user_initiate_hold=True):
        self.marionette.execute_async_script("""
        let active = window.wrappedJSObject.active_call;
        var user_initiate_hold = arguments[0];

        window.wrappedJSObject.onholding_call_ok = false;
        active.onholding = function ondisconnecting(event) {
          log("Received 'onholding' call event.");
          if (event.call.state == "holding") {
            window.wrappedJSObject.onholding_call_ok = true;
          };
        };

        window.wrappedJSObject.received_statechange = false;
        active.onstatechange = function onstatechange(event) {
        log("Received TelephonyCall 'onstatechange' event.");
          if (event.call.state == "held") {
            window.wrappedJSObject.received_statechange = true;
          };
        };

        window.wrappedJSObject.onheld_call_ok = false;
        active.onheld = function ondisconnected(event) {
          log("Received 'onheld' call event.");
          if (event.call.state == "held") {
            window.wrappedJSObject.onheld_call_ok = true;
          };
        };
        if (user_initiate_hold) {
          active.hold();
        }
        marionetteScriptFinished(1);
        """, script_args=[user_initiate_hold], special_powers=True)

        if user_initiate_hold == True:
            # should have received both events associated with a call on hold
            wait = Wait(self.marionette, timeout=90, interval=0.5)
            try:
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.onholding_call_ok"))
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.onheld_call_ok"))
                wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
            except:
                # failed to hold
                self.fail("Failed to put call on hold initiated by user")

    def resume_held_call(self):
        self.marionette.execute_async_script("""
        let active = window.wrappedJSObject.active_call;

        window.wrappedJSObject.received_statechange = false;
        active.onstatechange = function onstatechange(event) {
        log("Received TelephonyCall 'onstatechange' event.");
          if (event.call.state == "resuming") {
            window.wrappedJSObject.received_statechange = true;
          };
        };

        window.wrappedJSObject.onresuming_call_ok = false;
        active.onresuming = function onresuming(event) {
          log("Received 'onresuming' call event.");
          if (event.call.state == "resuming") {
            window.wrappedJSObject.onresuming_call_ok = true;
          };
        };

        active.resume();
        marionetteScriptFinished(1);
        """, special_powers=True)

        # should have received event associated with a resumed call
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.onresuming_call_ok"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
        except:
            # failed to resume
            self.fail("Failed to resume the held call")

    def initiate_outgoing_call(self, destination):
        self.marionette.execute_script(self.returnable_calls)

        # use the webapi to initiate a call to the specified number
        self.marionette.execute_async_script("""
        var telephony = window.navigator.mozTelephony;
        var destination = arguments[0]

        telephony.dial(destination).then(out_call => {

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
                window.wrappedJSObject.returnable_outgoing_call = {
                    number: out_call.number,
                    state: out_call.state
                };
                window.wrappedJSObject.calls = telephony.calls;
              };
            };

            window.wrappedJSObject.received_callschanged = false;
            telephony.oncallschanged = function oncallschanged(event) {
              log("Received Telephony 'oncallschanged' event.");
              window.wrappedJSObject.received_callschanged = true;
            };

            window.wrappedJSObject.received_busy = false;
            out_call.onerror = function onerror(event) {
              log("Received TelephonyCall 'onerror' event.");
              if (event.call.error.name == "BusyError") {
                window.wrappedJSObject.received_busy = true;
              };
            };
        });

        marionetteScriptFinished(1);
        """, script_args=[destination], special_powers=True)

        # should have received all events associated with an outgoing call
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_dialing"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_statechange"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_alerting"))
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.received_callschanged"))
        except:
            # failed to initiate call; check if the destination phone's line was busy
            busy = self.marionette.execute_script("return window.wrappedJSObject.received_busy")
            self.assertFalse(busy, "Received busy signal; ensure target phone is available and try again")
            self.fail("Failed to initiate call; mozTelephony.dial is broken -or- there is no network signal. Try again")

        # verify outgoing call state to be 'alerting'
        self.outgoing_call = self.marionette.execute_script("return window.wrappedJSObject.returnable_outgoing_call")
        self.assertEqual(self.outgoing_call['state'], "alerting", "Call state should be 'alerting'")

    def user_guided_outgoing_call(self):
        # ask user to input destination phone number
        destination = self.prompt("Please enter a destination phone number (not the Firefox OS device) which will receive a test call")

        # can't check format as different around the world, just ensure not empty
        if destination is None:
            self.fail("Must enter a destination phone number")

        destination = destination.strip()
        self.assertGreater(len(destination), 3, "Destination phone number entered is incomplete")

        # ask user to confirm destination number
        self.confirm('Warning: A test call will be made from the Firefox OS device to "%s" is this number correct?' % destination)

        # make the call via webapi
        self.initiate_outgoing_call(destination)

    def disable_dialer(self):
        # disable system dialer agent so it doesn't steal the
        # incoming/outgoing calls away from the certest app
        cur_frame = self.marionette.get_active_frame()
        self.marionette.switch_to_frame()  # system app
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
        self.marionette.switch_to_frame()  # system app
        try:
            self.marionette.execute_async_script("""
            log("enabling system dialer agent");
            window.wrappedJSObject.dialerAgent.start();
            marionetteScriptFinished(1);
            """, special_powers=True)
        except:
            self.fail("failed to enable dialer agent")
        finally:
            self.marionette.switch_to_frame(cur_frame)

    def mute_call(self, enable=True):
        self.marionette.execute_script("""
        var enable = arguments[0];
        var telephony = window.navigator.mozTelephony;
        if (enable) {
          log("enabling mute");
          telephony.muted = true;
        } else {
          log("disabling mute");
          telephony.muted = false;
        }
        """, script_args=[enable], special_powers=True)

    def set_speaker(self, enable=True):
        self.marionette.execute_script("""
        var enable = arguments[0];
        var telephony = window.navigator.mozTelephony;
        if (enable) {
          log("enabling speaker");
          telephony.speakerEnabled = true;
        } else {
          log("disabling speaker");
          telephony.speakerEnabled = false;
        }
        """, script_args=[enable], special_powers=True)
