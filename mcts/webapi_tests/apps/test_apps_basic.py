# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.apps import AppsTestCommon


class TestAppsBasic(TestCase, AppsTestCommon):
    def setUp(self):
        super(TestAppsBasic, self).setUp()
        self.wait_for_obj("window.navigator.mozApps")

    def test_get_self(self):
        app = self.get_self()
        self.assertEqual(app["manifest"]["name"], "CertTest App", "Application name is different from CertTest App")
        self.assertEqual(app["manifest"]["description"], "Generated app", "Application description is different from Generated app")

    def test_get_all(self):
        applist = self.get_all()
        for app in applist:
            if app["manifest"]["name"] == "CertTest App":
                self.assertEqual(app["manifest"]["developer"]["url"], "https://wiki.mozilla.org/Auto-tools",
                                "Application developer url is different from https://wiki.mozilla.org/Auto-tools")
                
                # for Stingray the app is installed manually, the origin is different from we expected
                # self.assertEqual(app["origin"], "app://certtest-app", "Application origin is different from app://certtest-app")
                break
