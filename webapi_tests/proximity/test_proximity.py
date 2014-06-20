# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from webapi_tests.semiauto import TestCase


class TestProximity(TestCase):
    """
    This is a test for the `Proximity API`_ which will:

    - Setup an event listener for the device proximity light sensor
    - Ask the test user to place their hand near/over the device light sensor
    - Verify a proximity event was triggered

    .. _`Proximity API`: https://developer.mozilla.org/en-US/docs/Web/API/Proximity_Events
    """

    def tearDown(self):
        self.marionette.execute_script("""
        window.removeEventListener('devicelight', window.wrappedJSObject.prox_function);
        """)
        TestCase.tearDown(self)

    def test_proximity_change(self):
        self.instruct("Ensure the phone is unlocked and held in your hand, perpendicular to the floor")
        # set up listener to store changes in an object
        # NOTE: use wrappedJSObject to access non-standard properties of window
        script = """
        window.wrappedJSObject.proximityStates = [];
        window.wrappedJSObject.prox_function = function(event){
                                  window.wrappedJSObject.proximityStates.push((event.value != undefined));
                                };
        window.addEventListener('devicelight', window.wrappedJSObject.prox_function);
        """
        self.marionette.execute_script(script)
        self.instruct("Move your hand toward the screen until the screen darkens")
        proximity_values = self.marionette.execute_script("return window.wrappedJSObject.proximityStates")
        self.assertNotEqual(0, len(proximity_values), "Expected proximity event")
        self.assertTrue(proximity_values[0], "Expected proximity event")
