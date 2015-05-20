# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from mcts.webapi_tests.semiauto import TestCase
from mcts.webapi_tests.geolocation import GeolocationTestCommon


class TestGeolocationBasic(TestCase, GeolocationTestCommon):
    """
    This is a basic test of the `Geolocation API`_ including:

    - Enabling and disabling geolocation
    - Retrieving the current device location

    .. _`Geolocation API`: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation
    """

    def setUp(self):
        super(TestGeolocationBasic, self).setUp()
        self.wait_for_obj("window.navigator.geolocation")
        # ensure geolocation is available and enabled in settings
        self.assertTrue(self.is_geolocation_available(), "Geolocation is not available on the device")
        if not self.is_geolocation_enabled():
            self.set_geolocation_enabled(True)

    def test_enabled(self):
        # already enabled, so disable first
        self.set_geolocation_enabled(False)
        self.assertFalse(self.is_geolocation_enabled(), "Geolocation should NOT be enabled")
        time.sleep(5)
        self.set_geolocation_enabled(True)
        self.assertTrue(self.is_geolocation_enabled(), "Geolocation should be enabled")

    def test_get_current_position(self):
        position = self.get_current_position()
        # check position details exist
        self.assertIsNotNone(position['timestamp'], "position.timestamp must have a value")
        self.assertIsNotNone(position['coords']['altitude'], "position.coords.altitude must have a value")
        self.assertIsNotNone(position['coords']['latitude'], "position.coords.latitude must have a value")
        self.assertIsNotNone(position['coords']['longitude'], "position.coorts.longitude must have a value")
        self.assertIsNotNone(position['coords']['altitudeAccuracy'], "position.altitudeAccuracy must have a value")
        # disable checking speed and heading because bug 1090047
        # self.assertIsNone(position['coords']['speed'], "Expected position.speed to be 'None'")
        # self.assertIsNone(position['coords']['heading'], "Expected position.heading to be 'None'")
        self.assertIsNotNone(position['coords']['accuracy'], "position.accuracy must have a value")
        # ask user to verify lat/long using the web
        lat = position['coords']['latitude']
        long = position['coords']['longitude']
        self.confirm("Location found. <br /><br />Latitude: %s<br /> Longitude: %s<br /><br />"
                     " Please look up these coordinates on an internet mapping web site. Does"
                     " this correctly identify your current approximate location?" % (lat, long))
