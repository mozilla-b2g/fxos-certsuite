#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import importlib
import inspect
import os
import sys
import json

from fnmatch import fnmatch

from mozdevice import DeviceManagerADB
from mozlog.structured import commandline

from mcts.webapi_tests import semiauto
from mcts.webapi_tests.semiauto import environment

def iter_tests(start_dir, pattern="test_*.py"):
    """List available Web API tests and yield a tuple of (group, tests),
    where tests is a list of test names."""

    start_dir = os.path.abspath(start_dir)
    visited = set()

    for root, dirs, files in os.walk(start_dir, followlinks=True):
        if root in visited:
            raise ImportError("Recursive symlink: %r" % root)
        visited.add(root)

        group = os.path.relpath(root, start_dir)

        tests = []
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            if not fnmatch(file, pattern) or not os.path.exists(path):
                continue

            relpath = os.path.relpath(path, start_dir)
            if relpath.endswith(".py"):
                relpath = relpath[:-3]
            name = "mcts.webapi_tests.%s" % relpath.replace(os.path.sep, ".")
            module = None
            try:
                module = importlib.import_module(name)
            except ImportError:
                # Module has import problems which shouldn't affect listing
                # tests
                # print "WebAPI module ImportError: %s" % name
                continue

            members = inspect.getmembers(module)
            ts = [t for t in zip(*members)[1] if isinstance(t, type)]

            for cls in ts:
                if not issubclass(cls, semiauto.testcase.TestCase):
                    continue

                if getattr(cls, "__module__", None) != name:
                    continue
                tests.extend(
                    [member[0] for member in inspect.getmembers(cls) if member[0].startswith("test_")])

        if len(tests) > 0:
            yield group, tests


def main():
    parser = argparse.ArgumentParser(
        description="Runner for guided Web API tests.")
    parser.add_argument("-l", "--list-test-groups", action="store_true",
                        help="List all logical test groups")
    parser.add_argument("-a", "--list-all-tests", action="store_true",
                        help="List all tests")
    parser.add_argument("-i", "--include", metavar="GROUP", action="append", default=[],
                        help="Only include specified group(s) in run, include several "
                        "groups by repeating flag")
    parser.add_argument("-n", "--no-browser", action="store_true",
                        help="Don't start a browser but wait for manual connection")
    parser.add_argument("--version", action="store", dest="version",
                        help="B2G version")
    parser.add_argument('-H', '--host',
                        help='Hostname or ip for target device',
                        action='store', default='localhost')
    parser.add_argument('-P', '--port',
                        help='Port for target device',
                        action='store', default=2828)
    parser.add_argument('-p', "--device-profile", action="store",  type=os.path.abspath,
                        help="specify the device profile file path which could include skipped test case information")
    parser.add_argument(
        "-v", dest="verbose", action="store_true", help="Verbose output")
    commandline.add_logging_group(parser)
    args = parser.parse_args(sys.argv[1:])
    logger = commandline.setup_logging(
        "webapi", vars(args), {"raw": sys.stdout})

    if args.list_test_groups and len(args.include) > 0:
        print >> sys.stderr("%s: error: cannot list and include test "
                            "groups at the same time" % sys.argv[0])
        parser.print_usage()
        sys.exit(1)

    testgen = iter_tests(os.path.dirname(__file__))
    if args.list_test_groups:
        for group, _ in testgen:
            print(group)
        return 0
    elif args.list_all_tests:
        for group, tests in testgen:
            for test in tests:
                print("%s.%s" % (group, test))
        return 0

    semiauto.testcase._host = args.host
    semiauto.testcase._port = int(args.port)

    env = environment.get(environment.InProcessTestEnvironment)
    environment.env.device_profile = None
    if args.device_profile:
        with open(args.device_profile, 'r') as device_profile_file:
            environment.env.device_profile = json.load(device_profile_file)['result']

    test_loader = semiauto.TestLoader(version=args.version)
    tests = test_loader.loadTestsFromNames(
        map(lambda t: "mcts.webapi_tests.%s" % t, args.include or [g for g, _ in testgen]), None)
    results = semiauto.run(tests,
                           logger=logger,
                           spawn_browser=not args.no_browser,
                           verbosity=2 if args.verbose else 1)
    return 0 if results.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
