# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.webrtc import WebrtcTestCommon


class TestWebrtcBasic(TestCase, WebrtcTestCommon):
    def setUp(self):
        super(TestWebrtcBasic, self).setUp()

    def test_basic_wifi_enabled(self):
        # enable wifi via settings
        ret = self.webrtc_message_test()
        self.assertEqual(ret, "pc1 said: test from pc2")
