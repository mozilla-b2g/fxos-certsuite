from webapi_tests import MinimalTestCase

class TestBattery(MinimalTestCase):
    def tearDown(self):
        self.marionette.execute_script("""
        window.navigator.battery.onchargingchange = null;
        window.navigator.battery.onchargingtimechange = null;
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
        window.wrappedJSObject.chargingStates = [];
        window.wrappedJSObject.change_function = function(event, obj){
                                  var battery =  window.navigator.battery;
                                  var data = [event.type, battery.charging, battery.chargingTime,
                                              battery.dischargingTime];
                                  obj.push(data);
                                };
        window.navigator.battery.onchargingchange = function(evt) { 
                                                 window.wrappedJSObject.change_function(
                                                    evt, 
                                                    window.wrappedJSObject.chargeStates);};
        window.navigator.battery.onchargingtimechange = function(evt) { 
                                                 window.wrappedJSObject.change_function(
                                                    evt, 
                                                    window.wrappedJSObject.chargingStates);};
        """
        self.marionette.execute_script(script)
        self.unplug_and_instruct("Wait 5 seconds")
        charge_values = self.marionette.execute_script("return window.wrappedJSObject.chargeStates")
        charging_values = self.marionette.execute_script("return window.wrappedJSObject.chargingStates")
        def check_values(values, event):
            state = values[0]
            self.assertEqual(state[0], event)
            self.assertEqual(state[1], False)
            self.assertEqual(state[2], None)
            self.assertEqual(state[3], None)
            state = values[1]
            self.assertEqual(state[1], True)
        check_values(charge_values, "chargingchange")
        check_values(charging_values, "chargingtimechange")
