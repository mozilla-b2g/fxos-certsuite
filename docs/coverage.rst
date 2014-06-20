Test Coverage
=============

Web Platform Tests
------------------

Tests from the W3C's web-platform-tests_ testsuite covering
standardised, web-exposed, platform features. These tests work by
loading HTML documents in a simple test application and using
javascript to determine the test result. Tests are divided
into groups — i.e. directories — according to the specification that
they are testing. The upstream testsuite is undergoing continual
development and it is not expected that we pass all tests; instead
correctness for the purposes of the certsuite is determined by
comparison to a reference run. At present the following tests groups
are enabled:

dom
  Tests for the dom core specification

IndexedDB
  Tests for the IndexedDB specification

touch_events
  Simple tests for the automatically verifiable parts of the touch
  events specification
  
.. _web-platform-tests: https://github.com/w3c/web-platform-tests/

Guided WebAPI Tests
-------------------

WebAPIs makes it possible to interface between the web platform and
device compatibility and access APIs.  To test these APIs we need
to assert certain physical aspects about the phone during the
testrun.

E.g. to verify that the device does indeed change its screen
orientation when tilted 90º, we will first ask the user to turn the
device and then ask her for the perceived orientation, which is
then compared with what the API reports.

For this reason the guided Web API tests, backed by the test harness
*semiauto*, requires a user to interact with various questions and
prompts raised by the tests.  This works by showing a dialogue with
a question, confirmation, or input request in a web browser on the
user's host computer (the computer the device is connected to).

To ensure that all facets of the various WebAPIs are covered the
tests also require a number of phyiscal aids to be present when the
tests are running.  These involve the presence of a Wi-Fi network,
a bluetooth enabled second device, a phone with SMS and MMS
capabilities, &c.

As with the web platform tests, the tests are organized into logical
groups divided by directories or Python modules.  It is expected
that the device under test passes all the following guided WebAPI
test groups:

bluetooth
  Bluetooth API provides low-level access to the device's Bluetooth
  hardware.

fm_radio
  Provides support for a device's FM radio functionality, if
  available.

geolocation
  Provides information about the device's physical location.

mobile_message
  Lets apps send and receive SMS text messages, as well as to access
  and manage the messages stored on the device.

mozpower
  Lets apps turn on and off the screen, CPU, device power, and so
  forth.  Also provides support for listening for and inspecting
  resource lock events.

moztime
  Provides support for setting the current time.

notification
  Lets applications send notifications displayed at the system level.

orientation
  Provides notifications when the device's orientation changes.

proximity
  Lets you detect proximity of the device to a nearby object, such
  as the user's face.

tcp_socket
  Provides low-level sockets and SSL support.

telephony
  Lets apps place and answer phone calls and use the built-in
  telephony user interface.

vibration
  Lets apps control the device's vibration hardware for things such
  as haptic feedback in games.

wifi
  A privileged API which provides information about signal strength,
  the name of the current network, available WiFi networks, and so
  forth.
