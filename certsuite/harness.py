#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import mozdevice
import mozprocess
import os
import sys
import tempfile
import zipfile

from mozfile import TemporaryDirectory
from mozlog.structured import reader

SUBTESTS = [
    'cert.py',
]

class TestResult:
    def __init__(self, test_name, passed, failures, errors, results_file):
        self.test_name = test_name
        self.passed = passed
        self.failures = failures
        self.errors = errors
        self.results_file = results_file

def get_test_failures(raw_log):
    """
    Return the list of test failures contained within a structured log file.
    """
    failures = []
    def test_status(data):
        if data['status'] == 'FAIL':
            failures.append(data)
    with open(raw_log, 'r') as f:
        #XXX: bug 985606: map_action is a generator
        list(reader.map_action(reader.read(f),
                               {"test_status":test_status}))
    return failures

def run_test(test, temp_dir, args):
    print "Running %s" % test
    result = None
    test_name = os.path.splitext(os.path.basename(test))[0]
    try:
        raw_log = os.path.join(temp_dir, "structured.log")
        result_file = os.path.join(temp_dir, "results.json")
        cmd = [sys.executable, "-u", test,
               '--version=%s' % args.version,
               '--log-raw=%s' % raw_log,
               '--result-file=%s' % result_file,
               ]
        if args.no_reboot:
            cmd.append('--no-reboot')
        proc = mozprocess.ProcessHandler(cmd)
        #TODO: move timeout handling to here instead of each test?
        proc.run()
        passed = proc.wait() == 0
        failures = get_test_failures(raw_log)
        if failures:
            passed = False
        #TODO: check for errors in the log
        result = TestResult(test_name, passed, failures, [], result_file)
    except Exception as e:
        result = TestResult(test_name, False, [], [e], result_file)
    finally:
        if result is None:
            try:
                proc.kill()
            except:
                pass
    return result

def log_result(results, result):
    results[result.test_name] = {
        'status': 'PASS' if result.passed else 'FAIL',
        'failures': result.failures,
        'errors': result.errors,
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='version of Firefox OS under test',
                        default='1.3',
                        action='store')
    parser.add_argument("--no-reboot",
                        help="don't reboot device before running test",
                        action="store_true")
    args = parser.parse_args()
    try:
        dm = mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        print "Error connecting to device via adb (error: %s). Please be " \
            "sure device is connected and 'remote debugging' is enabled." % \
            e.msg
        sys.exit(1)
    #TODO: install marionette

    results = {}
    output_zipfile = 'firefox-os-certification.zip'
    with zipfile.ZipFile(output_zipfile, 'w', zipfile.ZIP_DEFLATED) as f:
        for test in SUBTESTS:
            with TemporaryDirectory() as temp_dir:
                test_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                         test))
                result = run_test(test_path, temp_dir, args)
                log_result(results, result)
                if result.results_file and os.path.exists(result.results_file):
                    f.write(result.results_file, '%s_results.json' % result.test_name)
        f.writestr('certsuite-results.json', json.dumps(results))
    print 'Results saved in %s' % output_zipfile

if __name__ == '__main__':
    main()
