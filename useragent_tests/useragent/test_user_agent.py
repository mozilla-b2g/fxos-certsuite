# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from useragent_tests.useragent import UserAgentTestCommon
from webapi_tests.semiauto import TestCase

class TestUserAgent(TestCase, UserAgentTestCommon):

    # def setUp(self):
    #     self.setup()

    def test_user_agent(self):
        user_agent_string = self.get_user_agent()
        valid, message = self.check_user_agent_is_valid(user_agent_string)
        self.assertTrue(valid, message)
