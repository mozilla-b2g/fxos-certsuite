#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys
import unittest

from mozlog.structured import commandline

from webapi_tests.semiauto import TestLoader
from webapi_tests.semiauto import run


test_loader = None


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
    logger = commandline.setup_logging("webapi", args, {"mach": sys.stdout})

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
