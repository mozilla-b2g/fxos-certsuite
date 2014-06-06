from webapi_tests import MinimalTestCase
from webapi_tests import ContactsTestCommon

class TestGetAllContacts(MinimalTestCase, ContactsTestCommon):
    def tearDown(self):
        MinimalTestCase.tearDown(self)

    def test_get_all_contacts(self):
        # delete all contacts from the device to start clean
        self.clear_contacts()

        # add a bunch of new contacts
        for count in range(10):
            self.add_basic_contact()

        # get all contacts and verify
        self.get_all_contacts(expected=10)
