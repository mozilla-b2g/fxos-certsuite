fxos-certsuite
==============

A tool to verify the functionality and characteristics of FirefoxOS
devices.

Requirements
------------

Currently requires a Linux or Mac based system with adb installed.
The device and machine running the tests must be on the same WIFI
network.

Quick Setup and Usage
-------------------

You can setup your environment and run the tests by running:

    source run.sh

This sets up a virtual environment for you, with all the proper
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
