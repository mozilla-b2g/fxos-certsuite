# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase
from mozapps import AppsTestCommon


class TestAppsBasic(TestCase, AppsTestCommon):
    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestAppsBasic, self).setUp()
        self.marionette.execute_script("window.wrappedJSObject.rcvd_app_name = null;")
        self.marionette.execute_script("window.wrappedJSObject.error_msg = null;")

    def test_getselfapp(self):
        app_name = self.get_selfapp()
        self.assertEqual(app_name, "CertTest App", "Application name is different or called from outside of CertTest App")

    def clean_up(self):
        self.marionette.execute_script("window.wrappedJSObject.rcvd_app_name = null;")
        self.marionette.execute_script("window.wrappedJSObject.error_msg = null;")
