from webapi_tests import MinimalTestCase
from webapi_tests import ContactsTestCommon

class TestClearContacts(MinimalTestCase, ContactsTestCommon):
    def tearDown(self):
        MinimalTestCase.tearDown(self)

    def test_clear_contacts(self):
        # add a bunch of new contacts
        for count in range(10):
            self.add_basic_contact()

        # clear all contacts and verify
        self.clear_contacts()
