Setup and Usage
===============

There are two methods for setting up and running the test suite:
The “quick” method and the “virtualenv” way.  For either to work
you must enable adb access to the device.

Enabling ADB
------------

**For Firefox OS version 1.3:** Launch *Settings*, and navigate to
*Device Information* → *More Information* → *Developer*, then check
*Remote Debugging*.

**For version 1.4:** Launch *Settings*, and navigate to *Device
Information* → *More Information*, then check *Developer Options*.
Next, hold down the *Home* button, and close the *Settings* app
(press the *X*).  Finally, launch *Settings* again, and navigate
to *Developer*, then select *ADB only* in *Remote Debugging*.

Once this is done, go to *Settings* → *Display* and set the *Screen
Timeout* to “never”.  You need this because adb will not work when
the device is locked.

Quick Setup and Usage
---------------------

You can setup your environment and run the tests by running::

    ./run.sh --version=<some version>

The *--version* argument is optional.  If passed, *--version* must
be one of our supported release versions, either 1.3 or 1.4.  If
you don't pass a version, 1.3 will be assumed.

This command sets up a virtual environment for you, with all the
proper packages installed, activates the environment, runs the
tests, and lastly deactivates the environment.

You may call *run.sh* as many times as you like, and it will run
the tests using its previously set up virtual environment.

Some of the tests for Web APIs require manual user intervention.
At this point a browser will open on your host computer.  Simply
follow the instructions given on screen.

Setup and Usage With virtualenv
-------------------------------

If the quick setup doesn't work, then follow these instructions.
You can set up and run this tool inside a virtual environment.  From
the root directory of your source checkout, run::

    virtualenv .
    ./bin/pip install -e .

Then activate the virtualenv::

    source bin/activate

Once the virtualenv is activated, the certification test suite can
be run by executing::

    runcertsuite

To get a list of command-line arguments, use::

    runcertsuite --help

For example it is possible to list logical test groups and to run
filtered test runs of only a subset of the tests::

    runcertsuite --list-test-groups

Submitting Results
------------------

Once the tests have completed successfully, they will write a file
containing the results to disk; by default this file is called
*firefox-os-certification.zip* and will be put in your current
working directory. Please e-mail this file to fxos-cert@mozilla.com.

Known Issues
------------

* Bug 1030238 - Semi-auto WebAPI tests do not produce a log file
* Bug 1026259 - web-platform tests sometimes lose wifi connection
