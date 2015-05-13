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

    def assert_msg_received(self):
        received = self.marionette.execute_script("return window.wrappedJSObject.received_msg")
        self.assertTrue(received, "Message not received (mozMobileMessage.onreceived event not found)")
        self.in_msg = self.marionette.execute_script("return window.wrappedJSObject.in_msg")
        self.assertIsNotNone(self.in_msg, "Incoming message object doesn't exist")

    def user_guided_incoming_msg(self, msg_type="SMS"):
        self.setup_receiving_listener()
        try:
            self.confirm("From a different phone, send an %s to the Firefox OS device and wait for it to arrive. "
                         "Did the %s message arrive?" % (msg_type, msg_type))
            self.assert_msg_received()
        finally:
            self.remove_receiving_listener()

    def get_message(self, msg_id):
        """ Get the sms or mms for the given id. Return the message, or none if it doesn't exist"""
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

        requestRet.onerror = function() {
            window.wrappedJSObject.rcvd_event = true;
            log("Get message returned error: %s" % requestRet.error.name);
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
            if (event.target.result) {
                window.wrappedJSObject.msg_deleted = true;
            } else {
                window.wrappedJSObject.msg_deleted = false;
            }
        };

        requestRet.onerror = function() {
            window.wrappedJSObject.rcvd_error = true;
            log("Delete message returned error: %s" % requestRet.error.name);
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

    def send_msg(self, destination, body, msg_type="SMS"):
        """ Use the webapi to send an sms or mms to the specified number, with specified text """
        self.assertIn(msg_type, ["SMS", "MMS"], "Called send_msg with invalid message type")

        self.marionette.execute_async_script("""
        var msg_type = arguments[0];
        var mm = window.navigator.mozMobileMessage;
        var requestRet = null;
        // Bug 952875
        mm.getThreads();

        if (msg_type == "SMS") {
            requestRet = mm.send(arguments[1], arguments[2]);
        } else {
            let test_subject = arguments[2];
            let test_receiver = arguments[1];
            let mms_params = { subject: test_subject,
                               receivers: test_receiver,
                               attachments: [] };
            requestRet = mm.sendMMS(mms_params);
        }

        requestRet.onsuccess = function(event) {
            log("Received 'onsuccess' event.");
            if (event.target.result) {
                window.wrappedJSObject.rcvd_req_success = true;
            } else {
                log("request returned false for manager.send");
            }
        };

        requestRet.onerror = function() {
            log("Failed to send message, received error: %s" % requestRet.error.name);
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_type, destination, body], special_powers=True)
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
            self.fail("Failed to send message. The API is broken -or- "
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

    def ask_user_for_number(self, msg_type="SMS"):
        """ Prompt user to enter a phone number; check formatting and give three attempts """
        for _ in range(3):
            destination = self.prompt("Please enter a destination phone number where a test %s will be sent (not the "
                                      "Firefox OS device). Digits only with no spaces, brackets, or hyphens." % msg_type)
            # can't check format as different around the world, just ensure not empty and is digits
            if destination is None or len(destination.strip()) == 0 or destination.isdigit() is False:
                continue
            else:
                return destination.strip()
        self.fail("Failed to enter a valid destination phone number")

    def user_guided_outgoing_msg(self, msg_type="SMS"):
        # ask user to input destination phone number
        destination = self.ask_user_for_number(msg_type)

        # ask user to confirm destination number
        self.confirm('Warning: An %s will be sent to "%s" is this number correct?' % (msg_type, destination))
        self.out_destination = destination

        # ask user to input body text
        body = self.prompt("Please enter some text to be sent in the %s message" % msg_type)
        if body is None:
            self.fail("Must enter some text for the message")

        body = body.strip()
        self.assertTrue(len(body) > 0 and len(body) < 161, "Message text entered must be between 1 and 160 chars")

        # setup listeners and send the msg via webapi
        self.setup_sending_listeners()
        try:
            self.send_msg(destination, body)

            # verify message was sent from Firefox OS device before asking user to check target
            self.assert_message_sent()
            # user verification that it was received on target, before continue
            self.confirm('%s sent to "%s". Please wait a few minutes. Was it '
                         'received on the target phone?' % (msg_type, destination))
            # verify sms body
            self.assertTrue(len(self.out_msg['body']) > 0, "Sent %s event message has no message body" % msg_type)
            self.confirm('Sent %s with text "%s" does this text match what was received on the target phone?' % (msg_type, self.out_msg['body']))
        finally:
            self.remove_sending_listeners()

    def mark_message_status(self, msg_id, is_read=False):
        self.marionette.execute_async_script("""
        var msg_id = arguments[0];
        var is_read = arguments[1];
        var requestRet = null;

        var mm = window.navigator.mozMobileMessage;
        // Bug 952875
        mm.getThreads();

        requestRet = mm.markMessageRead(msg_id, is_read);
        window.wrappedJSObject.rcvd_req_success_read = false;
        window.wrappedJSObject.rcvd_req_success_unread = false;
        requestRet.onsuccess = function(event) {
            log("Received 'onsuccess' event.");
            if (event.target.result) {
                window.wrappedJSObject.rcvd_req_success_read = true;
            } else {
                window.wrappedJSObject.rcvd_req_success_unread = true;
                log("request returned false for manager.markMessageRead");
            }
        }

        requestRet.onerror = function() {
            log("Failed to mark message read status, received error: %s" % requestRet.error.name);
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_id, is_read], special_powers=True)

        wait = Wait(self.marionette, timeout=15, interval=0.5)
        try:
            if is_read is True:
                wait.until(lambda m: self.marionette.execute_script("return window.wrappedJSObject.rcvd_req_success_read"))
            else:
                wait.until(lambda m: self.marionette.execute_script("return window.wrappedJSObject.rcvd_req_success_unread"))
        except errors.TimeoutException:
            # msg read status wasn't marked
            self.fail("Failed to update the read status of message.")
