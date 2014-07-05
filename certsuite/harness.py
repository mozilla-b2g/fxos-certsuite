#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
from marionette_extension import install as marionette_install
from marionette_extension import AlreadyInstalledException
import mozdevice
import mozprocess
import os
import pkg_resources
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile

from collections import OrderedDict
from datetime import datetime
from mozfile import TemporaryDirectory
from mozlog.structured import structuredlog, handlers, formatters

import report

logger = None
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.json"))


def setup_logging(log_manager):
    global logger
    log_f = log_manager.structured_file
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
            cmd = [opts["cmd"], '--list-test-groups'] + opts.get("common_args", [])
            for group in subprocess.check_output(cmd).splitlines():
                yield name, group
        except (subprocess.CalledProcessError, OSError) as e:
            print >> sys.stderr, "Failed to run command: %s: %s" % (" ".join(cmd), e)
            sys.exit(1)


def get_metadata():
    dist = pkg_resources.get_distribution("fxos-certsuite")
    return {"version": dist.version}

def log_metadata():
    metadata = get_metadata()
    for key in sorted(metadata.keys()):
        logger.info("fxos-certsuite %s: %s" % (key, metadata[key]))

class LogManager(object):
    def __init__(self):
        self.time = datetime.now()
        self.structured_path = "run.log"
        self.zip_path = 'firefox-os-certification_%s.zip' % (time.strftime("%Y%m%d%H%M%S"))
        self.structured_file = None
        self.subsuite_results = []

    def add_file(self, path, file_obj):
        self.zip_file.write(path, file_obj)

    def add_subsuite_report(self, path):
        results = report.parse_log(path)
        self.subsuite_results.append(results)
        if not results.is_pass:
            html_str = report.subsuite.make_report(results)
            path = "%s/report.html" % results.name
        self.zip_file.writestr(path, html_str)

    def add_summary_report(self, path):
        summary_results = report.parse_log(path)
        html_str = report.summary.make_report(self.time,
                                              summary_results,
                                              self.subsuite_results)
        path = "report.html"
        self.zip_file.writestr(path, html_str)

    def __enter__(self):
        self.zip_file = zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED)
        self.structured_file = open(self.structured_path, "w")
        return self

    def __exit__(self, *args, **kwargs):
        try:
            self.structured_file.__exit__(*args, **kwargs)
            self.zip_file.write(self.structured_path)
            self.add_summary_report(self.structured_path)
        finally:
            try:
                os.unlink(self.structured_path)
            finally:
                self.zip_file.__exit__(*args, **kwargs)

class DeviceBackup(object):
    def __init__(self):
        self.device = mozdevice.DeviceManagerADB()
        self.backup_dirs = ["/data/local",
                            "/data/b2g/mozilla"]
        self.backup_files = ["/system/etc/hosts"]

    def local_dir(self, remote):
        return os.path.join(self.backup_path, remote.lstrip("/"))

    def __enter__(self):
        logger.info("Saving device state")
        self.backup_path = tempfile.mkdtemp()

        for remote_path in self.backup_dirs:
            local_path = self.local_dir(remote_path)
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            self.device.getDirectory(remote_path, local_path)

        for remote_path in self.backup_files:
            remote_dir, filename = remote_path.rsplit("/", 1)
            local_dir = self.local_dir(remote_dir)
            local_path = os.path.join(local_dir, filename)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            self.device.getFile(remote_path, local_path)

        return self

    def __exit__(self, *args, **kwargs):
        shutil.rmtree(self.backup_path)

    def restore(self):
        logger.info("Restoring device state")
        self.device.remount()

        for remote_path in self.backup_files:
            remote_dir, filename = remote_path.rsplit("/", 1)
            local_path = os.path.join(self.local_dir(remote_dir), filename)
            self.device.removeFile(remote_path)
            self.device.pushFile(local_path, remote_path)

        for remote_path in self.backup_dirs:
            local_path = self.local_dir(remote_path)
            self.device.removeDir(remote_path)
            self.device.pushDir(local_path, remote_path)

        self.device.reboot(wait=True)


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

    def run_suite(self, suite, groups, log_manager):
        with TemporaryDirectory() as temp_dir:
            result_files, structured_path = self.run_test(suite, groups, temp_dir)

            for path in result_files:
                file_name = os.path.split(path)[1]
                log_manager.add_file(path, "%s/%s" % (suite, file_name))

            log_manager.add_subsuite_report(structured_path)

    def run_test(self, suite, groups, temp_dir):
        logger.info('Running suite %s' % suite)

        failures = []
        try:
            cmd, output_files, structured_log = self.build_command(suite, groups, temp_dir)

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

        except Exception:
            logger.critical("Error running suite %s:\n%s" %(suite, traceback.format_exc()))
            raise
        finally:
            try:
                proc.kill()
            except:
                pass

        return output_files, structured_log

    def build_command(self, suite, groups, temp_dir):
        suite_opts = self.config["suites"][suite]

        subn = self.config.copy()
        del subn["suites"]
        subn.update({"temp_dir": temp_dir})

        cmd = [suite_opts['cmd']]

        log_name = "%s/%s_structured%s.log" % (temp_dir, suite, "_".join(item.replace("/", "-") for item in groups))
        cmd.extend(["--log-raw=%s" % log_name,
                    "--log-mach=-"])

        if groups:
            cmd.extend('--include=%s' % g for g in groups)

        cmd.extend(item % subn for item in suite_opts.get("run_args", []))
        cmd.extend(item % subn for item in suite_opts.get("common_args", []))

        output_files = [log_name]
        output_files += [item % subn for item in suite_opts.get("extra_files", [])]

        return cmd, output_files, log_name

def log_result(results, result):
    results[result.test_name] = {
        'status': 'PASS' if result.passed else 'FAIL',
        'failures': result.failures,
        'errors': result.errors,
        }

def check_adb():
    try:
        logger.info("Testing ADB connection")
        mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        logger.critical('Error connecting to device via adb (error: %s). Please be ' \
                        'sure device is connected and "remote debugging" is enabled.' % \
                        e.msg)
        sys.exit(1)

def install_marionette(version):
    try:
        logger.info("Installing marionette extension")
        try:
            marionette_install(version)
        except AlreadyInstalledException:
            logger.info("Marionette is already installed")
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
    error = False
    output_zipfile = None

    try:
        with LogManager() as log_manager:
            output_zipfile = log_manager.zip_path
            setup_logging(log_manager)

            log_metadata()
            check_adb()
            install_marionette(config['version'])

            with DeviceBackup() as device:
                runner = TestRunner(args, config)

                for suite, groups in runner.iter_suites():
                    try:
                        runner.run_suite(suite, groups, log_manager)
                    except:
                        logger.critical("Encountered error:\n%s" % traceback.format_exc())
                        error = True
                    finally:
                        device.restore()

            if error:
                logger.critical("Encountered errors during run")

    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        error = True
        print "Encountered error at top level:\n%s" % traceback.format_exc()

    if output_zipfile:
        sys.stderr.write('Results saved in %s\n' % output_zipfile)

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
                        action='store', default=config_path)
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
