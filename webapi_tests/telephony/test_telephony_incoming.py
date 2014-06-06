# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from webapi_tests.semiauto import TestCase
from webapi_tests.telephony import TelephonyTestCommon


class TestTelephonyIncoming(TestCase, TelephonyTestCommon):
    def setUp(self):
        self.addCleanup(self.clean_up)
        super(TestTelephonyIncoming, self).setUp()
        # disable the default dialer manager so it doesn't grab our calls
        self.disable_dialer()

    def test_telephony_incoming(self):
        # ask user to call the device; answer and verify via webapi
        self.user_guided_incoming_call()

        # keep call active for awhile
        time.sleep(5)

        # disconnect the call
        self.hangup_active_call()

    def clean_up(self):
        # re-enable the default dialer manager
        self.enable_dialer()
