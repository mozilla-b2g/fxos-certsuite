# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

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
