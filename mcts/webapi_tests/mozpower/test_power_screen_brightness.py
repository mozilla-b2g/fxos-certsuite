# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase


class TestPowerManagement(TestCase):
    """
    This is a test for the `Power Management API`_ which will:

    - Test increasing the device screen brightness (verified by the test user)
    - Test decreasing the device screen brightness (verified by the test user)

    .. _`Power Management API`: https://developer.mozilla.org/en-US/docs/Web/API/Power_Management_API
    """

    def setUp(self):
        super(TestPowerManagement, self).setUp()
        self.wait_for_obj("window.navigator.mozPower")

    def test_brightness_decrease(self):
        #initialize the screen brightness
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")
        self.instruct("About to decrease the screen "
                      "brightness; please watch the screen and click OK")
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 0.1")
        self.confirm("Did you notice decrease in brightness?")

    def test_brightness_increase(self):
        #initialize the screen brightness
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 0.1;")
        self.instruct("About to increase the screen "
                      "brightness; please watch the screen and click OK")
        self.marionette.execute_script("window.navigator.mozPower.screenBrightness = 1.0;")
        self.confirm("Did you notice increase in brightness?")
