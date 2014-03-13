import datetime

from webapi_tests import MinimalTestCase
from webapi_tests import ContactsTestCommon

class TestAddContact(MinimalTestCase, ContactsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            window.navigator.mozContacts.oncontactchange = null;
        """)
        MinimalTestCase.tearDown(self)

    def test_add_basic_contact(self):
        first = 'First (%s)' %datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last = 'Last'
        email_type = 'work'
        email_adr = 'email@domain.com'
        note = 'Brought to you by Firefox OS'
        tel_type = 'mobile'
        tel = '5551234567'
        adr_type = 'work'
        adr_street = '123 Maple Street'
        adr_locality = 'Toronto'
        adr_region = 'ON'
        adr_postalCode = 'A1B 2C3'
        adr_countryName = 'Canada'
        contact_info = [first, last, email_type, email_adr, note, tel_type, tel,
                        adr_type, adr_street, adr_locality, adr_region, adr_postalCode, adr_countryName]
        self.add_basic_contact(contact_info)
