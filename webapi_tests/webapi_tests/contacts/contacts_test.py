import time

class ContactsTestCommon(object):
    def __init__(self):
        self.new_contact = None

    def add_basic_contact(self, contact_info):
        # add a new contact using the given info
        #print "Adding new contact (%s %s)" %(first, last)
        print "Adding new contact: %s" %contact_info[0]
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;
        window.wrappedJSObject.gotChangeEvent = false;

        window.navigator.mozContacts.oncontactchange = function(event) {
            console.log("Received mozContacts.oncontactchange event");
            window.wrappedJSObject.gotChangeEvent = true;
        };

        var contactData = {
            givenName: [arguments[0][0]],
            familyName: [arguments[0][1]],
            email: [{type: [arguments[0][2]], value: [arguments[0][3]]}],
            note: [arguments[0][4]],
            tel: [{type: [arguments[0][5]], value: [arguments[0][6]]}],
            adr: [{type: [arguments[0][7]], streetAddress: [arguments[0][8]], locality: [arguments[0][9]],
            region: [arguments[0][10]], postalCode: [arguments[0][11]], countryName: [arguments[0][12]]}]
        };

        var person = new mozContact(contactData);

        // save the new contact
        var saving = window.navigator.mozContacts.save(person);

        saving.onsuccess = function() {
            console.log("Received mozContacts.saving.onsuccess event");
            window.wrappedJSObject.gotSuccess = true;
        };

        saving.onerror = function(err) {
            window.wrappedJSObject.gotSuccess = false;
        };
        marionetteScriptFinished(1);
        """, script_args=[contact_info], special_powers=True)

        # sleep a couple of seconds to ensure contact saved
        time.sleep(2)

        # verify contact was added (should have got onsuccess and contactschange event)
        changed = self.marionette.execute_script("return window.wrappedJSObject.gotChangeEvent")
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(changed, "Should have received mozContacts.oncontactchange event")
        self.assertTrue(success, "Should have received mozContacts saving.success event")
