# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
from cert import test_user_agent

class Logger(object):
    """Dummy logger"""
    def test_status(this, *args):
        pass

class TestCert(unittest.TestCase):

    def setUp(self):
        self.logger = Logger()

    def test_test_user_agent(self):
        self.assertFalse(test_user_agent("Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0", self.logger), "android")
        self.assertTrue(test_user_agent("Mozilla/5.0 (Mobile; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "mobile")
        self.assertTrue(test_user_agent("Mozilla/5.0 (Tablet; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "tablet")
        self.assertTrue(test_user_agent("Mozilla/5.0 (Mobile; nnnn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "example device")
        self.assertFalse(test_user_agent("Mozilla/5.0 (Mobile; nn nn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "invalid device")
        self.assertFalse(test_user_agent("Mozilla/5.0 (Mobile; nn;nn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "invalid device")
        self.assertFalse(test_user_agent("Mozilla/5.0 (Mobile; nn/nn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "invalid device")
        self.assertFalse(test_user_agent("Mozilla/5.0 (Mobile; nn(nn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "invalid device")
        self.assertFalse(test_user_agent("Mozilla/5.0 (Mobile; nn)nn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "invalid device")

        self.assertTrue(test_user_agent("Mozilla/5.0 (Mobile;   nnnn   ; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "extra whitespace in device")
        self.assertTrue(test_user_agent("Mozilla/5.0 (Mobile;nnnn; rv:26.0) Gecko/26.0 Firefox/26.0", self.logger), "no whitespace in device")

if __name__ == '__main__':
    unittest.main()
