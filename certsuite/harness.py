#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import mozprocess
import os
import sys

SUBTESTS = [
    'cert.py',
]

class TestResult:
    def __init__(self, passed, failures, errors):
        self.passed = passed
        self.failures = failures
        self.errors = errors

def run_test(test, args):
    print "test: %s" % test
    result = None
    try:
        proc = mozprocess.ProcessHandler([sys.executable, "-u", test,
                                          '--version=%s' % args.version])
        #TODO: move timeout handling to here instead of each test?
        proc.run()
        if proc.wait() == 0:
            #TODO: check for errors in the log
            result = TestResult(True, [], [])
        else:
            result = TestResult(False, ["TODO get failure"], [])
    except Exception, e:
        result = TestResult(False, [], [e])
        raise
    finally:
        if result is None:
            try:
                proc.kill()
            except:
                pass
    return result

def log_result(result):
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='version of Firefox OS under test',
                        default='1.3',
                        action='store')
    args = parser.parse_args()
    #TODO: check for device
    #TODO: install marionette

    for test in SUBTESTS:
        test_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 test))
        log_result(run_test(test_path, args))

if __name__ == '__main__':
    main()
