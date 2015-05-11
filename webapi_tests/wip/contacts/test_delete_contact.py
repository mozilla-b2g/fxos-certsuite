# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests import MinimalTestCase
from webapi_tests import ContactsTestCommon


class TestDeleteContact(MinimalTestCase, ContactsTestCommon):
    def tearDown(self):
        MinimalTestCase.tearDown(self)

    def test_delete_contact(self):
        # start with zero contacts
        self.clear_contacts()

        # add a test contact
        self.add_basic_contact()

        # verify 1 contact
        self.get_count(expected=1)

        # delete the test contact
        self.delete_contact()

        # verify zero contacts
        self.get_count(expected=0)
