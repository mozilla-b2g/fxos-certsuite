# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.orientation import DeviceMotionTestCommon


class TestDeviceMotion(TestCase, DeviceMotionTestCommon):
    """
    This is a test for the `Device Acceleration API`_ which will:

    - Setup a device motion event listener
    - Ask the test user to move the device into various positions
    - Verify that the corresponding device motion events are triggered

    .. _`Device Acceleration API` https://developer.mozilla.org/en-US/docs/Web/API/DeviceAcceleration
    .. _`Device Motion Event`: https://developer.mozilla.org/en-US/docs/Web/Events/devicemotion
    """

    def setUp(self):
        super(TestDeviceMotion, self).setUp()
        self.wait_for_obj("window.wrappedJSObject.addEventListener")

        self.instruct("Place the phone on a level surface and make sure the lockscreen is not on")
        # set up listener to store changes in an object
        self.setup_default_device_motion()
        self.instruct("Keep the phone on the surface and rotate the phone by more than 90 degrees "
                      "then back to its starting position (z-axis test)", "img/orientation_z-axis.png")
        self.instruct("Pick up the phone and rotate the phone so the screen is perpendicular to the table, "
                      "so the screen is facing you, then hold it parallel to the floor (x-axis test)", "img/orientation_x-axis.png")
        self.instruct("Rotate the phone left or right by more than 90 degrees and back to its starting position (y-axis test)", "img/orientation_y-axis.png")

    def tearDown(self):
        self.clear_event_listener()
        TestCase.tearDown(self)

    def test_device_motion_acceleration(self):
        x = self.get_obj_value('acceleration', 'x')
        y = self.get_obj_value('acceleration', 'y')
        z = self.get_obj_value('acceleration', 'z')
        if not (x and y and z):
            message = "Missing acceleration:" + ("" if x else " x") + ("" if y else " y") + ("" if z else " z")
            self.fail(message)
        
    def test_device_motion_acceleration_including_gravity(self):
        x = self.get_obj_value('accelerationIncludingGravity', 'x')
        y = self.get_obj_value('accelerationIncludingGravity', 'y')
        z = self.get_obj_value('accelerationIncludingGravity', 'z')
        if not (x and y and z):
            message = "Missing accelerationIncluding Gravity:" + ("" if x else " x") + ("" if y else " y") + ("" if z else " z")
            self.fail(message)

    def test_device_motion_rotation_rate(self):
        alpha = self.get_obj_value('rotationRate', 'alpha')
        beta = self.get_obj_value('rotationRate', 'beta')
        gamma = self.get_obj_value('rotationRate', 'gamma')
        if not (alpha and beta and gamma):
            message = "Missing accelerationIncluding Gravity:" + ("" if alpha else " alpha") + ("" if beta else " beta") + ("" if gamma else " gamma")
            self.fail(message)
