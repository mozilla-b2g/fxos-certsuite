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

Once installed, adb must be on your PATH.  If you use the bash shell
emulator you can modify your *~/.bashrc* or equivalent file, by
adding the following line to the file (replacing $SDK_HOME with the
location of the Android SDK::

    export PATH=$SDK_HOME:$PATH

The device must have a SIM card with a functioning phone
subscription to receive SMS messages and phone calls for a subset of the tests
to pass.

The device must have an SD card inserted with some free space available for
a subset of the tests to pass.

Network
-------

The device must be connected to WiFi and must have network access to
the host machine.

On the host machine, the following ports are required, and must not
have any existing servers running on them:

- 2828
- 8000
- 8001
- 8888

Any network firewall must be configured to allow the device to access
the host computer on the above ports.

Additionally, if you run the test suite on Mac you need to disable
the system firewall so that the servers used as part of the test
suite can listen to the ports mentioned above.  To do this, head
to the *Security & Privacy* pane in *System Preferences* and click
the *Turn Off Firewall* button if present.
