#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import socket
import sys
import unittest

from mozlog.structured import formatters, handlers, structuredlog, commandline
from moztest.adapters.unit import StructuredTestRunner

from webapi_tests.semiauto import environment, runner, server
from webapi_tests.semiauto.loader import TestLoader

__all__ = ["run", "main"]


test_loader = None


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

        python -m semiauto discover .

    """

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

    tests = runner.serialize_suite(suite)
    test_runner = StructuredTestRunner(logger=logger, test_list=tests)

    # This is a hack to make the test suite metadata and the handler
    # available to the tests.
    so.suite = suite
    environment.env.handler = so

    try:
        results = test_runner.run(suite)
    except (SystemExit, KeyboardInterrupt) as e:
        sys.exit(1)

    return results


def get_parser():
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

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("-n", "--no-browser", action="store_true",
                        dest="no_browser", default=False, help="Don't "
                        "start a browser but wait for manual connection")
    parser.add_argument("-v", action="store_true", dest="verbose", default=False,
                        help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true",
                        dest="quiet", help="Minimal output")
    parser.add_argument("--failfast", "-f", action="store_true",
                        dest="failfast", help="Stop on first failure")
    parser.add_argument("--catch", "-c", action="store_true",
                        help="Catch C-c and display eresults")
    parser.add_argument("--buffer", "-b", action="store_true",
                        help="Buffer stdout and stderr during test runs")
    parser.add_argument("--pattern", "-p", dest="pattern",
                        help='Pattern to match tests ("test_*.py" default)')
    parser.add_argument("tests", nargs="*")

    commandline.add_logging_group(parser)
    return parser

def main(argv):
    parser = get_parser()
    args = parser.parse_args(argv[1:])
    logger = commandline.setup_logging("webapi", args, {"mach":sys.stdout})

    test_loader = TestLoader()

    tests = []

    if len(args.tests) >= 1 and args.tests[0] == "discover":
        start_dir = args.tests[1] if len(args.tests) > 1 else "."
        tests = test_loader.discover(start_dir, args.pattern or "test_*.py")
    else:
        tests = None
        if len(args.tests) > 0:
            tests = test_loader.loadTestsFromNames(args.tests, None)
        else:
            tests = unittest.TestSuite()

    results = run(tests,
                  spawn_browser=not args.no_browser,
                  verbosity=2 if args.verbose else 1,
                  failfast=args.failfast,
                  catch_break=args.catch,
                  buffer=args.buffer,
                  logger=logger)
    sys.exit(not results.wasSuccessful())
