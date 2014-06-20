Test Coverage
=============

web-platform-tests
~~~~~~~~~~~~~~~~~~

Tests from the W3C's web-platform-tests testsuite covering
standardised, web-exposed, platform features. These tests work by
loading HTML documents in a simple test application and using
javascript to determine the test result. Tests are divided
into groups — i.e. directories — according to the specification that
they are testing. The upstream testsuite is undergoing continual
development and it is not expected that we pass all tests; instead
correctness for the purposes of the certsuite is determined by
comparison to a reference run. At present the following tests groups
are enabled:

 * dom - Tests for the dom core specification

 * IndexedDB - Tests for the IndexedDB specification

 * touch_events - Simple tests for the automatically verifiable parts
   of the touch events specification
