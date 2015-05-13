# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from marionette.wait import Wait


class FMRadioTestCommon(object):
    def __init__(self):
        # ensure radio is off on test startup
        if self.is_radio_enabled():
            self.turn_radio_off()

    def is_antenna_available(self):
        return self.marionette.execute_script("return window.navigator.mozFMRadio.antennaAvailable")

    def user_connect_antenna(self):
        self.setup_antenna_change_listener()
        self.instruct("Insert the headset into the Firefox OS device, then click 'OK'")
        self.wait_for_antenna_change()
        self.assertTrue(self.is_antenna_available(), "Expected antenna/headset to be connected")
        self.remove_antenna_change_listener()

    def user_detach_antenna(self):
        self.setup_antenna_change_listener()
        self.instruct("Remove the headset from the device, then click 'OK'")
        self.wait_for_antenna_change()
        self.assertFalse(self.is_antenna_available(), "Expected antenna/headset to be disconnected")
        self.remove_antenna_change_listener()

    def is_radio_enabled(self):
        return self.marionette.execute_script("return window.navigator.mozFMRadio.enabled")

    def setup_antenna_change_listener(self):
        # setup event handler for antenna insert/remove
        self.marionette.execute_async_script("""
        var fm = window.navigator.mozFMRadio;
        window.wrappedJSObject.antenna_change = false;
        fm.onantennaavailablechange = function() {
            window.wrappedJSObject.antenna_change = true;
        };
        marionetteScriptFinished(1);
        """)

    def remove_antenna_change_listener(self):
        self.marionette.execute_script("window.navigator.mozFMRadio.onantennaavailablechange = null")

    def wait_for_antenna_change(self):
        # wait for radio to change state
        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.antenna_change"))
        except:
            self.fail("Failed to receive mozFMRadio.onantennaavailablechange event")

    def setup_radio_change_listeners(self):
        # setup event handlers for radio turning on/off
        self.marionette.execute_async_script("""
        var fm = window.navigator.mozFMRadio;
        window.wrappedJSObject.rcvd_radio_on = false;
        fm.onenabled = function() {
            window.wrappedJSObject.rcvd_radio_on = true;
        };
        window.wrappedJSObject.rcvd_radio_off = false;
        fm.ondisabled = function() {
            window.wrappedJSObject.rcvd_radio_off = true;
        };
        marionetteScriptFinished(1);
        """)

    def remove_radio_change_listeners(self):
        self.marionette.execute_script("""
        window.navigator.mozFMRadio.onenabled = null;
        window.navigator.mozFMRadio.ondisabled = null;
        """)

    def turn_radio_on(self):
        self.change_radio_state(turning_on=True)

    def turn_radio_off(self):
        self.change_radio_state(turning_on=False)

    def change_radio_state(self, turning_on):
        # turn on or off radio and verify request
        self.marionette.execute_async_script("""
        var turning_on = arguments[0];
        var fm = window.navigator.mozFMRadio;
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        // turn on or off accordingly
        if (turning_on) {
            var request = fm.enable(99.9);
        } else {
            var request = fm.disable();
        };
        // verify request
        request.onsuccess = function() {
            window.wrappedJSObject.rcvd_success = true;
        };
        request.onerror = function() {
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[turning_on])

        # wait for radio to change state
        wait = Wait(self.marionette, timeout=10, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                if turning_on:
                    self.fail("MozFMRadio.enable returned error")
                else:
                    self.fail("MozFMRadio.disable returned error")
            else:
                if turning_on:
                    self.fail("Failed to turn on the fm radio")
                else:
                    self.fail("Failed to turn off the fm radio")

    def rcvd_radio_on(self):
        return self.marionette.execute_script("return window.wrappedJSObject.rcvd_radio_on")

    def rcvd_radio_off(self):
        return self.marionette.execute_script("return window.wrappedJSObject.rcvd_radio_off")
