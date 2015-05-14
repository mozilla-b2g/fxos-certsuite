# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette.wait import Wait


class BluetoothTestCommon(object):
    have_adapter = False

    def is_bt_enabled(self):
        return self.marionette.execute_script("return window.navigator.mozBluetooth.enabled;")

    def set_bt_enabled(self, enable):
        self.marionette.execute_async_script("""
        var enable = arguments[0];
        window.wrappedJSObject.rcvd_enabled_event = false;
        window.wrappedJSObject.rcvd_disabled_event = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.rcvd_adapter_added_event = false;
        var mozBT = window.navigator.mozBluetooth;

        mozBT.onenabled = function() {
           console.log("Recieved mozBluetooth.onenabled event");
           window.wrappedJSObject.rcvd_enabled_event = true;
        };

        mozBT.ondisabled = function() {
           console.log("Received mozBluetooth.ondisabled event");
           window.wrappedJSObject.rcvd_disabled_event = true;
        };

        mozBT.onadapteradded = function() {
           console.log("Recieved mozBluetooth.onadapteradded event");
           window.wrappedJSObject.rcvd_adapter_added_event = true;
        };

        if (enable) {
            console.log("Turning on bluetooth via settings");
        } else {
            console.log("Turning off bluetooth via settings");
        }
        var lock = window.navigator.mozSettings.createLock();

        var result = lock.set({
            'bluetooth.enabled': enable
        });

        result.onerror = function() {
            if (enable) {
                console.log("Failed to changed Bluetooth setting to ON");
            } else {
                console.log("Failed to changed Bluetooth setting to OFF");
            }
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[enable])

        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            if enable:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_enabled_event;"))
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_adapter_added_event;"))
            else:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.rcvd_disabled_event;"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error;"):
                self.fail("Error received while changing the bluetooth enabled setting")
            else:
                if enable:
                    self.fail("Failed to enable bluetooth via mozSettings")
                else:
                    self.fail("Failed to disable bluetooth via mozSettings")

    def get_default_bt_adapter(self):
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

        # https://developer.mozilla.org/en-US/docs/Web/API/BluetoothAdapter
        # TODO: work around until bug https://bugzilla.mozilla.org/show_bug.cgi?id=1138331 is fixed
        adapter = {}
        adapter['name'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.name")
        adapter['class'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.class")
        adapter['address'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.address")
        adapter['discoverable'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverable")
        adapter['discoverableTimeout'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverableTimeout")
        adapter['discovering'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discovering")
        adapter['devices'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.devices")
        adapter['uuids'] = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.uuids")
        self.assertIsNotNone(adapter, "mozBluetooth.getDefaultAdapter returned none")
        self.have_adapter = True
        return adapter

    def get_bt_discoverable_timeout(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverableTimeout")

    def set_bt_discoverable_timeout(self, timeout):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        # no point in setting if it is already set to the requested value
        if self.get_bt_discoverable_timeout() == timeout:
            return

        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        window.wrappedJSObject.discoverable_timeout = null;
        var mozBt = window.navigator.mozBluetooth;
        var mozBtAdapter = window.wrappedJSObject.bt_adapter;
        var new_timeout = arguments[0];

        console.log("Setting bluetooth discoverable timeout");
        var request = mozBtAdapter.setDiscoverableTimeout(new_timeout);

        request.onsuccess = function() {
            console.log("BluetoothAdapter.setDiscoverableTimeout request success");
            window.wrappedJSObject.rcvd_success = true;
            window.wrappedJSObject.discoverable_timeout = mozBtAdapter.discoverableTimeout;
        };

        request.onerror = function() {
            console.log("BluetoothAdapter.setDiscoverableTimeout returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[timeout])
        # wait for timeout to be set
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("BluetoothAdapter.setDiscoverableTimeout returned error")
            else:
                self.fail("BluetoothAdapter.setDiscoverableTimeout failed")

        set_timeout = self.get_bt_discoverable_timeout()
        self.assertEqual(set_timeout, timeout, "BluetoothAdapter.discoverableTimeout value was not set correctly")

    def get_bt_discoverable_mode(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverable")

    def set_bt_discoverable_mode(self, set_discoverable):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")

        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        var mozBtAdapter = window.wrappedJSObject.bt_adapter;
        var set_discoverable = arguments[0];

        if (set_discoverable == true){
            console.log("Turning on bluetooth discoverable mode");
        } else {
            console.log("Turning off bluetooth discoverable mode");
        }

        var request = mozBtAdapter.setDiscoverable(set_discoverable);

        request.onsuccess = function() {
            console.log("BluetoothAdapter.setDiscoverable request success");
            window.wrappedJSObject.rcvd_success = true;
        };

        request.onerror = function() {
            console.log("BluetoothAdapter.setDiscoverable returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[set_discoverable])

        # wait for request success
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("BluetoothAdapter.setDiscoverable returned error")
            else:
                self.fail("BluetoothAdapter.setDiscoverable failed")

        discoverable_setting = self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverable")
        if set_discoverable:
            self.assertTrue(discoverable_setting, "Firefox OS BluetoothAdapter.discoverable should be TRUE")
        else:
            self.assertFalse(discoverable_setting, "Firefox OS BluetoothAdapter.discoverable should be FALSE")

    def set_bt_adapter_name(self, new_name):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")

        # no point in changing name if it is already set the same
        if self.get_bt_adaptor_name() == new_name:
            return

        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        var mozBtAdapter = window.wrappedJSObject.bt_adapter;
        var new_name = arguments[0];

        console.log("Changing bluetooth adaptor name to '%s'" %new_name);

        var request = mozBtAdapter.setName(new_name);

        request.onsuccess = function() {
            console.log("BluetoothAdapter.setName request success");
            window.wrappedJSObject.rcvd_success = true;
        };

        request.onerror = function() {
            console.log("BluetoothAdapter.setName returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """, script_args=[new_name])

        # wait for request success
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("BluetoothAdapter.setName returned error")
            else:
                self.fail("BluetoothAdapter.setName failed")

        self.assertEqual(new_name, self.get_bt_adaptor_name(), "The bluetooth adaptor name is incorrect")

    def get_bt_adaptor_name(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.name")

    def get_bt_discovering(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discovering || false")

    def start_bt_discovery(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        self.marionette.execute_async_script("""
        window.wrappedJSObject.found_device_count = 0;
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        var mozBtAdapter = window.wrappedJSObject.bt_adapter;

        // Setup callback for when a bt device is found
        mozBtAdapter.ondevicefound = function () {
            console.log("Discovery found a bluetooth device nearby");
            window.wrappedJSObject.found_device_count++;
        };

        // Begin discovery and verify request success
        console.log("Starting bluetooth discovery");

        var request = mozBtAdapter.startDiscovery();

        request.onsuccess = function() {
            console.log("BluetoothAdapter.startDiscovery request success");
            window.wrappedJSObject.rcvd_success = true;
        };

        request.onerror = function() {
            console.log("BluetoothAdapter.startDiscovery returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """)

        # wait for request success
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("BluetoothAdapter.startDiscovery returned error")
            else:
                self.fail("BluetoothAdapter.startDiscovery failed")

        # verify in discovering mode
        self.assertTrue(self.get_bt_discovering(), "Failed to start bluetooth discovery")

    def stop_bt_discovery(self):
        self.assertTrue(self.have_adapter, "Must get default bluetooth adapter first")
        self.marionette.execute_async_script("""
        window.wrappedJSObject.rcvd_success = false;
        window.wrappedJSObject.rcvd_error = false;
        var mozBtAdapter = window.wrappedJSObject.bt_adapter;

        console.log("Stopping bluetooth discovery");

        var request = mozBtAdapter.stopDiscovery();

        request.onsuccess = function() {
            console.log("BluetoothAdapter.stopDiscovery request success");
            window.wrappedJSObject.rcvd_success = true;
        };

        request.onerror = function() {
            console.log("BluetoothAdapter.stopDiscovery returned error");
            window.wrappedJSObject.rcvd_error = true;
        };
        marionetteScriptFinished(1);
        """)

        # wait for request success
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            wait.until(lambda x: x.execute_script("return window.wrappedJSObject.rcvd_success"))
        except:
            if self.marionette.execute_script("return window.wrappedJSObject.rcvd_error"):
                self.fail("BluetoothAdapter.stopDiscovery returned error")
            else:
                self.fail("BluetoothAdapter.stopDiscovery failed")

        # verify no longer discovering
        self.assertFalse(self.get_bt_discovering(), "Failed to stop bluetooth discovery")

    def get_num_bt_devices_found(self):
        return self.marionette.execute_script("return window.wrappedJSObject.found_device_count || 0")
