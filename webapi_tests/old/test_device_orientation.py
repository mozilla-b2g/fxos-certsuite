import time
from webapi_tests import MinimalTestCase

class TestDeviceOrientation(MinimalTestCase):
    def tearDown(self):
        clear_script = """
            window.removeEventListener("deviceorientation", window.wrappedJSObject.deviceListener);
            window.removeEventListener("deviceorientation", window.wrappedJSObject.checkValues);
        """
        self.marionette.execute_script(clear_script)
        MinimalTestCase.tearDown(self)

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
                      "then back to its starting position (z-axis test)")
        self.instruct("Pick up the phone and rotate the phone so the screen is perpendicular to the table, "\
                      "so the screen is facing you, then hold it parallel to the floor (y-axis test)")
        self.instruct("Rotate the phone left or right by more than 90 degrees and back to its starting position (x-axis test)")
        self.assertEqual(type(self.get_window_value("absolute")), bool)
        self.assertTrue(self.get_window_value('alpha'))
        self.assertTrue(self.get_window_value('beta'))
        self.assertTrue(self.get_window_value('gamma'))
