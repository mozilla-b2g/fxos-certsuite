from webapi_tests import MinimalTestCase

class TestBattery(MinimalTestCase):
    def tearDown(self):
        self.marionette.execute_script("""
        window.navigator.battery.onchargingchange = null;
        window.navigator.battery.onlevelchange = null;
        """)
        MinimalTestCase.tearDown(self)

    def test_battery_charge(self):
        # set up listener to store changes in an object
        script = """
        var battery = window.navigator.battery;
        var data = [battery.charging, battery.chargingTime,
                   (battery.dischargingTime != undefined),
                   (battery.level != undefined)];
        return data;
        """
        data = self.marionette.execute_script(script)
        self.assertEqual(data[0], True)
        self.assertTrue(type(data[1]) == int)
        self.assertTrue(data[2])
        self.assertTrue(data[3])

    def test_battery_discharge(self):
        # set up listener to store changes in an object
        script = """
        window.wrappedJSObject.chargeStates = [];
        window.wrappedJSObject.charge_function = function(event){
                                  var battery =  window.navigator.battery;
                                  var data = [event.type, battery.charging, battery.chargingTime,
                                              battery.dischargingTime];
                                  window.wrappedJSObject.chargeStates.push(data);
                                };
        window.navigator.battery.onchargingchange = window.wrappedJSObject.charge_function;
        """
        self.marionette.execute_script(script)
        self.unplug_and_instruct("Wait 5 seconds")
        charge_values = self.marionette.execute_script("return window.wrappedJSObject.chargeStates")
        self.assertNotEqual(0, len(charge_values))
        state = charge_values[0]
        self.assertEqual(state[0], "chargingchange")
        self.assertEqual(state[1], False)
        self.assertEqual(state[2], None)
        self.assertEqual(state[3], None)
