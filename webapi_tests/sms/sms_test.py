# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from marionette.wait import Wait


class SmsTestCommon(object):
    def __init__(self):
        self.in_sms = None
        self.out_sms = None
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

        window.wrappedJSObject.receivedSms = false;
        mm.onreceived = function onreceived(event) {
            console.log("Received 'onreceived' mozMobileMessage event");
            window.wrappedJSObject.receivedSms = true;
            window.wrappedJSObject.in_sms = event.message;
            ok(event.message instanceof MozSmsMessage, ",onreceived event.message is instanceof MozSmsMessage");
            ok(event.message.threadId, "onreceived event thread id exists")
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def remove_receiving_listener(self):
        self.marionette.execute_script("window.navigator.mozMobileMessage.onreceived = null")

    def verify_sms_received(self):
        received = self.marionette.execute_script("return window.wrappedJSObject.receivedSms")
        self.assertTrue(received, "SMS message not received (mozMobileMessage.onreceived event not found)")
        # verify message body
        self.in_sms = self.marionette.execute_script("return window.wrappedJSObject.in_sms")
        self.assertTrue(len(self.in_sms['body']) > 0, "Received SMS has no message body (was text included in the sent SMS message?)")

    def user_guided_incoming_sms(self):
        self.setup_receiving_listener()
        self.instruct("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive. \
                        Did the SMS arrive?")
        self.verify_sms_received()

        # verify body text
        self.confirm('Received SMS with text "%s" does this text match what was sent to the Firefox OS phone?' %self.in_sms['body'])
        self.remove_receiving_listener()

    def get_message(self, sms_id, expect_found=True, error_message="mozMobileMessage.getMessage returned unexpected value"):
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
        """, script_args=[sms_id], special_powers=True)

        time.sleep(2)

        found = self.marionette.execute_script("return window.wrappedJSObject.sms_found")
        self.assertEqual(found, expect_found, error_message)

    def delete_message(self, sms_id):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        ok(mm instanceof MozMobileMessageManager, "Failed to create instance of MozMobileMessageManager")
        // Bug 952875
        mm.getThreads();

        let requestRet = mm.delete(arguments[0]);
        requestRet.onsuccess = function(event) {
            if(event.target.result){
                window.wrappedJSObject.sms_deleted = true;
            } else {
                window.wrappedJSObject.sms_deleted = false;
            }
        };

        requestRet.onerror = function(event) {
            window.wrappedJSObject.sms_deleted = false;
        };
        marionetteScriptFinished(1);
        """, script_args=[sms_id], special_powers=True)

        time.sleep(2)

        deleted = self.marionette.execute_script("return window.wrappedJSObject.sms_deleted")
        self.assertTrue(deleted, "MozMobileMessage.delete returned unexpected error and failed to delete the SMS")

    def setup_sending_listeners(self):
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        ok(mm instanceof MozMobileMessageManager, "Failed to create instance of MozMobileMessageManager")
        // Bug 952875
        mm.getThreads();

        window.wrappedJSObject.gotSmsOnsending = false;
        mm.onsending = function onsending(event) {
            log("Received 'onsending' mozMobileMessage event");
            window.wrappedJSObject.gotSmsOnsending = true;
            window.wrappedJSObject.sending_sms = event.message;
        };

        window.wrappedJSObject.gotSmsOnsent = false;
        mm.onsent = function onsent(event) {
            log("Received 'onsent' mozMobileMessage event");
            window.wrappedJSObject.gotSmsOnsent = true;
            window.wrappedJSObject.out_sms = event.message;
        };

        window.wrappedJSObject.gotSmsOnfailed = false;
        mm.onfailed = function onsent(event) {
            log("Received 'onfailed' mozMobileMessage event");
            window.wrappedJSObject.gotSmsOnfailed = true;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def remove_sending_listeners(self):
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsending = null")
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsent = null")
        self.marionette.execute_script("window.navigator.mozMobileMessage.onfailed = null")

    def send_message(self, destination, body):
        # use the webapi to send an sms to the specified number, with specified text
        self.marionette.execute_async_script("""
        var mm = window.navigator.mozMobileMessage;
        ok(mm instanceof MozMobileMessageManager, "Failed to create instance of MozMobileMessageManager")
        // Bug 952875
        mm.getThreads();

        let requestRet = mm.send(arguments[0], arguments[1]);
        ok(requestRet, "smsrequest obj returned");
        requestRet.onsuccess = function(event) {
            log("Received 'onsuccess' smsrequest event.");
            if(event.target.result){
                window.wrappedJSObject.gotReqOnsuccess = true;
            } else {
                log("smsrequest returned false for manager.send");
                ok(false,"SMS send failed");
                cleanUp();
            }
        };

        requestRet.onerror = function(event) {
            log("Received 'onerror' smsrequest event.");
            ok(event.target.error, "domerror obj");
            ok(false, "manager.send request returned unexpected error: "
                + event.target.error.name );
            cleanUp();
        };
        marionetteScriptFinished(1);
        """, script_args=[destination, body], special_powers=True)

        time.sleep(5)

    def verify_message_sent(self):
        # wait for sent message; possibly could fail because of insufficient network signal
        wait = Wait(self.marionette, timeout=90, interval=0.5)
        try:
            wait.until(lambda x: self.marionette.execute_script("return window.wrappedJSObject.gotReqOnsuccess"))
        except:
            # sms wasn't sent; either the api is broken or mobile network signal is insufficient
            self.fail("Failed to send SMS; mozMobileMessage.send is broken -or- \
                        perhaps there is no mobile network signal. Please try again")

        # verify the remaining sms send events
        got_failed = self.marionette.execute_script("return window.wrappedJSObject.gotSmsOnfailed")
        self.assertFalse(got_failed, "SMS should not have failed sending (received mozMobileMessage.onfailed event")
        got_sending = self.marionette.execute_script("return window.wrappedJSObject.gotSmsOnsending")
        self.assertTrue(got_sending, "SMS should have been sending (expected mozMobileMessage.onsending event")
        got_sent = self.marionette.execute_script("return window.wrappedJSObject.gotSmsOnsent")
        self.assertTrue(got_sent, "SMS should have been sent (expected mozMobileMessage.onsent event)")

        # get message event
        self.out_sms = self.marionette.execute_script("return window.wrappedJSObject.out_sms")

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
        self.send_message(destination, body)

        # verify sms was sent from Firefox OS device before asking user to check target
        self.verify_message_sent()

        # user verification that it was received on target, before continue
        self.confirm('SMS sent to "%s". Please wait a few minutes. Was it received on the target phone?' %destination)

        # verify sms body
        self.assertTrue(len(self.out_sms['body']) > 0, "Sent SMS event message has no message body")
        self.confirm('Sent SMS with text "%s" does this text match what was received on the target phone?' %self.out_sms['body'])
        self.remove_sending_listeners()
