# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

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
