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

WebAPIs make it possible to interface between the web platform and
device compatibility APIs.  To test these APIs we need to assert
certain physical aspects about the phone during the testrun.

E.g. to verify that the device does indeed change its screen
orientation when tilted 90º, we will first ask the user to turn the
device and then ask her for the perceived orientation, which is
then compared with what the API reports.

For this reason the guided Web API tests, backed by the test harness
*semiauto*, require a user to interact with various questions and
prompts raised by the tests.  This works by showing a dialogue with
a question, confirmation, or input request in a web browser on the
user's host computer (the computer the device is connected to).

To ensure that all facets of the various WebAPIs are covered the
tests also require a number of phyiscal aids to be present when the
tests are running.  These involve the presence of a Wi-Fi network,
a bluetooth enabled second device, a phone with SMS and MMS
capabilities, &c.

As with the web platform tests, the tests are organized in logical
groups divided by directories (listed below) that make up Python
modules.  Some of the tests may not be applicable depending on the
device under test's capabilities and hardware configuration.

bluetooth
  Bluetooth API provides low-level access to the device's Bluetooth
  hardware.

fm_radio
  Provides support for a device's FM radio functionality.

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


WebAPI Verifier
----------------
The WebAPI Verifier test group attempts to detect changes to the supported
WebAPIs. Test apps are generated with all permissions for each app type
(hosted, privileged, certified) and the tests are repeated for each
condition.

Coverage is provided in two ways. The first is a simple recursive walk of
the window (and so also the navigator) object which enumerates properties
of each object encountered. This is compared to an expected results list,
which will detect added, removed and modified properties. It is not capable
of detecting behavioural or semantic modifications (for example, changes to
the arguments for a method.)

The W3C WebIDL test suite [1] is used to provide additional test coverage.
This suite generates tests to verify WebAPI implementations based upon the
WebIDL files used to define them. It goes further than the simple recursive
enumeration of properties described above. For example, given a method on an
interface, it creates tests to verify the type of the method is 'function',
checks that the length of the operation matches the minimum number of arguments
specified in the IDL file, and verifies that function will throw a TypeError if
called with fewer arguments.

The the WebIDL test suite is itself is still under development and so has bugs
and does not provide complete coverage. It was originally designed to work on a
desktop browser and will run out of memory on some devices. To work around these
problems, a preprocessing step is performed using the in-tree WebIDL.py parser,
which also limits testing to a subset of the interfaces defined in the full set
of WebIDL files.

This avoids out-of-memory situations on the device as well as running tests
which are guaranteed to fail. For example, the version of the test suite in use
currently expects every interface defined to be accessible from the window
object, which is not the case for interfaces like 'AbstractWorker'. These
interfaces are made available to the test suite when testing other interfaces,
but are not directly tested themselves.

The WebIDL test suite should be sufficient by itself to verify the WebAPIs have
not been modified, but since it is not complete, the recursive walk of the
window object is also performed to provide additional coverage.

[1] https://github.com/w3c/testharness.js/

Permissions
-----------

The permissions model is tested by first retrieving the PermissionsTable from
the device. Then for each app type (hosted, privileged, certified) an app is
generated and installed on the device. For each permission in the
PermissionsTable, the value is queried in the app and compared to an expected
result. This comparison will detect added or removed permissions, as well as
any changes to the default permission value (deny, prompt, allow) for each
app type.

Once this is complete, a second round of testing determines the effect of
setting each permission to 'allow'. A baseline result is generated by
recursively walking the window object with no permissions set. Then each
permission is individually set to 'allow' and then window object is again
walked and the result compared to the baseline. This will detect any changes to
the window or navigator object that result from the permission being set.

This is not sufficient to detect the effect of all permissions. For instance, to
detect whether the mozbrowser permission is granted, it is necessary to create
an iframe with mozbrower and then look for additional properties on it. A small
number of hand written tests are run to accomodate these cases, and again
compared to expected results.

Not all permissions are not currently tested due to a variety of reasons:
* background-sensors (planned feature)
* background-service (planned feature)
* deprecated-hwvideo (removed)
* networkstats-manage (only used in Gaia)
* storage (attempts to test this result in OOM)
* audio-capture (triggers known bug on some devices)
* video-capture (triggers known bug on some devices)
* network-events (requires phone to be on data network, but the testharness
requires wifi)
* wappush (requires source of wappush events)

Omni Analyzer
-------------

Many of Gecko's JavaScript sources are compressed into an omni.ja file which
is part of all FirefoxOS distributions.  The omni-analyzer extracts these files
and compares them to a relevant reference version.  Any differences are
logged, and the diffs between test and reference files can be viewed using the
omni_diff.py tool.

The omni-analyzer does not produce pass/fail results; differences in
JavaScript source files should be reviewed by an engineer to determine whether
they're harmless in terms of FirefoxOS branding requirements.

User-Agent Test
---------------

The user-agent test verifies that the user agent string reported by the device
conforms to the `Gecko user agent specification`_ and the `device model inclusion requirements`_.

.. _Gecko user agent specification: https://developer.mozilla.org/en-US/docs/Web/HTTP/Gecko_user_agent_string_reference#Firefox_OS
.. _device model inclusion requirements: https://wiki.mozilla.org/B2G/User_Agent/Device_Model_Inclusion_Requirements
