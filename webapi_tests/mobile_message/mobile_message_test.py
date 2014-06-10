# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from marionette.wait import Wait


class MobileMessageTestCommon(object):
    def __init__(self):
        self.in_msg = None
        self.out_msg = None
        self.out_destination = None
        self.marionette.execute_async_script("""
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        marionetteScriptFinished(1);
        """, special_powers=True)

    def setup_receiving_listener(self):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        ok(mm instanceof MozMobileMessageManager, "Failed to create instance of MozMobileMessageManager")
        // Bug 952875
        mm.getThreads();

        window.wrappedJSObject.received_msg = false;
        mm.onreceived = function onreceived(event) {
            console.log("Received 'onreceived' mozMobileMessage event");
            window.wrappedJSObject.received_msg = true;
            window.wrappedJSObject.in_msg = event.message;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def remove_receiving_listener(self):
        self.marionette.execute_script("window.navigator.mozMobileMessage.onreceived = null")

    def verify_sms_received(self):
        received = self.marionette.execute_script("return window.wrappedJSObject.received_msg")
        self.assertTrue(received, "SMS message not received (mozMobileMessage.onreceived event not found)")
        # verify message body
        self.in_msg = self.marionette.execute_script("return window.wrappedJSObject.in_msg")
        self.assertTrue(len(self.in_msg['body']) > 0, "Received SMS has no message body (was text included in the sent SMS message?)")

    def user_guided_incoming_sms(self):
        self.setup_receiving_listener()
        self.confirm("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive. \
                        Did the SMS arrive?")
        self.verify_sms_received()
        # verify body text
        self.confirm('Received SMS with text "%s" does this text match what was sent to the Firefox OS phone?' %self.in_msg['body'])
        self.remove_receiving_listener()

    def get_message(self, msg_id, expect_found=True, error_message="mozMobileMessage.getMessage returned unexpected value"):
        # get the sms for the given id and verify it was or wasn't found, as expected
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        ok(mm instanceof MozMobileMessageManager, "Failed to create instance of MozMobileMessageManager")
        // Bug 952875
        mm.getThreads();

        let requestRet = mm.getMessage(arguments[0]);
        requestRet.onsuccess = function(event) {
            if(event.target.result){
                window.wrappedJSObject.sms_found = true;
                ok(event.target.result, "smsrequest event.target.result");
                window.wrappedJSObject.event_sms = event.target.result;
            } else {
                window.wrappedJSObject.sms_found = false;
            }
        };

        requestRet.onerror = function(event) {
            window.wrappedJSObject.sms_found = false;
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_id], special_powers=True)

        time.sleep(2)

        found = self.marionette.execute_script("return window.wrappedJSObject.sms_found")
        self.assertEqual(found, expect_found, error_message)

    def delete_message(self, msg_id):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
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
            window.wrappedJSObject.msg_deleted = false;
        };
        marionetteScriptFinished(1);
        """, script_args=[msg_id], special_powers=True)

        time.sleep(2)

        deleted = self.marionette.execute_script("return window.wrappedJSObject.msg_deleted")
        self.assertTrue(deleted, "MozMobileMessage.delete returned unexpected error")

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
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsending = null")
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsent = null")
        self.marionette.execute_script("window.navigator.mozMobileMessage.onfailed = null")

    def send_sms(self, destination, body):
        # use the webapi to send an sms to the specified number, with specified text
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

    def verify_message_sent(self):
        # wait for sent message; possibly could fail because of insufficient network signal
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: self.marionette.execute_script("return window.wrappedJSObject.rcvd_req_success"))
        except:
            # msg wasn't sent; either the api is broken or mobile network signal is insufficient
            self.fail("Failed to send SMS or MMS; mozMobileMessage.send is broken -or- \
                        perhaps there is no mobile network signal. Please try again")

        # verify the remaining sms send events
        got_failed = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_failed")
        self.assertFalse(got_failed, "Failed to send message; received mozMobileMessage.onfailed event")
        got_sending = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_sending")
        self.assertTrue(got_sending, "Failed to send message; mozMobileMessage.onsending event not received")
        got_sent = self.marionette.execute_script("return window.wrappedJSObject.rcvd_on_sent")
        self.assertTrue(got_sent, "Failed to send message; mozMobileMessage.onsent event not received")

        # get message event
        self.out_msg = self.marionette.execute_script("return window.wrappedJSObject.out_msg")

    def user_guided_outgoing_sms(self):
        # ask user to input destination phone number
        destination = self.prompt("Please enter a destination phone number where a test SMS will be sent (not the Firefox OS device)")

        # can't check format as different around the world, just ensure not empty
        if destination is None:
            self.fail("Must enter a destination phone number")

        destination = destination.strip()
        self.assertTrue(len(destination) > 1, "Destination phone number must be entered")

        # ask user to confirm destination number
        self.confirm('Warning: An SMS will be sent to "%s" is this number correct?' %destination)
        self.out_destination = destination

        # ask user to input sms body text
        body = self.prompt("Please enter some text to be sent in the SMS message")
        if body is None:
            self.fail("Must enter some text for the SMS message")

        body = body.strip()
        self.assertTrue(len(body) > 0 & len(body) < 161,
                        "SMS message text entered must be between 1 and 160 characters in length")

        # setup listeners and send the sms via webapi
        self.setup_sending_listeners()
        self.send_sms(destination, body)

        # verify sms was sent from Firefox OS device before asking user to check target
        self.verify_message_sent()

        # user verification that it was received on target, before continue
        self.confirm('SMS sent to "%s". Please wait a few minutes. Was it received on the target phone?' %destination)

        # verify sms body
        self.assertTrue(len(self.out_msg['body']) > 0, "Sent SMS event message has no message body")
        self.confirm('Sent SMS with text "%s" does this text match what was received on the target phone?' %self.out_msg['body'])
        self.remove_sending_listeners()
