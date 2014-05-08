# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from semiauto import TestCase
from telephony import TelephonyTestCommon


class TestTelephonyIncoming(TestCase, TelephonyTestCommon):
    def test_telephony_incoming(self):
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()

        # re-enable the default dialer manager
        self.enable_dialer()
