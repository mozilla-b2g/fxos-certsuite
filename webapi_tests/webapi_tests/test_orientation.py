from webapi_tests import MinimalTestCase

class TestProximity(MinimalTestCase):
    def test_proximity_change(self):
        self.instruct("Ensure the phone is unlocked and in portrait mode")
        orientation = self.marionette.execute_script("return window.wrappedJSObject.screen.mozOrientation;")
        self.assertTrue("portrait" in orientation)
        self.instruct("Now rotate the phone into landscape mode")
        orientation = self.marionette.execute_script("return window.wrappedJSObject.screen.mozOrientation;")
        self.assertTrue("landscape" in orientation)
