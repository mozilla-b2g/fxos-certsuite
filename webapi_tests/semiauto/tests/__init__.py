# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from tests import *
from test_sms import TestSms


def all(handler):
    env = environment.get(InProcessTestEnvironment)
    suite = unittest.TestSuite()
    suite.addTest(TestSms("test_navigate", handler=handler))
    return suite
