==================================
Firefox OS Certification Testsuite
==================================

Tests and tools to verify the functionality and characteristics of
Firefox OS on real devices.

The test suite is designed to run on unprivileged devices and does not
rely on high level instrumentation.  Instead human interaction is
needed throughout the test suite to perform various instructions in
order to assert that conditions are met on the device.

Requirements
============

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

Enabling ADB
------------

Furthermore, you must turn on adb access on the device:

**For Firefox OS version 1.3:** Launch *Settings*, and navigate to
*Device Information* → *More Information* → *Developer*, then check
*Remote Debugging*.

**For version 1.4:** Launch *Settings*, and navigate to *Device
Information* → *More Information*, then check *Developer Options*.
Next, hold down the *Home* button, and close the *Settings* app (press
the x).  Finally, launch *Settings* again, and navigate to
*Developer*, then select *ADB only* in *Remote Debugging*.

Once this is done, go to *Settings* → *Display* and set the *Screen
Timeout* to “never”.  You need this because adb will not work when the
device is locked.

Quick Setup and Usage
=====================

You can setup your environment and run the tests by running::

    ./run.sh --version=<some version> --result-file=<absolute filepath>

The *--version* and *--result* arguments are optional.  If passed,
*--version* must be one of our supported release versions, either 1.3
or 1.4.  If you don't pass a version, 1.3 will be assumed.  The
*--result-file* option can be used to specify where you want the json
file to be created.  By default, it will write the file *results.json*
in the current working directory.

This command sets up a virtual environment for you, with all the
proper packages installed, activates the environment, runs the tests,
and lastly deactivates the environment.

You may call *run.sh* as many times as you like, and it will run the
tests using its previously set up virtual environment.

Setup Using virtualenv
======================

If the quick setup doesn't work, then follow these instructions.  You
can set up and run this tool inside a virtual environment.  From the
root directory of your source checkout, run::

    virtualenv .
    ./bin/pip install -e .

Then activate the virtualenv::

    source bin/activate

Usage
=====

The certification test suite can be run simply by executing::

    cert

To get a list of command-line arguments, use::

    cert --help

Submitting Results
==================

Once the tests have completed successfully, they will write a file
containing the results to disk; by default this file is called
*results.json* and will be put in your current working directory.
Please compress this file and e-mail it to fxos-cert@mozilla.com.
