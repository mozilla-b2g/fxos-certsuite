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
import shutil

from collections import OrderedDict
from mozfile import TemporaryDirectory
from mozlog.structured import structuredlog, reader, handlers, formatters

logger = None

def setup_logging(log_f):
    global logger
    logger = structuredlog.StructuredLogger("firefox-os-cert-suite")
    logger.add_handler(handlers.StreamHandler(sys.stderr,
                                              formatters.MachFormatter()))

    logger.add_handler(handlers.StreamHandler(log_f,
                                              formatters.JSONFormatter()))


def load_config(path):
    with open(path) as f:
        config = json.load(f)
    config["suites"] = OrderedDict(config["suites"])
    return config

def iter_test_lists(suites_config):
    '''
    Query each subharness for the list of test groups it can run and
    yield a tuple of (subharness, test group) for each one.
    '''
    for name, opts in suites_config.iteritems():
        try:
            cmd = [opts["cmd"], '--list-test-groups'] + opts.get("pos_args", [])
            for group in subprocess.check_output(cmd).splitlines():
                yield name, group
        except subprocess.CalledProcessError:
            print >> sys.stderr("Failed to run command %s" % " ".join(cmd))
            sys.exit(1)

class DeviceBackup(object):
    def __init__(self):
        self.device = mozdevice.DeviceManagerADB()
        self.backup_dirs = ["/data/local",
                            "/data/b2g/mozilla",
                            "/system/etc"]

    def local_dir(self, remote):
        return os.path.join(self.backup_path, remote.lstrip("/"))

    def __enter__(self):
        logger.info("Saving device state")
        self.backup_path = tempfile.mkdtemp()

        for remote in self.backup_dirs:
            local = self.local_dir(remote)
            self.device.getDirectory(remote, local)

        return self

    def __exit__(self, *args, **kwargs):
        shutil.rmtree(self.backup_path)

    def restore(self):
        logger.info("Restoring device state")
        for remote in self.backup_dirs:
            local = self.local_dir(remote)
            self.device.removeDir(remote)
            self.device.pushDir(local, remote)


class TestRunner(object):
    def __init__(self, args, config):
        self.args = args
        self.config = config

    def iter_suites(self):
        '''
        Iterate over test suites and groups of tests that are to be run. Returns
        tuples of the form (suite, [test_groups]) where suite is the name of a
        test suite and [test_groups] is a list of group names to run in that suite,
        or the empty list to indicate all tests.
        '''
        if not self.args.tests:
            tests = self.config["suites"].keys()
        else:
            tests = self.args.tests

        d = OrderedDict()
        for t in tests:
            v = t.split(":", 1)
            suite = v[0]
            if suite not in d:
                d[suite] = []

            if len(v) == 2:
                #TODO: verify tests passed against possible tests?
                d[suite].append(v[1])

        for suite, groups in d.iteritems():
            yield suite, groups

    def run_suite(self, suite, groups, output_zip):
        with TemporaryDirectory() as temp_dir:
            result_files = self.run_test(suite, groups, temp_dir)

            for path in result_files:
                file_name = os.path.split(path)[1]
                output_zip.write(path, "%s/%s" % (suite, file_name))

    def run_test(self, suite, groups, temp_dir):
        logger.info('Running suite %s' % suite)

        files = []

        try:
            cmd, output_files = self.build_command(suite, groups, temp_dir)

            logger.debug(cmd)
            logger.debug(output_files)

            env = dict(os.environ)
            env['PYTHONUNBUFFERED'] = '1'
            proc = mozprocess.ProcessHandler(cmd, env=env)
            logger.debug("Process '%s' is running" % " ".join(cmd))
            #TODO: move timeout handling to here instead of each test?
            proc.run()
            proc.wait()
            logger.debug("Process finished")

        except Exception as e:
            logger.critical("Error running suite %s:\n%s" %(suite, traceback.format_exc()))
            raise
        finally:
            try:
                proc.kill()
            except:
                pass

        return output_files

    def build_command(self, suite, groups, temp_dir):
        suite_opts = self.config["suites"][suite]

        subn = self.config.copy()
        del subn["suites"]
        subn.update({"temp_dir": temp_dir})

        cmd = [suite_opts['cmd']]
        cmd.extend(item % subn for item in suite_opts.get("args", []))

        log_name = "%s/%s_structured%s.log" % (temp_dir, suite, "_".join(item.replace("/", "-") for item in groups))
        cmd.extend(["--log-raw=%s" % log_name,
                    "--log-mach=-"])

        if groups:
            cmd.extend('--include=%s' % g for g in groups)

        cmd.extend(item % subn for item in suite_opts.get("pos_args", []))

        output_files = [log_name]
        output_files += [item % subn for item in suite_opts.get("extra_files", [])]

        return cmd, output_files

def log_result(results, result):
    results[result.test_name] = {
        'status': 'PASS' if result.passed else 'FAIL',
        'failures': result.failures,
        'errors': result.errors,
        }

def check_adb():
    try:
        logger.info("Testing ADB connection")
        dm = mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        logger.critical('Error connecting to device via adb (error: %s). Please be ' \
                        'sure device is connected and "remote debugging" is enabled.' % \
                        e.msg)
        sys.exit(1)

def install_marionette():
    try:
        logger.info("Installing marionette extension")
        marionette_extension.install()
    except subprocess.CalledProcessError, e:
        logger.critical('Error installing marionette extension: %s' % e)
        sys.exit(1)

def list_tests(args, config):
    print 'Tests available:'
    for test, group in iter_test_lists(config["suites"]):
        print "%s:%s" % (test, group)
    print '''To run a set of tests, pass those test names on the commandline, like:
runcertsuite suite1:test1 suite1:test2 suite2:test1 [...]'''
    return 0

def run_tests(args, config):
    output_zipfile = 'firefox-os-certification.zip'
    output_logfile = "run.log"
    error = False

    try:
        with zipfile.ZipFile(output_zipfile, 'w', zipfile.ZIP_DEFLATED) as zip_f:
            with open(output_logfile, "w") as log_f:
                setup_logging(log_f)

                check_adb()
                install_marionette()

                with DeviceBackup() as device:
                    runner = TestRunner(args, config)

                    for suite, groups in runner.iter_suites():
                        try:
                            runner.run_suite(suite, groups, zip_f)
                        except:
                            logger.critical("Encountered error:\n%s" % traceback.format_exc())
                            error = True
                        finally:
                            device.restore()

                if error:
                    logger.critical("Encountered errors during run")

            zip_f.write(output_logfile)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        error = True
        print "Encountered error at top level:\n%s" % traceback.format_exc()

    sys.stderr.write('Results saved in %s' % output_zipfile)

    return int(error)

def main():
    parser = get_parser()
    args = parser.parse_args()

    config = load_config(args.config)

    if args.list_tests:
        return list_tests(args, config)
    else:
        return run_tests(args, config)

def get_parser():
    parser = argparse.ArgumentParser()
    #TODO make this more robust
    parser.add_argument('--config',
                        help='Path to config file', type=os.path.abspath,
                        action='store', default='certsuite/config.json')
    parser.add_argument('--list-tests',
                        help='list all tests available to run',
                        action='store_true')
    parser.add_argument('tests',
                        metavar='TEST',
                        help='test to run (use --list-tests to see available tests)',
                        nargs='*')
    return parser

if __name__ == '__main__':
    sys.exit(main())
