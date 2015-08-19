# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver.wait import Wait


class BluetoothTestCommon(object):
    have_adapter = False

    @property
    def get_adapter_name(self):
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.name")

    @property
    def get_adapter_state(self):
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.state")

    @property
    def get_adapter_address(self):
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.address")

    @property
    def get_adapter_discoverable(self):
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discoverable")

    @property
    def get_adapter_discovering(self):
        return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.discovering")

    @property
    def is_bt_enabled(self):
        if self.marionette.execute_script("return !!window.wrappedJSObject.bt_adapter;"):
            return self.marionette.execute_script("return window.wrappedJSObject.bt_adapter.state == 'enabled';")
        else:
            return False

    def get_default_bt_adapter(self):
        # check if bt_adapter exsists (it can check empty string, null, undefined, NaN, false, 0)
        if self.marionette.execute_script("return !!window.wrappedJSObject.bt_adapter;"):
            return True

        self.marionette.execute_async_script("""
        var bt_adapter = navigator.mozBluetooth.defaultAdapter;

        function sleep(ms) {
            var unixtime_ms = new Date().getTime();
            while(new Date().getTime() < unixtime_ms + ms) {}
        }

        // set onattributechange so that bluetooth adapter can be ready
        bt_adapter.onattributechanged = function onAdapterAttributeChanged(evt) {
          for (var i in evt.attrs) {
            switch (evt.attrs[i]) {
              case 'defaultAdapter':
                window.wrappedJSObject.bt_adapter = bt_adapter;
              case 'state':
                console.log("adapter state changed to", window.wrappedJSObject.bt_adapter.state);
                break;
              case 'name':
                console.log("adapter name changed to", window.wrappedJSObject.bt_adapter.name);
                break;
              case 'discoverable':
                console.log("adapter discoverable changed to", window.wrappedJSObject.bt_adapter.discoverable);
                break;
              default:
                break;
            };
          };
        };

        // wait at least 1 second before taking bt_adapter;
        sleep(5000);
        window.wrappedJSObject.bt_adapter = bt_adapter;

        marionetteScriptFinished(1);
        """)

        self.assertTrue("return !!window.wrappedJSObject.bt_adapter")
        return True

    def set_bt_enabled(self, enable):
        self.get_default_bt_adapter()

        if enable:
            self.marionette.execute_async_script("""
                window.wrappedJSObject.bt_adapter.enable();
                marionetteScriptFinished(1);
            """)
        else:
            self.marionette.execute_async_script("""
                window.wrappedJSObject.bt_adapter.disable();
                marionetteScriptFinished(1);
            """)


        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            if enable:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.state == 'enabled';"))
            else:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.state == 'disabled';"))
        except:
            if enable:
                self.fail("Failed to enable bluetooth")
            else:
                self.fail("Failed to disable bluetooth")

    def set_bt_discoverable_mode(self, set_discoverable):
        self.set_bt_enabled(True)

        if set_discoverable:
            self.marionette.execute_async_script("""
                window.wrappedJSObject.bt_adapter.setDiscoverable(true);
                marionetteScriptFinished(1);
            """)
        else:
            self.marionette.execute_async_script("""
                window.wrappedJSObject.bt_adapter.disable(false);
                marionetteScriptFinished(1);
            """)

        # wait for enabled/disabled event
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            if set_discoverable:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.discoverable == true;"))
            else:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.discoverable == false;"))
        except:
            if set_discoverable:
                self.fail("Failed to enable bluetooth discoverable")
            else:
                self.fail("Failed to disable bluetooth discoverable")

    def bt_discovery(self, set_discovering):
        self.set_bt_enabled(True)

        if set_discovering:
            self.marionette.execute_async_script("""
            window.wrappedJSObject.found_device_count = 0;
            var discoveryHandle;

            window.wrappedJSObject.bt_adapter.startDiscovery().then ( function onResolve(handle) {
              console.log("Resolved with discoveryHandle");

              // Keep reference to handle in order to listen to ondevicefound event handler 
              discoveryHandle = handle;
              discoveryHandle.ondevicefound = function onDeviceFound(evt) {
                var device = evt.device;
                console.log("Discovered remote device. Address:", device.address);
                window.wrappedJSObject.found_device_count++;
              };
            }, function onReject(aReason) {
              console.log("Rejected with this reason: " + aReason);
            });

            marionetteScriptFinished(1);
            """)
        else:
            self.marionette.execute_async_script("""
            window.wrappedJSObject.bt_adapter.stopDiscovery().then ( function onResolve() {
              console.log("Resolved with void value");
            }, function onReject(aReason) {
              console.log("Rejected with this reason: " + aReason);
            });

            marionetteScriptFinished(1);
            """)

        # wait for request success
        wait = Wait(self.marionette, timeout=30, interval=0.5)
        try:
            if set_discovering:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.discovering == true;"))
            else:
                wait.until(lambda m: m.execute_script("return window.wrappedJSObject.bt_adapter.discovering == false;"))
        except:
            if set_discovering:
                self.fail("Failed to enable bluetooth discovering")
            else:
                self.fail("Failed to disable bluetooth discovering")

    def get_num_bt_devices_found(self):
        return self.marionette.execute_script("return window.wrappedJSObject.found_device_count || 0")
