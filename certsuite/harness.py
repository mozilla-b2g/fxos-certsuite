#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


import argparse
import json
import os
import pkg_resources
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from cStringIO import StringIO
from collections import OrderedDict
from datetime import datetime

import marionette
import mozdevice
import moznetwork
import mozprocess
import wptserve

from marionette import expected
from marionette.by import By
from marionette.wait import Wait
from marionette_extension import AlreadyInstalledException
from marionette_extension import install as marionette_install
from marionette_extension import uninstall as marionette_uninstall
from mozfile import TemporaryDirectory
from mozlog.structured import structuredlog, handlers, formatters, set_default_logger
from reportmanager import ReportManager
from logmanager import LogManager

import adb_b2g
import gaiautils
import report

logger = None
remove_marionette_after_run = False
stdio_handler = handlers.StreamHandler(sys.stderr,
                                       formatters.MachFormatter())
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.json"))


def setup_logging(log_manager):
    global logger
    log_f = log_manager.structured_file
    logger = structuredlog.StructuredLogger("firefox-os-cert-suite")
    logger.add_handler(stdio_handler)
    logger.add_handler(handlers.StreamHandler(log_f,
                                              formatters.JSONFormatter()))
    set_default_logger(logger)


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
            # There's no logger at this point in the code to log this as an exception
            print >> sys.stderr, "Failed to run command: %s: %s" % (" ".join(cmd), e)
            sys.exit(1)


def get_metadata():
    dist = pkg_resources.get_distribution("fxos-certsuite")
    return {"version": dist.version}

def log_metadata():
    metadata = get_metadata()
    for key in sorted(metadata.keys()):
        logger.info("fxos-certsuite %s: %s" % (key, metadata[key]))

# Consider upstreaming this to marionette-client:
class MarionetteSession(object):
    def __init__(self, device):
        self.device = device
        self.marionette = marionette.Marionette()

    def __enter__(self):
        self.device.forward("tcp:2828", "tcp:2828")
        self.marionette.wait_for_port()
        self.marionette.start_session()
        return self.marionette

    def __exit__(self, *args, **kwargs):
        if self.marionette.session is not None:
            self.marionette.delete_session()


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

    def run_suite(self, suite, groups, log_manager, report_manager):
        with TemporaryDirectory() as temp_dir:
            result_files, structured_path = self.run_test(suite, groups, temp_dir)

            report_manager.add_subsuite_report(structured_path, result_files)

    def run_test(self, suite, groups, temp_dir):
        logger.info('Running suite %s' % suite)

        def on_output(line):
            written = False
            if line.startswith("{"):
                try:
                    data = json.loads(line.strip())
                    if "action" in data:
                        sub_logger.log_raw(data)
                        written = True
                except ValueError:
                    pass
            if not written:
                logger.process_output(proc.pid,
                                      line.decode("utf8", "replace"),
                                      command=" ".join(cmd))

        try:
            cmd, output_files, structured_path = self.build_command(suite, groups, temp_dir)

            logger.debug(cmd)
            logger.debug(output_files)

            env = dict(os.environ)
            env['PYTHONUNBUFFERED'] = '1'
            proc = mozprocess.ProcessHandler(cmd, env=env, processOutputLine=on_output)
            logger.debug("Process '%s' is running" % " ".join(cmd))
            #TODO: move timeout handling to here instead of each test?
            with open(structured_path, "w") as structured_log:
                sub_logger = structuredlog.StructuredLogger(suite)
                sub_logger.add_handler(stdio_handler)
                sub_logger.add_handler(handlers.StreamHandler(structured_log,
                                                              formatters.JSONFormatter()))
                proc.run()
                proc.wait()
            logger.debug("Process finished")

        except Exception:
            logger.error("Error running suite %s:\n%s" % (suite, traceback.format_exc()))
            raise
        finally:
            try:
                proc.kill()
            except:
                pass

        return output_files, structured_path

    def build_command(self, suite, groups, temp_dir):
        suite_opts = self.config["suites"][suite]

        subn = self.config.copy()
        del subn["suites"]
        subn.update({"temp_dir": temp_dir})

        cmd = [suite_opts['cmd']]

        subtests = '' if groups == [] else '_' + "_".join(item.replace("/", "-") for item in groups)
        log_name = "%s/%s_structured%s.log" % (temp_dir, suite, subtests)
        cmd.extend(["--log-raw=-"])

        if groups:
            cmd.extend('--include=%s' % g for g in groups)

        cmd.extend(item % subn for item in suite_opts.get("run_args", []))
        cmd.extend(item % subn for item in suite_opts.get("common_args", []))

        output_files = [log_name]
        output_files += [item % subn for item in suite_opts.get("extra_files", [])]

        return cmd, output_files, log_name


def log_result(results, result):
    results[result.test_name] = {'status': 'PASS' if result.passed else 'FAIL',
                                 'failures': result.failures,
                                 'errors': result.errors}


def check_preconditions(config):
    check_marionette_installed = lambda device: install_marionette(device, config['version'])

    device = check_adb()
    if not device:
        sys.exit(1)

    for precondition in [check_root,
                         check_marionette_installed,
                         ensure_settings,
                         check_network,
                         check_server]:
        try:
            passed = precondition(device)
        except:
            logger.critical("Error during precondition check:\n%s" % traceback.format_exc())
            passed = False
        if not passed:
            device.reboot()
            sys.exit(1)

    logger.info("Passed precondition checks")


def check_adb():
    try:
        logger.info("Testing ADB connection")
        return adb_b2g.ADBB2G()
    except (mozdevice.ADBError, mozdevice.ADBTimeoutError) as e:
        logger.critical('Error connecting to device via adb (error: %s). Please be ' \
                        'sure device is connected and "remote debugging" is enabled.' % \
                        e.msg)
        return False


def check_root(device):
    have_adbd = False
    have_root = False
    processes = device.get_process_list()
    for pid, name, user in processes:
        if name == "/sbin/adbd":
            have_adbd = True
            have_root = user == "root"
            if not have_root:
                logger.critical("adbd running as non-root user %s" % user)
            break
    if not have_adbd:
        logger.critical("adbd process not found")
    return have_root


def install_marionette(device, version):
    try:
        logger.info("Installing marionette extension")
        try:
            marionette_install(version)
            global remove_marionette_after_run
            remove_marionette_after_run = True
        except AlreadyInstalledException:
            logger.info("Marionette is already installed")
    except subprocess.CalledProcessError:
        logger.critical(
            "Error installing marionette extension:\n%s" % traceback.format_exc())
        raise
    except subprocess.CalledProcessError as e:
        logger.critical('Error installing marionette extension: %s' % e)
        logger.critical(traceback.format_exc())
        return False
    except adb_b2g.WaitTimeout:
        logger.critical("Timed out waiting for device to become ready")
        return False
    device.restart()
    return True

def check_network(device):
    try:
        device.wait_for_net()
        return True
    except adb_b2g.WaitTimeout:
        logger.critical("Failed to get a network connection")
        return False


def ensure_settings(device):
    test_settings = {"screen.automatic-brightness": False,
                     "screen.brightness": 1.0,
                     "screen.timeout": 0.0}
    logger.info("Setting up device for testing")
    with MarionetteSession(device) as marionette:
        settings = gaiautils.Settings(marionette)
        for k, v in test_settings.iteritems():
            settings.set(k, v)
    return True

@wptserve.handlers.handler
def test_handler(request, response):
    return "PASS"


def wait_for_homescreen(marionette, timeout):
    logger.info("Waiting for home screen to load")
    # Wait for the homescreen to finish loading
    Wait(marionette, timeout).until(expected.element_present(
        By.CSS_SELECTOR, '#homescreen[loading-state=false]'))


def check_server(device):
    logger.info("Checking access to host machine")
    routes = [("GET", "/", test_handler)]

    host_ip = moznetwork.get_ip()

    for port in [8000, 8001]:
        try:
            server = wptserve.WebTestHttpd(host=host_ip, port=port, routes=routes)
            server.start()
        except:
            logger.critical("Error starting local server on port %s:\n%s" %
                            (port, traceback.format_exc()))
            return False

        try:
            device.shell_output("curl http://%s:%i" % (host_ip, port))
        except mozdevice.ADBError as e:
            if 'curl: not found' in e.message:
                logger.warning("Could not check access to host machine: curl not present.")
                logger.warning("If timeouts occur, check your network configuration.")
                break
            logger.critical("Failed to connect to server running on host machine ip %s port %i. Check network configuration." % (host_ip, port))
            return False
        finally:
            logger.debug("Stopping server")
            server.stop()

    return True


def list_tests(args, config):
    for test, group in iter_test_lists(config["suites"]):
        print "%s:%s" % (test, group)
    return True


def run_tests(args, config):
    error = False
    output_zipfile = None

    try:
        with LogManager() as log_manager, ReportManager() as report_manager:
            output_zipfile = log_manager.zip_path
            setup_logging(log_manager)
            report_manager.setup_report(log_manager.zip_file, log_manager.structured_path)

            log_metadata()

            check_preconditions(config)

            with adb_b2g.DeviceBackup() as backup:
                device = backup.device
                runner = TestRunner(args, config)
                try:
                    for suite, groups in runner.iter_suites():
                        try:
                            runner.run_suite(suite, groups, log_manager, report_manager)
                        except:
                            logger.error("Encountered error:\n%s" %
                                         traceback.format_exc())
                            error = True
                finally:
                    marionette_uninstall()
                    backup.restore()
                    device.reboot()

            if error:
                logger.critical("Encountered errors during run")
    except:
        error = True
        print "Encountered error at top level:\n%s" % traceback.format_exc()
    finally:
        if output_zipfile:
            print >> sys.stderr, "Results saved to %s" % output_zipfile

    return error


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
                        help='tests to run',
                        nargs='*')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = load_config(args.config)

    if args.list_tests:
        return list_tests(args, config)
    else:
        return run_tests(args, config)


if __name__ == '__main__':
    sys.exit(not main())
