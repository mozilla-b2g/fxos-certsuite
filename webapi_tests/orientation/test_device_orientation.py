# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase


class TestDeviceOrientation(TestCase):
    """
    This is a test for the `Device Orientation API`_ which will:

    - Setup a device orientation event listener
    - Ask the test user to move the device into various positions
    - Verify that the corresponding device orientation events are triggered

    .. _`Device Orientation API`: https://developer.mozilla.org/en-US/docs/Web/API/Detecting_device_orientation
    """

    def setUp(self):
        super(TestDeviceOrientation, self).setUp()
        self.wait_for_obj("window.wrappedJSObject.addEventListener")

    def tearDown(self):
        clear_script = """
            window.removeEventListener("deviceorientation", window.wrappedJSObject.deviceListener);
            window.removeEventListener("deviceorientation", window.wrappedJSObject.checkValues);
        """
        self.marionette.execute_script(clear_script)
        TestCase.tearDown(self)

    def get_window_value(self, name):
        return self.marionette.execute_script("return window.wrappedJSObject.%s;" % name)

    def test_device_changes(self):
        # set up listener to store changes in an object
        script = """
        window.wrappedJSObject.absolute = null;
        window.wrappedJSObject.alphaOrig = null;
        window.wrappedJSObject.betaOrig = null;
        window.wrappedJSObject.gammaOrig = null;
        window.wrappedJSObject.alpha = false;
        window.wrappedJSObject.beta = false;
        window.wrappedJSObject.gamma = false;
        window.wrappedJSObject.checkValues = function(evt) {
            var setDeviceValue = function(value){
              if (!window.wrappedJSObject[value]) {
                console.log("MDAS: FFFS ORIG" + window.wrappedJSObject[value+'Orig']);
                console.log("MDAS: FFFS goddamn new" + evt[value]);
                var orig = Math.abs(window.wrappedJSObject[value+'Orig']);
                var newValue = Math.abs(evt[value]);
                console.log("MDAS " + value + " : " + (newValue - orig));
                window.wrappedJSObject[value] = ((Math.abs(newValue-orig) > 70) ? true : false);
              }
            };
            setDeviceValue('alpha');
            setDeviceValue('beta');
            setDeviceValue('gamma');
        };
        window.wrappedJSObject.deviceListener = function (evt) {
            window.wrappedJSObject.removeEventListener("deviceorientation", window.wrappedJSObject.deviceListener);
            window.wrappedJSObject.absolute = evt.absolute;
            window.wrappedJSObject.alphaOrig = evt.alpha;
            window.wrappedJSObject.betaOrig = evt.beta;
            window.wrappedJSObject.gammaOrig = evt.gamma;
            console.log("NOOOOOOOOOOOOOO");
            window.wrappedJSObject.addEventListener("deviceorientation", window.wrappedJSObject.checkValues);
        };
        window.wrappedJSObject.addEventListener("deviceorientation", window.wrappedJSObject.deviceListener);
        """
        self.instruct("Place the phone on a level surface and make sure the lockscreen is not on")
        # set up listener to store changes in an object
        self.marionette.execute_script(script)
        self.instruct("Keep the phone on the surface and rotate the phone by more than 90 degrees "\
                      "then back to its starting position (z-axis test)", "img/orientation_z-axis.png")
        self.instruct("Pick up the phone and rotate the phone so the screen is perpendicular to the table, "\
                      "so the screen is facing you, then hold it parallel to the floor (x-axis test)", "img/orientation_x-axis.png")
        self.instruct("Rotate the phone left or right by more than 90 degrees and back to its starting position (y-axis test)", "img/orientation_y-axis.png")
        self.assertEqual(type(self.get_window_value("absolute")), bool, "expected absolute")
        self.assertTrue(self.get_window_value('alpha'), "expected alpha")
        self.assertTrue(self.get_window_value('beta'), "expected beta")
        self.assertTrue(self.get_window_value('gamma'), "expected gamma")
