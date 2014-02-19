fxos-certsuite
==============

A tool to verify the functionality and characteristics of FirefoxOS
devices.

Requirements
------------

Currently requires a Linux or Mac based system with adb installed.  If you
need to install adb, see
https://developer.mozilla.org/en-US/Firefox_OS/Debugging/Installing_ADB.

The device and the machine running the tests must be on the same WiFi
network.

Furthermore, you must turn on adb access:

For FirefoxOS version 1.3: Launch Settings, and navigate to Device
Information -> More Information -> Developer, then check Remote Debugging.

For version 1.4: Launch Settings, and navigate to Device Information -> More
Information, then check Developer Options.  Next, hold down the Home button,
and close the Settings app (press the x).  Finally, launch Settings again,
and navigate to Developer, then select 'ADB only' in Remote Debugging.

Quick Setup and Usage
---------------------

You can setup your environment and run the tests by running:

    source run.sh --version=<some version> --result-file=<absolute filepath>

The --version and --result arguments are optional. If passed, --version must
be one of our supported release  versions, either 1.3 or 1.4. If you don't pass
a version, 1.3 will be assumed. The --result-file option can  be used to
specify where you want the json file to be created. By default, it will create
it as results.json in the current working directory.

This command sets up a virtual environment for you, with all the proper
packages installed, activates the environment, runs the tests, 
and lastly deactivates the environment.

You may call 'source run.sh' as many times as you like, and it
will run the tests using its previously set up virtual environment.

Alternative Setup
-----------------

If the quick setup doesn't work, then follow these instructions.
You can set up and run this tool inside a virtual environment.  From
the root directory of your source checkout, run:

    virtualenv .
    ./bin/pip install -e .

Then activate the virtualenv:

    source bin/activate

You should then be able to run the certification suite simply by
executing:

    cert

To get a list of command-line arguments, use:

    cert --help


Submitting Results
------------------

Once the tests have completed successfully, they will write a file
containing the results; by default this file is called results.json.  Please
compress this file and e-mail it to fxos-cert@mozilla.com.
