# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import sys
import unittest

from moztest.adapters.unit import StructuredTestRunner

from webapi_tests.semiauto import environment, server


def run(suite, logger, spawn_browser=True, verbosity=1, quiet=False,
        failfast=False, catch_break=False, buffer=True, **kwargs):
    """A simple test runner.

    This test runner is essentially equivalent to ``unittest.main``
    from the standard library, but adds support for loading test
    classes with extra keyword arguments.

    The easiest way to run a test is via the command line::

        python -m semiauto test_sms

    See the standard library unittest module for ways in which tests
    can be specified.

    For example it is possible to automatically discover tests::

        python -m semiauto discover ."""
    if catch_break:
        import unittest.signals
        unittest.signals.installHandler()

    env = environment.get(environment.InProcessTestEnvironment,
                          addr=None if spawn_browser else ("127.0.0.1", 6666),
                          verbose=(verbosity > 1))

    url = "http://%s:%d/" % (env.server.addr[0], env.server.addr[1])
    if spawn_browser:
        import webbrowser
        webbrowser.open(url)
    else:
        print >> sys.stderr, "Please connect your browser to %s" % url

    # Wait for browser to connect and get socket connection to client
    try:
        so = server.wait_for_client()
    except server.ConnectError as e:
        logger.error("%s: error: %s" % (sys.argv[0], e))
        sys.exit(1)

    tests = serialize_suite(suite)
    test_runner = StructuredTestRunner(logger=logger, test_list=tests)

    # This is a hack to make the test suite metadata and the handler
    # available to the tests.
    so.suite = suite
    environment.env.handler = so

    logger.suite_start(tests=tests)
    try:
        results = test_runner.run(suite)
    except (SystemExit, KeyboardInterrupt) as e:
        sys.exit(1)
    logger.suite_end()

    return results


def serialize_suite(tests, ov=[]):
    """Serialize a ``unittest.TestSuite`` instance for transportation
    across the wire.

    Tests are represented by their hash as we have no desire to
    replicate the full Test instance object on the client side.

    :param tests: Instance of ``unittest.suite.TestSuite`` to be
        serialized.

    :returns: List of test dicts represented by `id` and
        `description`.

    """

    rv = ov
    if isinstance(tests, collections.Iterable):
        # [TestCase, ...] or [<TestSuite ...>, <TestSuite ...>]
        for test in tests:
            if isinstance(test, unittest.suite.TestSuite):
                rv = serialize_suite(test, rv)
            else:
                rv.append(test.id())
    elif hasattr(tests, "_tests"):
        # <unittest.suite.TestSuite _tests=[...]>
        rv = serialize_suite(tests._tests, rv)

    return rv
