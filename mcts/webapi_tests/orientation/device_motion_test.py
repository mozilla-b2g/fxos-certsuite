# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class DeviceMotionTestCommon(object):

    def __init__(self):
        pass

    def clear_event_listener(self):
        clear_script = """
            window.removeEventListener("devicemotion", window.wrappedJSObject.deviceListener);
            window.removeEventListener("devicemotion", window.wrappedJSObject.checkValues);
        """
        self.marionette.execute_script(clear_script)

    def get_window_value(self, name):
        return self.marionette.execute_script("return window.wrappedJSObject.%s;" % name)

    def get_obj_value(self, objName, name):
        return self.marionette.execute_script("return window.wrappedJSObject.%s.%s" % (objName, name))

    def setup_default_device_motion(self):
        script = """
            window.wrappedJSObject.deviceMotionInterval = null;
            window.wrappedJSObject.acceleration = {};
            window.wrappedJSObject.acceleration.xOrig = null;
            window.wrappedJSObject.acceleration.yOrig = null;
            window.wrappedJSObject.acceleration.zOrig = null;
            window.wrappedJSObject.acceleration.x = false;
            window.wrappedJSObject.acceleration.y = false;
            window.wrappedJSObject.acceleration.z = false;
            window.wrappedJSObject.accelerationIncludingGravity = {};
            window.wrappedJSObject.accelerationIncludingGravity.xOrig = null;
            window.wrappedJSObject.accelerationIncludingGravity.yOrig = null;
            window.wrappedJSObject.accelerationIncludingGravity.zOrig = null;
            window.wrappedJSObject.accelerationIncludingGravity.x = false;
            window.wrappedJSObject.accelerationIncludingGravity.y = false;
            window.wrappedJSObject.accelerationIncludingGravity.z = false;
            window.wrappedJSObject.rotationRate = {};
            window.wrappedJSObject.rotationRate.xOrig = null;
            window.wrappedJSObject.rotationRate.yOrig = null;
            window.wrappedJSObject.rotationRate.zOrig = null;
            window.wrappedJSObject.rotationRate.x = false;
            window.wrappedJSObject.rotationRate.y = false;
            window.wrappedJSObject.rotationRate.z = false;

            window.wrappedJSObject.checkValues = function(evt) {
                window.wrappedJSObject.deviceMotionInterval = (evt.interval > 0) ? true : false;
                if (evt.acceleration){
                    var setDeviceAccelerationValue = function(value) {
                        if (!window.wrappedJSObject.acceleration[value]) {
                            var orig = Math.abs(window.wrappedJSObject.acceleration[value+'Orig']);
                            var newValue = Math.abs(evt.acceleration[value]);
                            window.wrappedJSObject.acceleration[value] = ((Math.abs(newValue-orig) > 1) ? true : false);
                        }
                    };
                    setDeviceAccelerationValue('x');
                    setDeviceAccelerationValue('y');
                    setDeviceAccelerationValue('z');
                }

                if (evt.accelerationIncludingGravity) {
                    var setDeviceAccelerationIncludingGravityValue = function(value) {
                        if (!window.wrappedJSObject.accelerationIncludingGravity[value]) {
                            var orig = Math.abs(window.wrappedJSObject.accelerationIncludingGravity[value+'Orig']);
                            var newValue = Math.abs(evt.accelerationIncludingGravity[value]);
                            window.wrappedJSObject.accelerationIncludingGravity[value] = ((Math.abs(newValue-orig) > 3) ? true : false);
                        }
                    };
                    setDeviceAccelerationIncludingGravityValue('x');
                    setDeviceAccelerationIncludingGravityValue('y');
                    setDeviceAccelerationIncludingGravityValue('z');
                }

                if (evt.rotationRate) {
                    var setDeviceRotationRateValue = function(value) {
                        if (!window.wrappedJSObject.rotationRate[value]) {
                            var orig = Math.abs(window.wrappedJSObject.rotationRate[value+'Orig']);
                            var newValue = Math.abs(evt.rotationRate[value]);
                            window.wrappedJSObject.rotationRate[value] = ((Math.abs(newValue-orig) > 45) ? true : false);
                        }
                    };
                    setDeviceRotationRateValue('alpha');
                    setDeviceRotationRateValue('beta');
                    setDeviceRotationRateValue('gamma');
                }
            };
            window.wrappedJSObject.deviceListener = function(evt) {
                window.wrappedJSObject.removeEventListener("devicemotion", window.wrappedJSObject.deviceListener);
                if (evt.acceleration) {
                    window.wrappedJSObject.acceleration.xOrig = evt.acceleration.x;
                    window.wrappedJSObject.acceleration.yOrig = evt.acceleration.y;
                    window.wrappedJSObject.acceleration.zOrig = evt.acceleration.z;
                }
                if (evt.accelerationIncludingGravity) {
                    window.wrappedJSObject.accelerationIncludingGravity.xOrig = evt.accelerationIncludingGravity.x;
                    window.wrappedJSObject.accelerationIncludingGravity.yOrig = evt.accelerationIncludingGravity.y;
                    window.wrappedJSObject.accelerationIncludingGravity.zOrig = evt.accelerationIncludingGravity.z;
                }
                if (evt.wrappedJSObject.rotationRate) {
                    window.wrappedJSObject.rotationRate.alphaOrig = evt.rotationRate.alpha;
                    window.wrappedJSObject.rotationRate.betaOrig = evt.rotationRate.beta;
                    window.wrappedJSObject.rotationRate.gammaOrig = evt.rotationRate.gamma;
                }
                window.wrappedJSObject.addEventListener("devicemotion", window.wrappedJSObject.checkValues);
            };
            window.wrappedJSObject.addEventListener("devicemotion", window.wrappedJSObject.deviceListener);
        """
        self.marionette.execute_script(script)
