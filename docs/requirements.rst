Requirements
============

The test suite is designed to run on unprivileged devices and does not
rely on high level instrumentation.  Instead human interaction is
needed throughout the test suite to perform various instructions in
order to assert that conditions are met on the device.

The certification test suite is intended to run on a host computer
attached to the device via USB cable.  Currently the host requires the
Linux or Mac OS operating systems with *adb* (Android Debug Bridge)
installed.

If you need to install adb, see
https://developer.mozilla.org/en-US/Firefox_OS/Debugging/Installing_ADB.

Once installed, add adb to your PATH in your ~/.bashrc
or equivalent file, by adding the following line to the file
(replacing $SDK_HOME with the location of the android sdk)::

    PATH=$SDK_HOME:$PATH

The device and the host machine running the tests must also be on the
same Wi-Fi network.

Furthermore, the device must have a SIM card with a functioning phone
subscription to receive SMS messages for a subset of the tests to
pass.
