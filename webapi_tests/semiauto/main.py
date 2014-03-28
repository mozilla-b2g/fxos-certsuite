#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import unittest

import environment
import runner


test_loader = None


def _install_test_event_hooks(test_runner, handler):
    state_updater = runner.TestStateUpdater(handler)
    test_runner.resultclass.add_callback(state_updater)


def run(suite, spawn_browser=True, verbosity=1, quiet=False,
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

    test_runner = runner.PreInstantiatedTestRunner(verbosity=verbosity,
                                                   failfast=failfast,
                                                   buffer=buffer,
                                                   **kwargs)

    delegator = runner.TestEventDelegator(
        test_runner.stream, test_runner.descriptions, test_runner.verbosity)
    test_runner.resultclass = delegator

    # Start new test environment, because first environment.get does
    # that for us the first time.
    #
    # This is a hack and shouldn't be here.  The reason it is is
    # because unittest doesn't allow us to modify the runner in a
    # TestCase's setUp.
    #
    # Generally a lot of this code should live in TestCase.setUp.
    env = environment.get(environment.InProcessTestEnvironment,
                          verbose=(verbosity > 1))

    # TODO(ato): Only spawn a browser when asked to.
    if spawn_browser:
        import webbrowser
        webbrowser.open("http://localhost:6666/")
    else:
        print("Please connect your browser to http://%s:%d/" %
              (env.server.addr[0], env.server.addr[1]))

    # Get a reference to the WebSocket handler that we can use to
    # communicate with the client browser.  This blocks until a client
    # connects.
    from semiauto import server
    # A timeout is needed because of http://bugs.python.org/issue1360
    handler = server.clients.get(block=True, timeout=sys.maxint)

    # Send list of tests to client.
    test_list = runner.serialize_suite(suite)
    handler.emit("testList", test_list)

    handler.suite = suite
    environment.env.handler = handler

    # Due to extent of how much unittest sucks, this is unfortunately
    # necessary:
    _install_test_event_hooks(test_runner, handler)

    try:
        results = test_runner.run(suite)
    except (SystemExit, KeyboardInterrupt) as e:
        sys.exit(1)

    return results


def main(argv):
    config = {}
    from semiauto.loader import TestLoader
    test_loader = TestLoader(config=config)
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
