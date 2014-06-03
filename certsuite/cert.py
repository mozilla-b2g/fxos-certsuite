#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import StringIO
import argparse
import json
import logging
import marionette
import mozdevice
import moznetwork
import os
import pkg_resources
import re
import sys
import time
import wptserve
from zipfile import ZipFile
import fxos_appgen

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)
from omni_analyzer import OmniAnalyzer
from wait import Wait

"""Signalizes whether client has made initial connection to HTTP
server.

This is used for whilst waiting for the user to enter the correct
hostname and port to the device's browser.

"""
connected = False

headers = None

installed = False

webapi_results = None

supported_versions = ["1.4", "1.3"]

@wptserve.handlers.handler
def webapi_results_handler(request, response):
    global headers
    headers = request.headers

    global webapi_results
    webapi_results = json.loads(request.POST["results"])

static_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "static"))

routes = [("POST", "/webapi_results", webapi_results_handler),
          ("GET", "/*", wptserve.handlers.file_handler)]

def read_manifest(app):
    with open(os.path.join(app, 'manifest.webapp')) as f:
        manifest = f.read()
    return manifest

def package_app(path, extrafiles):
    app_path = 'app.zip'
    with ZipFile(app_path, 'w') as zip_file:
        for root, dirs, files in os.walk(path):
            for f in files:
                if f in extrafiles:
                    continue
                zip_file.write(os.path.join(root, f), f)
        for f in extrafiles:
            zip_file.writestr(f, extrafiles[f])

def test_user_agent(user_agent, logger):
    # See https://developer.mozilla.org/en-US/docs/Gecko_user_agent_string_reference#Firefox_OS
    # and https://wiki.mozilla.org/B2G/User_Agent/Device_Model_Inclusion_Requirements
    ua_rexp = re.compile("Mozilla/(\d+\.\d+) \((Mobile|Tablet)(;.*)?; rv:(\d+\.\d+)\) Gecko/(\d+\.\d+) Firefox/(\d+\.\d+)")

    m = ua_rexp.match(user_agent)

    valid = True

    if m is None or len(m.groups()) != 6:
        # no match
        valid = False
        message = 'Did not match regular expression'
    elif m.groups()[2] != None:
        # Specified a device string, strip leading ';' and any leading/trailing whitespace
        device = m.groups()[2][1:].strip()
        # Do not use slash ("/"), semicolon (";"), round brackets or any whitespace.
        device_rexp = re.compile('[/;\(\)\s]')
        m = device_rexp.search(device)
        if m:
            valid = False
            message = 'Device identifier: "%s" contains forbidden characters' % device

    if valid:
        logger.test_status('webapi', 'user-agent-string', 'PASS')
    else:
        logger.test_status('webapi', 'user-agent-string', 'FAIL', 'Invalid user-agent string: %s: %s' % (user_agent, message))

    return valid

def diff_results(a, b):

    a_set = set(a.keys())
    b_set = set(b.keys())

    result = list(b_set.difference(a_set))

    same_keys = a_set.intersection(b_set)
    for key in same_keys:
        if type(a[key]) is dict:
            if type(b[key]) is not dict:
                result.append(key)
            else:
                result.extend([key + '.' + item for item in diff_results(a[key], b[key])])
        elif a[key] != b[key]:
            result.append(key)

    return result

def log_results(diff, logger, report, name):
    if diff:
        report[name.replace('-', '_')] = diff
        for result in diff:
            try:
                logger.test_status('webapi', name, 'FAIL', message='Unexpected result for: %s' % result['name'])
            except TypeError:
                logger.test_status('webapi', name, 'FAIL', message='Unexpected result for: %s' % result)
    else:
        logger.test_status('webapi', name, 'PASS')

def parse_results(expected_results_path, results, prefix, logger, report):
    with open(expected_results_path) as f:
        expected_results = json.load(f)

    webapi_passed = True

    #compute difference in window functions
    expected_window = expected_results["windowList"]
    window = results["windowList"]

    missing_window = diff_results(expected_window, window)
    log_results(missing_window, logger, report, prefix + 'missing-window-functions')

    added_window = diff_results(window, expected_window)
    log_results(added_window, logger, report, prefix + 'added-window-functions')
    if missing_window or added_window:
        webapi_passed = False

    # compute differences in WebIDL results
    expected_webidl = {}
    for result in expected_results['webIDLResults']:
        expected_webidl[result['name']] = result

    unexpected_webidl_results = []
    added_webidl_results = []
    for result in results['webIDLResults']:
        try:
            if expected_webidl[result['name']]['result'] != result['result']:
                unexpected_webidl_results.append(result)
            del expected_webidl[result['name']]
        except KeyError:
            added_webidl_results.append(result)

    # since we delete found results above, anything here is missing
    missing_webidl_results = list(expected_webidl.values())

    log_results(unexpected_webidl_results, logger, report, prefix + 'unexpected-webidl-results')
    log_results(added_webidl_results, logger, report, prefix + 'added-webidl-results')
    log_results(missing_webidl_results, logger, report, prefix + 'missing-webidl-results')
    if added_webidl_results or unexpected_webidl_results or missing_webidl_results:
        webapi_passed = False

    # compute differences in permissions results
    expected_permissions = expected_results["permissionsResults"]
    permissions = results["permissionsResults"]
    unexpected_permissions_results = diff_results(expected_permissions, permissions)
    log_results(unexpected_permissions_results, logger, report, prefix + 'unexpected-permissions-results')
    if unexpected_permissions_results:
        webapi_passed = False

    return webapi_passed


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reboot",
                        help="don't reboot device before running test",
                        action="store_true")
    parser.add_argument("--version",
                        help="version of FxOS under test",
                        default="1.3",
                        action="store")
    parser.add_argument("--debug",
                        help="enable debug logging",
                        action="store_true")
    parser.add_argument("--list-test-groups",
                        help="print test groups available to run",
                        action="store_true")
    parser.add_argument("--include",
                        metavar="TEST-GROUP",
                        help="include this test group",
                        action="append")
    parser.add_argument("--result-file",
                        help="absolute file path to store the resulting json." \
                             "Defaults to results.json on your current path",
                        action="store")
    parser.add_argument("--generate-reference",
                        help="Generate expected result files",
                        action="store_true")
    commandline.add_logging_group(parser)

    args = parser.parse_args()

    test_groups = [
        'omni-analyzer',
        'webapi',
        ]
    if args.list_test_groups:
        for t in test_groups:
            print t
        return 0

    test_groups = set(args.include if args.include else test_groups)
    report = {'buildprops': {}}

    logging.basicConfig()
    if not args.debug:
        logging.disable(logging.ERROR)

    logger = commandline.setup_logging("certsuite", vars(args), {})

    # Step 1: Get device information
    try:
        dm = mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        print "Error connecting to device via adb (error: %s). Please be " \
            "sure device is connected and 'remote debugging' is enabled." % \
            e.msg
        logger.error("Error connecting to device: %s" % e.msg)
        sys.exit(1)

    # Reboot phone so it is in a fresh state
    if not args.no_reboot:
        print "Rebooting device..."
        dm.reboot(wait=True)

        # wait here to make sure marionette is running
        if dm.forward("tcp:2828", "tcp:2828") != 0:
            raise Exception("Can't use localhost:2828 for port forwarding." \
                            "Is something else using port 2828?")
        retries = 0
        while retries < 5:
            try:
                m = marionette.Marionette()
                m.start_session()
                m.delete_session()
                break
            except (IOError, TypeError):
                time.sleep(5)
                retries += 1
        else:
            raise Exception("Couldn't connect to marionette after %d attempts. " \
            "Is the marionette extension installed?" % retries)

    if args.version not in supported_versions:
        print "%s is not a valid version. Please enter one of %s" % \
              (args.version, supported_versions)
        sys.exit(1)

    # get build properties
    buildpropoutput = dm.shellCheckOutput(["cat", "/system/build.prop"])
    for buildprop in [line for line in buildpropoutput.splitlines() if '=' \
                          in line]:
        (prop, val) = buildprop.split('=')
        report['buildprops'][prop] = val

    # get process list
    report['processes_running'] = map(lambda p: { 'name': p[1], 'user': p[2] },
                                      dm.getProcessList())

    # kernel version
    report['kernel_version'] = dm.shellCheckOutput(["cat", "/proc/version"])

    # application.ini information
    appinicontents = dm.pullFile('/system/b2g/application.ini')
    sf = StringIO.StringIO(appinicontents)
    config = ConfigParser.ConfigParser()
    config.readfp(sf)
    report['application_ini'] = {}
    for section in config.sections():
        report['application_ini'][section] = dict(config.items(section))

    # run the omni.ja analyzer
    if 'omni-analyzer' in test_groups:
        omni_results_path = pkg_resources.resource_filename(
                            __name__, 'omni.json')
        omni_verify_file = pkg_resources.resource_filename(
                            __name__, os.path.sep.join(['expected_omni_results', '%s.json' % args.version]))
        omni_work_dir = pkg_resources.resource_filename(
                            __name__, 'omnidir')
        omni_analyzer = OmniAnalyzer(vfile=omni_verify_file, results=omni_results_path, dir=omni_work_dir, logger=logger)
        omni_results = open(omni_results_path, 'r').read()
        report["omni_result"] = json.loads(omni_results)
        if not args.generate_reference:
            os.remove(omni_results_path)

    # run webapi, webidl and permissions tests
    if 'webapi' in test_groups:
        logger.test_start('webapi')

        httpd = wptserve.server.WebTestHttpd(
            host=moznetwork.get_ip(), port=8000, routes=routes, doc_root=static_path)
        httpd.start()
        addr = (httpd.host, httpd.port)

        webapi_passed = True

        for apptype in ['web', 'privileged', 'certified']:
            global webapi_results

            webapi_results = None
            print "Installing the %s app. This will take a minute... " % apptype

            appname = '%s WebAPI Verifier' % apptype.capitalize()
            details = fxos_appgen.create_details(args.version, all_perms=True)
            manifest = json.dumps(fxos_appgen.create_manifest(appname, details, apptype, args.version))

            apppath = os.path.join(static_path, 'webapi-test-app')
            package_app(apppath, {'results_uri.js': 'RESULTS_URI="http://%s:%s/webapi_results";' % addr,
                                  'manifest.webapp': manifest})

            fxos_appgen.install_app(appname, 'app.zip', script_timeout=30000)
            fxos_appgen.launch_app(appname)

            print "Done. Running the app..."

            Wait(timeout=600).until(lambda: webapi_results is not None)
            fxos_appgen.uninstall_app(appname)
            if "headers" not in report:
                report["headers"] = headers
                test_user_agent(headers['user-agent'], logger)

            if args.generate_reference:
                with open('webapi_results_%s.json' % apptype, 'w') as f:
                    f.write(json.dumps(webapi_results, sort_keys=True, indent=2))

            print "Processing results..."
            file_path = pkg_resources.resource_filename(
                                __name__, os.path.sep.join(['expected_webapi_results', '%s.%s.json' % (args.version, apptype)]))

            webapi_passed = parse_results(file_path, webapi_results, '%s-' % apptype, logger, report) and webapi_passed

        logger.test_end('webapi', 'OK' if webapi_passed else 'ERROR')

    result_file_path = args.result_file
    if not result_file_path:
        result_file_path = "results.json"
    result_file = open(result_file_path, "w")
    result_file.write(json.dumps(report, indent=2))
    result_file.close()

    print "\nResults have been stored in: %s" % result_file_path

if __name__ == "__main__":
    cli()
