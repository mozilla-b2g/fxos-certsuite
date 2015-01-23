# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase


class TestDevicelight(TestCase):
    """
    This is a test for the `devicelight API`_ which will:

    - Setup an event listener for the devicelight sensor
    - Ask the test user to place their hand near/over the device light sensor
    - Verify a devicelight event was triggered

    .. _`Devicelight API`: https://developer.mozilla.org/en-US/docs/Web/API/DeviceLightEvent
    """

    def setUp(self):
        super(TestDevicelight, self).setUp()
        self.wait_for_obj("window.addEventListener")

    def tearDown(self):
        self.marionette.execute_script("""
        window.removeEventListener('devicelight', window.wrappedJSObject.event_function);
        """)
        TestCase.tearDown(self)

    def test_devicelight_change(self):
        self.instruct("Ensure the phone is unlocked and that the light sensor is fully exposed")
        # set up listener to store changes in an object
        # NOTE: use wrappedJSObject to access non-standard properties of window
        script = """
        window.wrappedJSObject.devicelightevents = [];
        window.wrappedJSObject.event_function = function(event){
                                  window.wrappedJSObject.devicelightevents.push((event.value != undefined));
                                };
        window.addEventListener('devicelight', window.wrappedJSObject.event_function);
        """
        self.marionette.execute_script(script)
        self.instruct("Completely cover the light sensor with your hand or other solid object")
        devicelight_events = self.marionette.execute_script("return window.wrappedJSObject.devicelightevents")
        self.assertNotEqual(0, len(devicelight_events), "Expected devicelight event")
        self.assertTrue(devicelight_events[0], "Expected devicelight event")
