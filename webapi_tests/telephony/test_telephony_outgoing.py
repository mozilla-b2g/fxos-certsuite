# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyOutgoing(TestCase, TelephonyTestCommon):
    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyOutgoing, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_outgoing(self):
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

        # use the webapi to make an outgoing call to user-specified number; user answer
        self.user_guided_outgoing_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
