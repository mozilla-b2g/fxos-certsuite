===========================
Running Guided WebAPI Tests
===========================

This test tool will eventually contain a full suite of guided WebAPI tests
that allow a tester to interact with the phone to perform functional
testing of WebAPI's.

This semi-auto harness is in development, but you can run a prototype
of these tests now.  To do so:

    cd webapi_tests
    ./setup_and_run.sh

This will install a test app on your device, and then open a web page on 
your host browser (*not* on the device), which will lead you through the tests.
The prototype only contains a small set of SMS tests, but many more will
be added in the coming weeks.
