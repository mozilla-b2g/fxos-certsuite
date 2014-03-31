# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time


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

    def setup_onreceived_listener(self):
        self.marionette.execute_async_script("""
        // Bug 952875
        var mm = window.navigator.mozMobileMessage;
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

    def verify_sms_received(self):
        received = self.marionette.execute_script("return window.wrappedJSObject.receivedSms")
        self.assertTrue(received, "SMS message not received (mozMobileMessage.onreceived event not found)")

        # verify message body
        self.in_sms = self.marionette.execute_script("return window.wrappedJSObject.in_sms")
        self.assertTrue(len(self.in_sms['body']) > 0, "Received SMS has no message body (was text included in the sent SMS message?)")

    def remove_onreceived_listener(self):
        self.marionette.execute_script("window.navigator.mozMobileMessage.onreceived = null")

    def user_guided_incoming_sms(self):
        self.setup_onreceived_listener()
        self.instruct("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive")
        self.verify_sms_received()

        # verify body text
        self.confirm("Received SMS with text '%s'; does this text match what was sent to the Firefox OS phone?" %self.in_sms['body'])
        self.remove_onreceived_listener()

    def get_message(self, sms_id, expect_found=True, error_message="mozMobileMessage.getMessage returned unexpected value"):
        # get the sms for the given id and verify it was or wasn't found, as expected
        self.marionette.execute_async_script("""
        // Bug 952875
        var mm = window.navigator.mozMobileMessage;
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
        // Bug 952875
        var mm = window.navigator.mozMobileMessage;
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

    def setup_onsent_listener(self):
        # setup listener for sent sms
        self.marionette.execute_async_script("""
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        window.wrappedJSObject.gotSmsOnsent = false;
        window.wrappedJSObject.sentSms = false;
        window.navigator.mozMobileMessage.onsent = function onsent(event) {
            log("Received 'onsent' mozMobileMessage event");
            window.wrappedJSObject.gotSmsOnsent = true;
            window.wrappedJSObject.out_sms = event.message;
            if (window.wrappedJSObject.gotSmsOnsent && window.wrappedJSObject.gotReqOnsuccess) { window.wrappedJSObject.sentSms = true; }
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

    def send_message(self, destination, body):
        # use the webapi to send an sms to the specified number, with specified text
        self.marionette.execute_async_script("""
        let requestRet = window.navigator.mozMobileMessage.send(arguments[0], arguments[1]);
        ok(requestRet, "smsrequest obj returned");

        requestRet.onsuccess = function(event) {
            log("Received 'onsuccess' smsrequest event.");
            window.wrappedJSObject.gotReqOnsuccess = true;
            if(event.target.result){
                if (window.wrappedJSObject.gotSmsOnsent && window.wrappedJSObject.gotReqOnsuccess) { window.wrappedJSObject.sentSms = true; }
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
        # verify message was sent
        sent = self.marionette.execute_script("return window.wrappedJSObject.sentSms")
        self.assertTrue(sent, "SMS should have been sent (expected mozMobileMessage.onsent event and send request.onsuccess)")

        # get message event
        self.out_sms = self.marionette.execute_script("return window.wrappedJSObject.out_sms")

    def remove_onsent_listener(self):
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsent = null")

    def user_guided_outgoing_sms(self):
        # ask user to input destination phone number
        destination = self.prompt("Please enter a destination phone number where a test SMS will be sent (not the Firefox OS device)")
        destination = str(destination)

        # can't check format as different around the world, just ensure not empty
        self.assertTrue(len(destination) > 1, "Destination phone number must be entered")
        # ask user to confirm destination number
        self.confirm("You entered destination number '%s', is this correct?" %destination)
        self.out_destination = destination

        # ask user to input sms body text
        body = self.prompt("Please enter some text to be sent in the SMS message")
        self.assertTrue(len(body) > 0 & len(body) < 161,
                         "SMS message text entered must be between 1 and 160 characters long")

        # setup listener and send the sms via webapi
        self.setup_onsent_listener()
        self.send_message(destination, body)

        # user verification that it was received on target, before continue
        self.confirm("SMS has been sent to '%s'. Was it received on the target phone?" %destination)
        self.verify_message_sent()

        # verify sms body
        self.assertTrue(len(self.out_sms['body']) > 0, "Sent SMS event message has no message body")
        self.confirm("Sent SMS with text '%s'; does this text match what was received on the target phone?" %self.out_sms['body'])
        self.remove_onsent_listener()
