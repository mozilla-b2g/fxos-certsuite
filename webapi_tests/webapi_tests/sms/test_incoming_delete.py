import time

from webapi_tests import MinimalTestCase
from webapi_tests import SmsTestCommon

class TestSmsIncomingDelete(MinimalTestCase, SmsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            window.navigator.mozMobileMessage.onreceived = null;
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        MinimalTestCase.tearDown(self)

    def test_sms_incoming_delete(self):
        self.user_guided_incoming_sms()

        # delete fails sometimes without a sleep (because of the msg notification?)
        time.sleep(5)

        # delete the SMS using the webapi
        sms_to_delete = self.in_sms['id']
        self.delete_message(sms_to_delete)

        # now verify the message has been deleted by trying to get it, should fail
        print "Verifying SMS (id: %s) has been deleted" %sms_to_delete
        error_message = "mozMobileMessage.getMessage found the deleted SMS but shouldn't have; delete failed"
        self.get_message(sms_to_delete, False, error_message)
