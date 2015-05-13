# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os


atoms_dir = os.path.abspath(os.path.join(__file__, os.path.pardir, "atoms"))


class Settings(object):
    atom = os.path.join(atoms_dir, "data_layer.js")

    def __init__(self, driver):
        self.driver = driver
        self.driver.import_script(Settings.atom)

    def get(self, key):
        return self.driver.execute_async_script(
            "return GaiaDataLayer.getSetting('%s')" % key.replace("'", '"'),
            special_powers=True)

    def set(self, key, value):
        value = json.dumps(value)
        self.driver.execute_script(
            "return GaiaDataLayer.setSetting('%s', %s)" %
            (key.replace("'", '"'), value),
            special_powers=True)
