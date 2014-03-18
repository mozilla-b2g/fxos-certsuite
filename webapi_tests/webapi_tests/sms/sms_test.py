import time

class SmsTestCommon(object):
    def __init__(self):
        self.in_sms = None
        self.marionette.execute_async_script("""        
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        marionetteScriptFinished(1);
        """, special_powers=True)

    def user_guided_incoming_sms(self):
        # setup listener for incoming SMS
        self.marionette.execute_async_script("""
        // Bug 952875
        var mm = window.navigator.mozMobileMessage;
        mm.getThreads();

        window.wrappedJSObject.receivedSms = false;
        mm.onreceived = function onreceived(event) {
            console.log("Received 'onreceived' mozMobileMessage event");
            window.wrappedJSObject.receivedSms = true;
            window.wrappedJSObject.in_sms = event.message;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

        self.instruct("From a different phone, send an SMS text message to the Firefox OS device, and wait for it to arrive")

        # verify message was received
        received = self.marionette.execute_script("return window.wrappedJSObject.receivedSms")
        self.assertTrue(received, "SMS message not received (mozMobileMessage.onreceived event not found)")

        # verify message body
        self.in_sms = self.marionette.execute_script("return window.wrappedJSObject.in_sms")
        print "Received SMS (id: %s)" %self.in_sms['id']
        self.assertTrue(len(self.in_sms['body']) > 0, "Received SMS has no message body (was text included in the sent SMS message?)")
        self.confirm("Received SMS with text '%s'; does this text match what was sent to the Firefox OS phone?" %self.in_sms['body'])

        # don't need listener
        self.marionette.execute_script("window.navigator.mozMobileMessage.onreceived = null")

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

    def send_message(self, destination, body):
        # use the webapi to send a text to the destination number
        # setup listener for sent SMS
        self.marionette.execute_async_script("""
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        window.wrappedJSObject.gotSmsOnsent = false;
        window.wrappedJSObject.sentSms = false;
        window.navigator.mozMobileMessage.onsent = function onsent(event) {
            log("Received 'onsent' mozMobileMessage event");
            window.wrappedJSObject.gotSmsOnsent = true;
            window.wrappedJSObject.out_sms = event.message;
            if (gotSmsOnsent && gotReqOnsuccess) { window.wrappedJSObject.sentSms = true; }
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

        # send the SMS
        self.marionette.execute_async_script("""
        let requestRet = window.navigator.mozMobileMessage.send(arguments[0], arguments[1]);
        ok(requestRet, "smsrequest obj returned");

        requestRet.onsuccess = function(event) {
          log("Received 'onsuccess' smsrequest event.");
          gotReqOnsuccess = true;
          if(event.target.result){
            if (gotSmsOnsent && gotReqOnsuccess) { window.wrappedJSObject.sentSms = true; }
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

        # verify message was sent
        sent = self.marionette.execute_script("return window.wrappedJSObject.sentSms")
        self.assertTrue(sent, "SMS message not sent (mozMobileMessage.onsent event or send request.onsuccess not found)")

        # verify message body
        self.out_sms = self.marionette.execute_script("return window.wrappedJSObject.out_sms")
        print "Sent SMS (id: %s)" %self.out_sms['id']

        # user verification that it was received on target
        self.confirm("SMS has been sent from the Firefox OS phone to %s. Was it received on the target phone?" %destination)

        self.assertTrue(len(self.out_sms['body']) > 0, "Sent SMS event message has no message body")
        self.confirm("Sent SMS with text '%s'; does this text match what was received on the target phone?" %self.out_sms['body'])

        # don't need listener anymore        
        self.marionette.execute_script("window.navigator.mozMobileMessage.onsent = null")
