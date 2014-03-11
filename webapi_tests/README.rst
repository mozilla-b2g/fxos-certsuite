
==================================
WebAPI Tests
==================================

A tool to verify the functionality of WebAPIs on FxOS devices

Requirements
============

The certification test suite is intended to run on a host computer
attached to the device via USB cable. Currently the host requires the
Linux or Mac OS operating systems with *adb* (Android Debug Bridge)
installed.

If you need to install adb, see
https://developer.mozilla.org/en-US/Firefox_OS/Debugging/Installing_ADB.

Once installed, add adb to your PATH in your ~/.bashrc
or equivalent file, by adding the following line to the file
(replacing $SDK_HOME with the location of the android sdk):

    PATH=$SDK_HOME:$PATH

The device and the host machine running the tests must also be on the
same Wi-Fi network.

Enabling ADB
------------

Furthermore, you must turn on adb access on the device:

**For Firefox OS version 1.3:** Launch *Settings*, and navigate to
*Device Information* -> *More Information* -> *Developer*, then check
*Remote Debugging*.

**For version 1.4:** Launch *Settings*, and navigate to *Device
Information* -> *More Information*, then check *Developer Options*.
Next, hold down the *Home* button, and close the *Settings* app (press
the x).  Finally, launch *Settings* again, and navigate to
*Developer*, then select *ADB only* in *Remote Debugging*.

Once this is done, go to Settings->Display and set the 'Screen Timeout' to
'never'. You need this because adb will not work when the device is locked.

Quick Setup and Usage
=====================

If the device you have is a production build, then first you have
to set up Marionette on your phone. DO NOT run this if you have
an 'eng' build (Marionette is already installed!). 

If you are not sure which build you have, you can check to see if
Marionette is installed. To do this, run::

    adb shell stop b2g
    adb shell start b2g
    adb logcat | grep -i Marionette

Wait for the phone to restart and get to the lockscreen. If you don't
see any output with 'Marionette' in it, then you do not have Marionette 
installed, and you will need to install it. If you do see output, 
then you can skip this step.

To install Marionette, run:: 

    source install_marionette_extension.sh

For both production and eng builds, to set up and run the tests, run:: 

    source setup_and_run.sh

This command sets up a virtual environment for you, with all the
proper packages installed, activates the environment, runs the tests,
and lastly deactivates the environment.

You may call *setup_and_run.sh* as many times as you like, and it will run the
tests using its previously set up virtual environment.

Setup and Usage Using virtualenv
======================

If the quick setup doesn't work, then follow these instructions.  You
can set up and run this tool inside a virtual environment.  From the
root directory of your source checkout, run::

    virtualenv .
    ./bin/pip install -e .

Then activate the virtualenv::

    source bin/activate

Then install the package::

    python setup.py install

The test suite can be run simply by executing::

    marionette --address=localhost:2828 <path to test or manifest>

