fxos-certsuite
==============

A tool to verify the functionality and characteristics of FirefoxOS devices.

Requirements
============

Currently requires a Linux or Mac based system with adb installed. The device
and machine running the tests must be on the same WIFI network.

Setup
=====

You can set up and run this tool inside a virtual environment. From the root
directory of your source checkout, run:

    virtualenv .
    ./bin/pip install -e .

Then activate the virtualenv:

    source bin/activate

You should then be able to run the certification suite simply by executing:

    cert
