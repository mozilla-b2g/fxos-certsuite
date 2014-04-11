===========================
Running Guided WebAPI Tests
===========================

This test tool will eventually contain a full suite of guided WebAPI tests
that allow a tester to interact with the phone to perform functional
testing of WebAPI's.

This semi-auto harness is in development, but you can run a prototype
of these tests now.  To do so:

    cd webapi_tests
    ./setup_and_run.sh <directory>

where <directory> is one of the directory names under webapi_tests that contains
tests, one of: sms, proximity, tcp_socket, telephony, orientation, or 
vibration.

This will install a test app on your device, and then open a web page on 
your host browser (*not* on the device), which will lead you through the tests.

