from webapi_tests import MinimalTestCase

class TestBattery(MinimalTestCase):
    def tearDown(self):
        self.marionette.execute_script("""
        window.navigator.battery.onchargingchange = null;
        window.navigator.battery.onlevelchange = null;
        """)
        MinimalTestCase.tearDown(self)

    def test_proximity_change(self):
        # set up listener to store changes in an object
        # NOTE: use wrappedJSObject to access non-standard properties of window
        script = """
        window.wrappedJSObject.chargeStates = [];
        window.wrappedJSObject.charge_function = function(event){
                                  window.wrappedJSObject.chargeStates.push(event.type);
                                };
        window.navigator.battery.onchargingchange = window.wrappedJSObject.charge_function;
        """
        self.marionette.execute_script(script)
        self.unplug_and_instruct("Wait 5 seconds")
        charge_values = self.marionette.execute_script("return window.wrappedJSObject.chargeStates")
        self.assertNotEqual(0, len(charge_values))
        self.assertEqual(charge_values[0], "chargingchange")
