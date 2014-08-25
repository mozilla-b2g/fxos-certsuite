# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
from marionette.wait import Wait

from webapi_tests.semiauto import TestCase
from webapi_tests.bluetooth import BluetoothTestCommon


class TestBluetoothDebug(TestCase, BluetoothTestCommon):

    def setUp(self):
        super(TestBluetoothDebug, self).setUp()
        self.wait_for_obj("window.navigator.mozBluetooth")
        # start with bt disabled
        if self.is_bt_enabled():
            self.set_bt_enabled(False)
        self.have_adapter = False

    def test_enabled(self):
        self.set_bt_enabled(True)
        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.bt_adapter = null;
        var mozBt = window.navigator.mozBluetooth;

        console.log("Getting default bluetooth adaptor");
        var request = mozBt.getDefaultAdapter();

        request.onsuccess = function() {
            console.log("mozBluetooth.getDefaultAdapter request success");
            window.wrappedJSObject.rcvd_success = true;
            window.wrappedJSObject.bt_adapter = request.result;
        };

        request.onerror = function() {
            console.log("mozBluetooth.getDefaultAdapter request returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """)

        # wait for adapter to be found
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("mozBluetooth.getDefaultAdapter returned error")
            else:
                self.fail("mozBluetooth.getDefaultAdapter failed")

        self.marionette.execute_script("""
            for (let i in window.wrappedJSObject.bt_adapter) {
                log("property " + i);
                log("property value " + window.wrappedJSObject.bt_adapter[i]);
            }
            """)

