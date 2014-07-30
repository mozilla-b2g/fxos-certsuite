# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os


__all__ = ["Settings", "LockScreen", "Screen"]

atoms_dir = os.path.join(__file__, os.path.pardir, "atoms")


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
        import json
        value = json.dumps(value)
        self.driver.execute_script(
            "return GaiaDataLayer.setSetting('%s', %s)" %
            (key.replace("'", '"'), value),
            special_powers=True)


class LockScreen(object):
    atom = os.path.join(atoms_dir, "lock_screen.js")

    def __init__(self, driver):
        self.driver = driver
        self.driver.import_script(LockScreen.atom)

    @property
    def is_locked(self):
        return self.driver.execute_script(
            "return window.wrappedJSObject.lockScreen.locked")

    def lock(self):
        self.driver.switch_to_frame()
        result = self.driver.execute_async_script("GaiaLockScreen.lock()")
        assert result, "Unable to lock screen"

    def unlock(self):
        self.driver.switch_to_frame()
        result = self.driver.execute_async_script(
            "GaiaLockScreen.unlock()")
        assert result, "Unable to unlock screen"


class Screen(object):
    def __init__(self, driver):
        self.driver = driver

    def on(self):
        self.driver.execute_script(
            "window.wrappedJSObject.ScreenManager.turnScreenOn()")

    def off(self):
        self.driver.execute_script(
            "window.wrappedJSObject.ScreenManager.turnScreenOff()")
