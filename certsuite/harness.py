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
import webbrowser
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
from webapi_tests.semiauto import environment, server

from reportmanager import ReportManager
from logmanager import LogManager

from report.results import KEY_MAIN

import adb_b2g
import gaiautils
import report

DeviceBackup = adb_b2g.DeviceBackup
_adbflag = False
_host = 'localhost'
_port = 2828
logger = None
remove_marionette_after_run = False
stdio_handler = handlers.StreamHandler(sys.stderr,
                                       formatters.MachFormatter())
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.json"))

retry_path = 'retry.json'

def setup_logging(log_f):
    global logger
    logger = structuredlog.StructuredLogger("firefox-os-cert-suite")
    logger.add_handler(stdio_handler)
    logger.add_handler(handlers.StreamHandler(log_f,
                                              formatters.JSONFormatter()))
    set_default_logger(logger)


def load_config(path):
    with open(path) as f:
        config = json.load(f)

    if sys.platform == 'win32':
        config_str = json.dumps(config)
        config_str.replace('/', os.sep)
        config = json.loads(config_str)
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
        global _host
        global _port
        self.device = device
        self.marionette = marionette.Marionette(host=_host, port=_port)

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
        self.retry = self.loadretry()
        self.regressions = []

    def loadretry(self):
        if not self.args.retry_failed:
            return False

        if not os.path.exists(retry_path):
            return False

        retrys = None
        try:
            with open(retry_path, 'r') as f:
                retrys = json.load(f)
        except:
            pass

        return retrys

    def iter_suites(self):
        '''
        Iterate over test suites and groups of tests that are to be run. Returns
        tuples of the form (suite, [test_groups]) where suite is the name of a
        test suite and [test_groups] is a list of group names to run in that suite,
        or the empty list to indicate all tests.
        '''
        if self.retry:
            tests = self.retry
        elif not self.args.tests:
            default_tests = self.config["suites"].keys()

            # stingray only test 'webapi' part
            if args.mode == 'stingray':
                default_tests = [default_tests['webapi']]

            tests = default_tests
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

    def test_string(self, test_id):
        if isinstance(test_id, unicode):
            return test_id
        else:
            return " ".join(test_id)

    def get_test_name(self, test, test_data):
        test_name = self.test_string(test)
        if len(test_data) == 1 and KEY_MAIN in test_data.keys():
            start_index = test_name.find('.') + 1
            end_index = test_name.find('.', start_index)
            test_name = test_name[start_index:end_index]
        return test_name

    def generate_retry(self):
        test_map = {'certsuite' : 'cert',
                    'webapi' : 'webapi',
                    'web-platform-tests':'web-platform-tests'}

        failed = []
        for regressions in self.regressions:
            if not regressions:
                continue
            tests = sorted(regressions.keys())
            for i, test in enumerate(tests):
                test_data = regressions[test]
                for subtest in sorted(test_data.keys()):
                    subtest_data = test_data[subtest]
                    subsuite = self.get_test_name(test, test_data)
                    if subtest_data["status"] == 'FAIL':
                        failed.append("%s:%s" %
                            (test_map[subtest_data['source']], subsuite))
                        break
        try:
            if failed:
                with open(retry_path, 'w') as f:
                    json.dump(failed, f)
        except:
            logger.error("Error generate retry.json file : %s" % traceback.format_exc())

    def run_suite(self, suite, groups, log_manager, report_manager):
        with TemporaryDirectory() as temp_dir:
            result_files, structured_path = self.run_test(suite, groups, temp_dir)

            self.regressions.append(report_manager.add_subsuite_report(structured_path, result_files))

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
        log_name = os.sep.join([temp_dir,"%s_structured%s.log" % (suite, subtests)])
        cmd.extend(["--log-raw=-"])

        if groups:
            cmd.extend('--include=%s' % g for g in groups)

        cmd.extend(item % subn for item in suite_opts.get("run_args", []))
        cmd.extend(item % subn for item in suite_opts.get("common_args", []))

        if self.args.debug and suite == 'webapi':
            cmd.append('-v')
        if self.args.debug and suite == 'cert':
            cmd.append('--debug')

        if suite == 'webapi' or suite == 'cert':
            cmd.append('--device-profile')
            cmd.append(self.args.device_profile)

        output_files = [log_name]
        output_files += [item % subn for item in suite_opts.get("extra_files", [])]

        cmd.extend([u'--host=%s' % _host, u'--port=%s' % _port])

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

class NoADBDeviceBackup():
    def __enter__(self):
        self.device = NoADB()
        return self
    def __exit__(self, *args, **kwargs):
        pass

class NoADB():
    def reboot(self):
        pass
    def wait_for_net(self):
        pass
    def shell_output(self):
        pass
    def forward(self, *args):
        pass
    def get_process_list(self):
        return [[1447, '/sbin/adbd', 'root']]
    def restart(self):
        pass

def check_adb():
    try:
        logger.info("Testing ADB connection")
        if _adbflag:
            logger.debug('Dummy ADB, please remember install Marionette and Cert Test App to device ')
            return NoADB()
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
    if _adbflag:
        logger.debug('The marionette should be installed manually by user.')
        return True
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

    if _adbflag:
        return True

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

def edit_device_profile(device_profile_path, message):
    resp = ''
    result = None
    try:
        env = environment.get(environment.InProcessTestEnvironment)
        url = "http://%s:%d/profile.html" % (env.server.addr[0], env.server.addr[1])
        webbrowser.open(url)
        environment.env.handler = server.wait_for_client()

        resp = environment.env.handler.prompt(message)

        message = 'Create device profile failed!!'
        if resp:
            result = json.loads(resp)
            if result['return'] == 'ok':
                with open(device_profile_path, 'w') as device_profile_f:
                    json.dump(result, device_profile_f, indent=4)
                message = 'Create device profile successfully!!'
            else:
                message = 'Create device profile is cancelled by user!!'
        else:
            message = ''
        logger.info(message)
    except:
        logger.error("Failed create device profile:\n%s" % traceback.format_exc())

    return result

def load_device_profile(device_profile_path):
    device_profile_object = None
    try:
        with open(device_profile_path, 'r') as device_profile_file:
            device_profile_object = json.load(device_profile_file)
            if not 'result' in device_profile_object:
                logger.error('Invalide device profile file [%s]' % device_profile_path)
                device_profile_object = None
            elif not 'contact' in device_profile_object['result']:
                    logger.error('Invalide device profile file [%s]' % device_profile_path)
                    device_profile_object = None
    except:
        logger.critical("Encountered error at checking device profile file [%s]:\n%s" % (device_profile_path, traceback.format_exc()))
        device_profile_object = None
    finally:
        return device_profile_object

def prepare_device_profile(edit_profile, profile_path, suites):
    profile_object = {'return': 'cancel'}

    if os.path.exists(profile_path):
        profile_object = load_device_profile(profile_path)
        logger.debug('load profile from [%s]' % profile_path)
        if not profile_object:
            edit_profile = True
    else:
        edit_profile = True

    if edit_profile:
        # create profile information to be displayed in profile.html
        profile_data = {}
        for test, group in iter_test_lists(suites):
            if test not in profile_data.keys():
                profile_data[test] = []
            profile_data[test].append({
                'id': group,
                'checked': True,
                'hidden': False
            })

        if profile_object is not None and profile_object['return'] == 'ok':
            # mark unchecked for those loaded from profile to skip
            for test in profile_data.keys():
                for i in range(len(profile_data[test])):
                    if profile_data[test][i]['id'] in profile_object['result'][test]:
                        profile_data[test][i]['checked'] = False

            # other profile datas are list, but profile_data['contact'] is map
            profile_data['contact'] = profile_object['result']['contact']

        message = json.dumps(profile_data)
        logger.debug('device profile message to tonado server:\n\t%s' % message)

        result = edit_device_profile(profile_path, message)
        logger.debug('User input profile information :\n\t%s' % json.dumps(result))
        if result:
            profile_object = result

    return profile_object

def run_tests(args, config):
    error = False
    output_zipfile = None

    try:
        with LogManager() as log_manager, ReportManager() as report_manager:
            output_zipfile = log_manager.zip_path
            setup_logging(log_manager.structured_file)

            config['profile'] = prepare_device_profile( args.edit_device_profile,
                                                        args.device_profile,
                                                        config['suites'])

            report_manager.setup_report(args.device_profile, log_manager.zip_file, log_manager.structured_path)

            log_metadata()

            check_preconditions(config)

            with DeviceBackup() as backup:
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
                    runner.generate_retry()
                    if remove_marionette_after_run:
                        marionette_uninstall()
                    backup.restore()
                    if not args.debug:
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
    parser.add_argument('-c', '--config',
                        help='Path to config file', type=os.path.abspath,
                        action='store', default=config_path)
    parser.add_argument('-d', '--debug',
                        help='Enable debug',
                        action='store_true')
    parser.add_argument('-e', '--edit-device-profile',
                        help='Edit the device profile',
                        action='store_true', default=False)
    parser.add_argument('-p', '--device-profile',
                        help='Path to device profile file', type=os.path.abspath,
                        action='store', default='device_profile.json')
    parser.add_argument('-l', '--list-tests',
                        help='List all tests available to run',
                        action='store_true')
    parser.add_argument('-r', '--retry-failed',
                        help='Retry last failed tests to run(IGNORE any tests parameters)',
                        action='store_true', default=False)
    parser.add_argument('-H', '--host',
                        help='Hostname or ip for target device',
                        action='store', default='localhost')
    parser.add_argument('-P', '--port',
                        help='Port for target device',
                        action='store', default='2828')
    parser.add_argument('-m', '--mode',
                        help='Test mode (stingray, phone) default (phone)',
                        action='store', default='phone')
    parser.add_argument('tests',
                        metavar='TEST',
                        help='Tests to run',
                        nargs='*')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = load_config(args.config)

    global _host
    global _port
    global _adbflag
    global DeviceBackup
    _host = args.host
    _port = int(args.port)

    if args.mode == 'stingray':
        _adbflag = True
        DeviceBackup = NoADBDeviceBackup

    if args.list_tests:
        return list_tests(args, config)

    return run_tests(args, config)


if __name__ == '__main__':
    sys.exit(not main())
