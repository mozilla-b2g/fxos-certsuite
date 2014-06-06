from webapi_tests import MinimalTestCase

class TestVibrate(MinimalTestCase):
    def test_vibrate_basic(self):
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate(200);")
        self.confirm("Did you feel a vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200]);")
        self.confirm("Did you feel a vibration?")
        self.instruct("Ensure the phone is unlocked, then hold the phone.")
        self.marionette.execute_script("window.navigator.vibrate([200, 1000, 200]);")
        self.confirm("Did you feel two vibrations, with about 1 second between each pulse?")

