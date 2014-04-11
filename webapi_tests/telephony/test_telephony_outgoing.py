# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from telephony import TelephonyTestCommon


class TestTelephonyOutgoing(TestCase, TelephonyTestCommon):
    def test_telephony_outgoing(self):
        # use the webapi to make an outgoing call to user-specified number; user answer
        self.user_guided_outgoing_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()
