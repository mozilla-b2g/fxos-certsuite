class SmsTestCommon(object):
    def __init__(self):
        self.in_sms = None

    def user_guided_incoming_sms(self):
        # setup listener for incoming SMS
        self.marionette.execute_async_script("""
        SpecialPowers.setBoolPref("dom.sms.enabled", true);
        SpecialPowers.addPermission("sms", true, document);
        window.wrappedJSObject.receivedSms = false;
        window.navigator.mozMobileMessage.onreceived = function onreceived(event) {
            log("Received 'onreceived' mozMobileMessage event");
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
        self.instruct("Received SMS with text '%s'; does this text match what was sent to the Firefox OS phone?" %self.in_sms['body'])

    def get_message(self, sms_id, expect_found=True, error_message="mozMobileMessage.getMessage returned unexpected value"):
        # get the sms for the given id and verify it was or wasn't found, as expected
        print "Getting SMS (id: %s)" %sms_id
        self.marionette.execute_async_script("""
        let requestRet = window.navigator.mozMobileMessage.getMessage(arguments[0]);

        requestRet.onsuccess = function(event) {
          if(event.target.result){
            window.wrappedJSObject.sms_found = true;
          } else {
            window.wrappedJSObject.sms_found = false;
          }
        };

        requestRet.onerror = function(event) {
            window.wrappedJSObject.sms_found = false;
        };
        marionetteScriptFinished(1);
        """, script_args=[sms_id], special_powers=True)

        found = self.marionette.execute_script("return window.wrappedJSObject.sms_found")
        self.assertEqual(found, expect_found, error_message)

    def delete_message(self, sms_id):
        print "Deleting SMS (id: %s)" %sms_id
        self.marionette.execute_async_script("""
        let requestRet = window.navigator.mozMobileMessage.delete(arguments[0]);

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

        deleted = self.marionette.execute_script("return window.wrappedJSObject.sms_deleted")
        self.assertTrue(deleted, "MozMobileMessage.delete returned unexpected error and failed to delete the SMS")
