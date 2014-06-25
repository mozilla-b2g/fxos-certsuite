# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase
from webapi_tests.apps import AppsTestCommon


class TestAppsBasic(TestCase, AppsTestCommon):
    def setUp(self):
        super(TestAppsBasic, self).setUp()

    def test_get_self(self):
        app = self.get_self()
        self.assertEqual(app["manifest"]["name"], "CertTest App", "Application name is different or called from outside of CertTest App")
        self.assertEqual(app["manifest"]["description"], "Generated app", "Application description is different from Generated app")
