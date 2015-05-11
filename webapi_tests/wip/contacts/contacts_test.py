# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time


class ContactsTestCommon(object):
    def __init__(self):
        self.event_reason = ""
        self.test_contact = ""

    def add_basic_contact(self):
        # add a new test contact
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;
        window.wrappedJSObject.gotChangeEvent = false;
        window.wrappedJSObject.event_reason = "";
        window.wrappedJSObject.test_contact = null;

        window.navigator.mozContacts.oncontactchange = function(event) {
            console.log("Received mozContacts.oncontactchange event");
            window.wrappedJSObject.gotChangeEvent = true;
            window.wrappedJSObject.event_reason = event.reason;
        };

        var curdate = new Date();
        var first_name = 'First (' + curdate.getHours() + ':' + curdate.getMinutes() + ':' + curdate.getSeconds() + ')';
        var contactData = {
            givenName: [first_name],
            familyName: ['Last'],
            email: [{type: ['work'], value: ['email@domain.com']}],
            note: ['Brought to you by Firefox OS'],
            tel: [{type: ['mobile'], value: ['5551234567']}],
            adr: [{type: ['work'], streetAddress: ['123 Maple Lane'], locality: ['Toronto'],
            region: ['ON'], postalCode: ['A1B 2C3'], countryName: ['Canada']}]
        };

        let person = new mozContact(contactData);

        // save the new contact
        var saving = window.navigator.mozContacts.save(person);

        saving.onsuccess = function() {
            console.log("Received mozContacts.saving.onsuccess event");
            window.wrappedJSObject.gotSuccess = true;
            window.wrappedJSObject.test_contact = person;
        };

        saving.onerror = function(err) {
            window.wrappedJSObject.gotSuccess = false;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

        # sleep a couple of seconds to ensure contact saved
        time.sleep(2)

        # verify contact was added (should have got onsuccess and contactschange event)
        changed = self.marionette.execute_script("return window.wrappedJSObject.gotChangeEvent")
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(changed, "Should have received mozContacts.oncontactchange event")
        self.assertTrue(success, "Should have received mozContacts saving.success event")

        # verify contact event
        self.event_reason = self.marionette.execute_script("return window.wrappedJSObject.event_reason")
        self.test_contact = self.marionette.execute_script("return window.wrappedJSObject.test_contact")
        self.assertEqual(self.event_reason, 'create', "mozContacts.oncontactchange event reason should be 'create'")
        self.assertTrue(len(self.test_contact['id']) > 0, "mozContacts.oncontactchange event contactID must not be 0")

        # no longer need listener
        self.marionette.execute_script("""
            window.navigator.mozContacts.oncontactchange = null;
        """)

    def delete_contact(self):
        # delete the test contact
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;
        window.wrappedJSObject.gotChangeEvent = false;
        window.wrappedJSObject.event_reason = "";

        window.navigator.mozContacts.oncontactchange = function(event) {
            console.log("Received mozContacts.oncontactchange event");
            window.wrappedJSObject.gotChangeEvent = true;
            window.wrappedJSObject.event_reason = event.reason;
            window.wrappedJSObject.event_contact_id = event.contactID;
        };

        var request = window.navigator.mozContacts.remove(window.wrappedJSObject.test_contact);

        request.onsuccess = function() {
            console.log("Received mozContacts.remove onsuccess event");
            window.wrappedJSObject.gotSuccess = true;
        };

        request.onerror = function(err) {
            window.wrappedJSObject.gotSuccess = false;
        };
        marionetteScriptFinished(1);
        """, special_powers=True)

        # sleep a couple of seconds
        time.sleep(2)

        # verify contact was deleted (should have got onsuccess and contactschange event)
        changed = self.marionette.execute_script("return window.wrappedJSObject.gotChangeEvent")
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(changed, "Should have received mozContacts.oncontactchange event")
        self.assertTrue(success, "Should have received mozContacts remove onsuccess event")

        # verify contact removed event
        self.event_reason = self.marionette.execute_script("return window.wrappedJSObject.event_reason")
        self.event_contact_id = self.marionette.execute_script("return window.wrappedJSObject.event_contact_id")
        self.assertEqual(self.event_reason, "remove", "mozContacts.oncontactchange event reason should be 'remove'")
        self.assertEqual(self.event_contact_id, self.test_contact['id'], "mozContacts.oncontactchange event contactID should match")

        # no longer need listener
        self.marionette.execute_script("""
            window.navigator.mozContacts.oncontactchange = null;
        """)

    def find_contacts(self, expected):
        # find contacts and verify expected number were found
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;
        window.wrappedJSObject.contacts_found = 0;

        var filter = {
            filterBy: ["givenName"],
            filterOp: "startsWith",
            filterValue: "F"
        };

        var request = window.navigator.mozContacts.find(filter);
        var count = 0;

        request.onsuccess = function () {
            window.wrappedJSObject.gotSuccess = true;
            window.wrappedJSObject.contacts_found = this.result.length;
        }

        request.onerror = function (err) {
            console.log('mozContacts.find returned error');
            console.log(err);
        }
        marionetteScriptFinished(1);
        """, special_powers=True)

        # verify success event
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(success, "Should have received mozContacts.findContact onsuccess event")

        # verify count is as expected
        found = self.marionette.execute_script("return window.wrappedJSObject.contacts_found")
        self.assertEqual(found, expected, "mozContacts.findContact returned unexpected count")

    def get_count(self, expected):
        # get the number of contacts and verify the expected count
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;
        window.wrappedJSObject.count = 0;

        var request = window.navigator.mozContacts.getCount();

        request.onsuccess = function () {
            console.log("Received mozContacts.getCount onsuccess event");
            window.wrappedJSObject.gotSuccess = true;
            window.wrappedJSObject.count = this.result;
        }

        request.onerror = function (err) {
            console.log("mozContacts.getCount returned error")
            console.log(err);
        }
        marionetteScriptFinished(1);
        """, special_powers=True)

        time.sleep(2)

        # verify received onsuccess event
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(success, "Should have received mozContacts.getCount onsuccess event")

        # verify count is as expected
        count_returned = self.marionette.execute_script("return window.wrappedJSObject.count")
        self.assertEqual(count_returned, expected, "mozContacts.getCount returned unexpected value")

    def get_all_contacts(self, expected):
        # find contacts and verify expected number were found
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotEvent = false;
        window.wrappedJSObject.found = 0;

        var filter = {
            filterBy: ["givenName"],
            filterOp: "startsWith",
            filterValue: "F"
        };

        var request = window.navigator.mozContacts.getAll(filter);
        var count = 0;

        request.onsuccess = function () {
            if(this.result) {
                count++;
                // Move to the next contact which will call the request.onsuccess with a new result
                this.continue();
            } else {
                window.wrappedJSObject.found = count;
                window.wrappedJSObject.gotEvent = true;
            }
        }

        request.onerror = function (err) {
            console.log('mozContacts.getAll returned error');
            console.log(err);
        }
        marionetteScriptFinished(1);
        """, special_powers=True)

        # fails without a sleep here
        time.sleep(5)

        # verify success event
        success = self.marionette.execute_script("return window.wrappedJSObject.gotEvent")
        self.assertTrue(success, "Should have received mozContacts.getAll onsuccess event")

        # verify count is as expected
        found = self.marionette.execute_script("return window.wrappedJSObject.found")
        self.assertEqual(found, expected, "mozContacts.getAll returned unexpected count")

    def clear_contacts(self):
        # erase all contacts from the device
        self.marionette.execute_async_script("""
        window.wrappedJSObject.gotSuccess = false;

        var request = window.navigator.mozContacts.clear();

        request.onsuccess = function () {
            console.log("Received mozContacts.clear onsuccess event");
            window.wrappedJSObject.gotSuccess = true;
        }

        request.onerror = function (err) {
            console.log("mozContacts.clear returned error")
            console.log(err);
        }
        marionetteScriptFinished(1);
        """, special_powers=True)

        # give time for delete, could be alot of contacts
        time.sleep(15)

        # verify received onsuccess event
        success = self.marionette.execute_script("return window.wrappedJSObject.gotSuccess")
        self.assertTrue(success, "Should have received mozContacts.clear onsuccess event")

        # verify there are zero contacts remaining
        self.get_count(expected=0)
