# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase


class PowerManagement(TestCase):

    def test_brightness_decrease(self):
        self.instruct("Testing decrease in brightness")
        decrease_brightness = """
            //initialize the brightness
            window.navigator.mozPower.screenBrightness = 1.0;
            //decresing the brightnesss
            window.navigator.mozPower.screenBrightness = 0.1;
        """
        self.marionette.execute_script(decrease_brightness)
        self.confirm("Did you notice decrease in brightness ?")

    def test_brightness_increase(self):
        self.confirm("Testing increase in brightness")
        increase_brightness = """
            window.navigator.mozPower.screenBrightness = 1.0;
        """
        self.marionette.execute_script(increase_brightness)
        self.confirm("Did you notice increase in brightness ?")
