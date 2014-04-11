#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import marionette_extension
import mozdevice
import mozprocess
import os
import subprocess
import sys
import tempfile
import traceback
import zipfile

from collections import OrderedDict
from mozfile import TemporaryDirectory
from mozlog.structured import reader

SUBTESTS = OrderedDict([
    ('cert', None),
])

class TestResult:
    def __init__(self, test_name, passed, failures, errors, results_file):
        self.test_name = test_name
        self.passed = passed
        self.failures = failures
        self.errors = errors
        self.results_file = results_file

def get_test_failures(raw_log):
    '''
    Return the list of test failures contained within a structured log file.
    '''
    failures = []
    def test_status(data):
        if data['status'] == 'FAIL':
            failures.append(data)
    with open(raw_log, 'r') as f:
        reader.each_log(reader.read(f),
                               {'test_status':test_status})
    return failures

def list_tests():
    '''
    Query each subharness for the list of test groups it can run and
    yield a tuple of (subharness, test group) for each one.
    '''
    for test, _ in SUBTESTS.iteritems():
        try:
            for group in subprocess.check_output([test, '--list-test-groups']).splitlines():
                yield test, group
        except subprocess.CalledProcessError:
            pass

def filter_tests(tests):
    '''
    Given a list of tests from the commandline, yield triples of
    (subsuite, options, test groups) of subsuites to run and the
    test groups to run within them. If test groups is an empty list,
    all tests in the subsuite should be run.
    '''
    if not tests:
        tests = SUBTESTS.keys()
    d = OrderedDict()
    for t in tests:
        v = t.split(":", 1)
        subsuite = v[0]
        if subsuite not in d:
            d[subsuite] = []
        if len(v) == 2:
            #TODO: verify tests passed against possible tests?
            d[subsuite].append(v[1])
    for subsuite, test_groups in d.iteritems():
        yield subsuite, SUBTESTS[subsuite], test_groups

def run_test(test_name, temp_dir, args, test_groups):
    print 'Running %s' % test_name
    result = None
    try:
        raw_log = os.path.join(temp_dir, 'structured.log')
        result_file = os.path.join(temp_dir, 'results.json')
        cmd = [test_name,
               '--version=%s' % args.version,
               '--log-raw=%s' % raw_log,
               '--result-file=%s' % result_file,
               ]
        if test_groups:
            cmd.extend('--include=%s' % g for g in test_groups)
        if args.no_reboot:
            cmd.append('--no-reboot')
        env = dict(os.environ)
        env['PYTHONUNBUFFERED'] = '1'
        proc = mozprocess.ProcessHandler(cmd, env=env)
        #TODO: move timeout handling to here instead of each test?
        proc.run()
        passed = proc.wait() == 0
        failures = get_test_failures(raw_log)
        if failures:
            passed = False
        #TODO: check for errors in the log
        result = TestResult(test_name, passed, failures, [], result_file)
    except Exception as e:
        result = TestResult(test_name, False, [], [traceback.format_exc()], result_file)
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

def check_adb():
    try:
        dm = mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        print 'Error connecting to device via adb (error: %s). Please be ' \
            'sure device is connected and "remote debugging" is enabled.' % \
            e.msg
        sys.exit(1)

def install_marionette(os_version):
    try:
        marionette_extension.install()
    except subprocess.CalledProcessError, e:
        print 'Error installing marionette extension: %s' % e
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='version of Firefox OS under test',
                        default='1.3',
                        action='store')
    parser.add_argument('--no-reboot',
                        help='don\'t reboot device before running test',
                        action='store_true')
    parser.add_argument('--list-tests',
                        help='list all tests available to run',
                        action='store_true')
    parser.add_argument('tests',
                        metavar='TEST',
                        help='test to run (use --list-tests to see available tests)',
                        nargs='*')
    args = parser.parse_args()

    if args.list_tests:
        print 'Tests available:'
        for test, group in list_tests():
            print "%s:%s" % (test, group)
        print '''To run a set of tests, pass those test names on the commandline, like:
    runcertsuite suite1:test1 suite1:test2 suite2:test1 [...]'''
        return 0

    check_adb()
    install_marionette(args.version)

    results = {}
    output_zipfile = 'firefox-os-certification.zip'
    with zipfile.ZipFile(output_zipfile, 'w', zipfile.ZIP_DEFLATED) as f:
        for test, test_opts, test_groups in filter_tests(args.tests):
            with TemporaryDirectory() as temp_dir:
                result = run_test(test, temp_dir, args, test_groups)
                log_result(results, result)
                if result.results_file and os.path.exists(result.results_file):
                    f.write(result.results_file, '%s_results.json' % result.test_name)
        f.writestr('certsuite-results.json', json.dumps(results))
    print 'Results saved in %s' % output_zipfile

if __name__ == '__main__':
    main()
