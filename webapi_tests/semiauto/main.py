#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import unittest

import environment
import runner

from mozlog.structured import formatters, handlers, structuredlog
from moztest.adapters.unit import StructuredTestRunner

from semiauto import server


test_loader = None


def _create_logger():
    logger = structuredlog.StructuredLogger("unknown")
    logger.add_handler(
        handlers.StreamHandler(sys.stdout, formatters.JSONFormatter()))
    return logger


def run(suite, logger=None, spawn_browser=True, verbosity=1, quiet=False,
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

        python -m semiauto discover .

    """

    if catch_break:
        import unittest.signals
        unittest.signals.installHandler()

    if not logger:
        logger = _create_logger()

    env = environment.get(environment.InProcessTestEnvironment,
                          verbose=(verbosity > 1))

    if spawn_browser:
        import webbrowser
        webbrowser.open("http://localhost:6666/")
    else:
        print >> sys.stderr, "Please connect your browser to http://%s:%d/" % \
            (env.server.addr[0], env.server.addr[1])

    # Wait for browser to connect and get socket connection to client
    so = server.wait_for_client()

    test_runner = StructuredTestRunner(logger=logger)
    test_list = runner.serialize_suite(suite)
    so.emit("testList", test_list)

    # This is a hack to make the test suite metadata and the handler
    # available to the tests.
    so.suite = suite
    environment.env.handler = so

    logger.add_handler(runner.WSHandler(so))

    so.emit("testRunStart")
    try:
        results = test_runner.run(suite)
    except (SystemExit, KeyboardInterrupt) as e:
        sys.exit(1)
    so.emit("testRunStop")

    return results


def main(argv):
    from semiauto.loader import TestLoader
    test_loader = TestLoader()
    prog = "python -m semiauto"
    indent = " " * len(prog)
    usage = """\
usage: %s [-h|--help] [-v|--verbose] [-q|--quiet]
%s [-f|--failfast] [-c|--catch] [-b|--buffer]
%s [TEST...|discover DIRECTORY [-p|--pattern]]

TEST can be a list of any number of test modules, classes, and test
modules.

The magic keyword "discover" can be used to autodetect tests according
to various criteria. By default it will start looking recursively for
tests in the current working directory (".").\
""" % (prog, indent, indent)

    import optparse
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-n", "--no-browser", action="store_true",
                      dest="no_browser", default=False, help="Don't "
                      "start a browser but wait for manual connection")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False,
                      help="Verbose output")
    parser.add_option("-q", "--quiet", action="store_true",
                      dest="quiet", help="Minimal output")
    parser.add_option("--failfast", "-f", action="store_true",
                      dest="failfast", help="Stop on first failure")
    parser.add_option("--catch", "-c", action="store_true",
                      help="Catch C-c and display eresults")
    parser.add_option("--buffer", "-b", action="store_true",
                      help="Buffer stdout and stderr during test runs")
    parser.add_option("--pattern", "-p", dest="pattern",
                      help='Pattern to match tests ("test_*.py" default)')
    parser.add_option("--reuse-browser", dest="reuse_browser",
                      help="Reuse an existing browser session.")

    opts, args = parser.parse_args(argv[1:])
    tests = []

    if len(args) >= 1 and args[0] == "discover":
        start_dir = args[1] if len(args) > 1 else "."
        tests = test_loader.discover(start_dir, opts.pattern or "test_*.py")
    else:
        tests = None
        if len(args) > 0:
            test_names = args
            tests = test_loader.loadTestsFromNames(test_names, None)
        else:
            tests = unittest.TestSuite()

    results = run(tests,
                  spawn_browser=not opts.no_browser,
                  verbosity=2 if opts.verbose else 1,
                  failfast=opts.failfast,
                  catch_break=opts.catch,
                  buffer=opts.buffer)
    sys.exit(not results.wasSuccessful())
