# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests import MinimalTestCase
from webapi_tests import ContactsTestCommon


class TestFindContacts(MinimalTestCase, ContactsTestCommon):
    def tearDown(self):
        MinimalTestCase.tearDown(self)

    def test_find_contacts(self):
        # delete all contacts from the device to start clean
        self.clear_contacts()

        # add a bunch of new contacts
        for count in range(10):
            self.add_basic_contact()

        # find contacts and verify
        self.find_contacts(expected=10)
