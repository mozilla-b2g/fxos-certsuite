# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from marionette.wait import Wait
from marionette import errors


class MobileMessageTestCommon(object):
    def __init__(self):
        self.in_msg = None
        self.out_msg = None
        self.out_destination = None
        self.marionette.execute_script("""
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        """, special_powers=True)

    def setup_receiving_listener(self):
        self.marionette.execute_script("""
        var mm = window.navigator.mozMobileMessage;
        // Bug 952875
        mm.getThreads();

        window.wrappedJSObject.received_msg = false;
        mm.onreceived = function onreceived(event) {
            console.log("Received 'onreceived' mozMobileMessage event");
            window.wrappedJSObject.received_msg = true;
            window.wrappedJSObject.in_msg = event.message;
        };
        """, special_powers=True)

    def remove_receiving_listener(self):
        self.marionette.execute_script("""
        if (window.navigator.mozMobileMessage !== undefined) {
            window.navigator.mozMobileMessage.onreceived = null;
        };
        """)

    def assert_sms_received(self):
        received = self.marionette.execute_script("return window.wrappedJSObject.received_msg")
        self.assertTrue(received, "SMS message not received (mozMobileMessage.onreceived event not found)")
        # verify message body
        self.in_msg = self.marionette.execute_script("return window.wrappedJSObject.in_msg")
        self.assertTrue(len(self.in_msg['body']) > 0, "Received SMS has no message body (was text included in the sent SMS message?)")

    def user_guided_incoming_sms(self):
        self.setup_receiving_listener()
        try:
            self.confirm("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive. "
                         "Did the SMS arrive?")
            self.assert_sms_received()
        finally:
            self.remove_receiving_listener()

    def get_message(self, msg_id):
        """ Get the sms for the given id. Return the sms, or none if it doesn't exist"""
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        window.wrappedJSObject.event_sms = null;
        window.wrappedJSObject.rcvd_event = false;

        // Bug 952875
        mm.getThreads();

        let requestRet = mm.getMessage(arguments[0]);
        requestRet.onsuccess = function(event) {
            if(event.target.result){
                window.wrappedJSObject.rcvd_event = true;
                window.wrappedJSObject.event_sms = event.target.result;
            }
        };

        requestRet.onerror = function(event) {
            window.wrappedJSObject.rcvd_event = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_id], special_powers=True)

        # wait for a result
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_event"))
        except errors.TimeoutException:
            self.fail("mozMobileMessage.getMessage() failed")

        # return the message if it was found, otherwise none
        return self.marionette.execute_script("return window.wrappedJSObject.event_sms")

    def delete_message(self, msg_id):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        window.wrappedJSObject.msg_deleted = false;
        window.wrappedJSObject.rcvd_error = false;
        // Bug 952875
        mm.getThreads();

        let requestRet = mm.delete(arguments[0]);
        requestRet.onsuccess = function(event) {
            if(event.target.result){
                window.wrappedJSObject.msg_deleted = true;
            } else {
                window.wrappedJSObject.msg_deleted = false;
            }
        };

        requestRet.onerror = function(event) {
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_id], special_powers=True)

        # wait for request.onsuccess
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda m: m.execute_script("return window.wrappedJSObject.msg_deleted"))
        except errors.TimeoutException:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error;"):
                self.fail("Error received while deleting message")
            else:
                self.fail("Failed to delete message")

    def setup_sending_listeners(self):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        // Bug 952875
        mm.getThreads();

        window.wrappedJSObject.rcvd_on_sending = false;
        mm.onsending = function onsending(event) {
            log("Received 'onsending' mozMobileMessage event");
            window.wrappedJSObject.rcvd_on_sending = true;
        };

        window.wrappedJSObject.rcvd_on_sent = false;
        mm.onsent = function onsent(event) {
            log("Received 'onsent' mozMobileMessage event");
            window.wrappedJSObject.rcvd_on_sent = true;
            window.wrappedJSObject.out_msg = event.message;
        };

        window.wrappedJSObject.rcvd_on_failed = false;
        mm.onfailed = function onsent(event) {
            log("Received 'onfailed' mozMobileMessage event");
            window.wrappedJSObject.rcvd_on_failed = true;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def remove_sending_listeners(self):
        self.marionette.execute_script("""
        if (window.navigator.mozMobileMessage !== undefined) {
            window.navigator.mozMobileMessage.onsending = null;
            window.navigator.mozMobileMessage.onsent = null;
            window.navigator.mozMobileMessage.onfailed = null;
        };
        """)

    def send_sms(self, destination, body):
        """ Use the webapi to send an sms to the specified number, with specified text """
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        // Bug 952875
        mm.getThreads();

        let requestRet = mm.send(arguments[0], arguments[1]);
        ok(requestRet, "smsrequest obj returned");
        requestRet.onsuccess = function(event) {
            log("Received 'onsuccess' smsrequest event.");
            if(event.target.result){
                window.wrappedJSObject.rcvd_req_success = true;
            } else {
                log("smsrequest returned false for manager.send");
                ok(false,"SMS send failed");
                cleanUp();
            }
        };

        requestRet.onerror = function(event) {
            log("Received 'onerror' smsrequest event.");
            cleanUp();
        };
        marionetteScriptFinished(1);
        """, script_args=[destination, body], special_powers=True)

        time.sleep(5)

    def assert_message_sent(self):
        """
        After sending an SMS/MMS, call this method to wait for the message to be sent.
        Verify that a mobile message was sent by checking if the expected events were triggered.
        Once verified, set the out_msg attribute to point to the message that has been sent.
        """
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda m: self.marionette.execute_script("return window.wrappedJSObject.rcvd_req_success"))
        except errors.TimeoutException:
            # msg wasn't sent; either the api is broken or mobile network signal is insufficient
            self.fail("Failed to send SMS or MMS; mozMobileMessage.send is broken -or- "
                      "perhaps there is no mobile network signal. Please try again")

        # verify the remaining msg send events
        rcvd_failed = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_failed")
        self.assertFalse(rcvd_failed, "Failed to send message; received mozMobileMessage.onfailed event")
        rcvd_sending = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_sending")
        self.assertTrue(rcvd_sending, "Failed to send message; mozMobileMessage.onsending event not received")
        rcvd_sent = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_sent")
        self.assertTrue(rcvd_sent, "Failed to send message; mozMobileMessage.onsent event not received")

        # get message event
        self.out_msg = self.marionette.execute_script("return window.wrappedJSObject.out_msg")

    def ask_user_for_number(self):
        """ Prompt user to enter a phone number; check formatting and give three attempts """
        for _ in range(3):
            destination = self.prompt("Please enter a destination phone number where a test SMS will be sent (not the "
                                      "Firefox OS device). Digits only with no spaces, brackets, or hyphens.")
            # can't check format as different around the world, just ensure not empty and is digits
            if destination is None or len(destination.strip()) == 0 or destination.isdigit() is False:
                continue
            else:
                return destination.strip()
        self.fail("Failed to enter a valid destination phone number")

    def user_guided_outgoing_sms(self):
        # ask user to input destination phone number
        destination = self.ask_user_for_number()

        # ask user to confirm destination number
        self.confirm('Warning: An SMS will be sent to "%s" is this number correct?' % destination)
        self.out_destination = destination

        # ask user to input sms body text
        body = self.prompt("Please enter some text to be sent in the SMS message")
        if body is None:
            self.fail("Must enter some text for the SMS message")

        body = body.strip()
        self.assertTrue(len(body) > 0 and len(body) < 161, "SMS message text entered must be between 1 and 160 chars")

        # setup listeners and send the sms via webapi
        self.setup_sending_listeners()
        try:
            self.send_sms(destination, body)
            # verify sms was sent from Firefox OS device before asking user to check target
            self.assert_message_sent()
            # user verification that it was received on target, before continue
            self.confirm('SMS sent to "%s". Please wait a few minutes. Was it '
                         'received on the target phone?' % destination)
            # verify sms body
            self.assertTrue(len(self.out_msg['body']) > 0, "Sent SMS event message has no message body")
            self.confirm('Sent SMS with text "%s" does this text match what was received on the target phone?' % self.out_msg['body'])
        finally:
            self.remove_sending_listeners()
