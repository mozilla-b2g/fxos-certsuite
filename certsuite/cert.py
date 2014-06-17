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
webapi_results_embed_app = None

supported_versions = ["1.4", "1.3"]

@wptserve.handlers.handler
def webapi_results_handler(request, response):
    global headers
    headers = request.headers

    global webapi_results
    webapi_results = json.loads(request.POST["results"])

@wptserve.handlers.handler
def webapi_results_embed_apps_handler(request, response):
    global webapi_results_embed_app
    webapi_results_embed_app = json.loads(request.POST["results"])

routes = [("POST", "/webapi_results", webapi_results_handler),
          ("POST", "/webapi_results_embed_apps", webapi_results_embed_apps_handler),
          ("GET", "/*", wptserve.handlers.file_handler)]

static_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "static"))

def read_manifest(app):
    with open(os.path.join(app, 'manifest.webapp')) as f:
        manifest = f.read()
    return manifest

def package_app(path, extrafiles={}):
    app_path = 'app.zip'
    with ZipFile(app_path, 'w') as zip_file:
        for root, dirs, files in os.walk(path):
            for f in files:
                if f in extrafiles:
                    continue
                zip_file.write(os.path.join(root, f), f)
        for f in extrafiles:
            zip_file.writestr(f, extrafiles[f])

def install_app(logger, appname, version, apptype, apppath, all_perms,
                extrafiles, launch=False):

    logger.debug('uninstalling: %s' % appname)
    fxos_appgen.uninstall_app(appname)

    logger.debug('packaging: %s version: %s apptype: %s all_perms: %s' %
        (appname, version, apptype, all_perms))
    details = fxos_appgen.create_details(version, all_perms=all_perms)
    manifest = json.dumps(fxos_appgen.create_manifest(appname, details, apptype, version))
    files = extrafiles.copy()
    files['manifest.webapp'] = manifest
    package_app(apppath, files)

    logger.debug('installing: %s' % appname)
    fxos_appgen.install_app(appname, 'app.zip', script_timeout=30000)
    if launch:
        logger.debug('launching: %s' % appname)
        fxos_appgen.launch_app(appname)

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

def test_open_remote_window(logger, version, addr, apptype, all_perms):
    print "Installing the open remote window test app. This will take a minute... "

    result = False

    appname = 'Open Remote Window Test App'
    apppath = os.path.join(static_path, 'open-remote-window-test-app')
    install_app(logger, appname, version, apptype, apppath, all_perms,
        {'results_uri.js':
            'RESULTS_URI="http://%s:%s/webapi_results";' % addr},
            True)

    global webapi_results
    webapi_results = None
    try:
        Wait(timeout=60).until(lambda: webapi_results is not None)
    except wait.TimeoutException:
        logger.error('Timed out waiting for results')
        logger.test_end('permissions', 'ERROR')
        sys.exit(1)

    webapi_results = None

    script = """
        let manager = window.wrappedJSObject.AppWindowManager || window.wrappedJSObject.WindowManager;
        return manager.getRunningApps();
    """

    m = marionette.Marionette()
    m.start_session()
    running_apps = m.execute_script(script)
    for app in running_apps:
        if app.find('Remote Window') != -1:
            result = True
            # window.close() from the remote window doesn't seem to work
            kill_script = """
                let manager = window.wrappedJSObject.AppWindowManager || window.wrappedJSObject.WindowManager;
                manager.kill("%s")""" % app
            m.execute_script(kill_script)

    m.delete_session()

    fxos_appgen.uninstall_app(appname)

    return result

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

def log_results(diff, logger, report, test_group, name):
    if diff:
        report[name.replace('-', '_')] = diff
        for result in diff:
            try:
                logger.test_status(test_group, name, 'FAIL', message='Unexpected result for: %s' % result['name'])
            except TypeError:
                logger.test_status(test_group, name, 'FAIL', message='Unexpected result for: %s' % result)
    else:
        logger.test_status(test_group, name, 'PASS')

def parse_webapi_results(expected_results_path, results, prefix, logger, report):
    with open(expected_results_path) as f:
        expected_results = json.load(f)

    #compute difference in window functions
    expected_window = expected_results["windowList"]
    window = results["windowList"]

    missing_window = diff_results(expected_window, window)
    log_results(missing_window, logger, report, 'webapi', prefix + 'missing-window-functions')

    added_window = diff_results(window, expected_window)
    log_results(added_window, logger, report, 'webapi', prefix + 'added-window-functions')

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

    log_results(unexpected_webidl_results, logger, report, 'webapi', prefix + 'unexpected-webidl-results')
    log_results(added_webidl_results, logger, report, 'webapi', prefix + 'added-webidl-results')
    log_results(missing_webidl_results, logger, report, 'webapi', prefix + 'missing-webidl-results')

def parse_permissions_results(expected_results_path, results, prefix, logger, report):
    with open(expected_results_path) as f:
        expected_results = json.load(f)

    # compute differences in permissions results
    unexpected_results = diff_results(expected_results, results)
    log_results(unexpected_results, logger, report, 'permissions', prefix + 'unexpected-permissions-results')
    return not unexpected_results

def cli():
    global webapi_results
    global webapi_results_embed_app

    parser = argparse.ArgumentParser()
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
        'permissions',
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

    # wait here to make sure marionette is running
    logger.debug('Attempting to set up port forwarding for marionette')
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

    result_file_path = args.result_file
    if not result_file_path:
        result_file_path = "results.json"

    # Make sure we can write to the results file before running tests.
    # This will also ensure this file exists in case we error out later on.
    try:
        result_file = open(result_file_path, "w")
        result_file.close()
    except IOError as e:
        print 'Could not open result file for writing: %s errno: %d' % (result_file_path, e.errno)
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

    # start webserver
    if 'webapi' in test_groups or 'permissions' in test_groups:
        httpd = wptserve.server.WebTestHttpd(
            host=moznetwork.get_ip(), port=8000, routes=routes, doc_root=static_path)
        httpd.start()
        addr = (httpd.host, httpd.port)

    # run webapi and webidl tests
    if 'webapi' in test_groups:
        logger.test_start('webapi')
        logger.debug('Running webapi verifier tests')

        for apptype in ['web', 'privileged', 'certified']:
            global webapi_results

            webapi_results = None

            appname = '%s WebAPI Verifier' % apptype.capitalize()
            apppath = os.path.join(static_path, 'webapi-test-app')
            install_app(logger, appname, args.version, apptype, apppath, True,
                        {'results_uri.js':
                            'RESULTS_URI="http://%s:%s/webapi_results";' % addr},
                        True)

            try:
                Wait(timeout=600).until(lambda: webapi_results is not None)
            except wait.TimeoutException:
                logger.error('Timed out waiting for results')
                logger.test_end('webapi', 'ERROR')
                sys.exit(1)

            fxos_appgen.uninstall_app(appname)
            if "headers" not in report:
                report["headers"] = headers
                test_user_agent(headers['user-agent'], logger)

            results_filename = '%s.%s.json' % (args.version, apptype)
            if args.generate_reference:
                with open(results_filename, 'w') as f:
                    f.write(json.dumps(webapi_results, sort_keys=True, indent=2))

            file_path = pkg_resources.resource_filename(
                                __name__, os.path.sep.join(['expected_webapi_results', results_filename]))

            parse_webapi_results(file_path, webapi_results, '%s-' % apptype, logger, report)

        logger.debug('Done.')
        logger.test_end('webapi', 'OK')

    if 'permissions' in test_groups:
        logger.test_start('permissions')
        logger.debug('Running permissions tests')

        # install test app for embed-apps permission test
        embed_appname = 'Embed Apps Test App'
        apppath = os.path.join(static_path, 'embed-apps-test-app')
        install_app(logger, appname, args.version, apptype, apppath, True,
                    {'results_uri.js': 'RESULTS_URI="http://%s:%s/webapi_results_embed_apps";' % addr},
                     False)

        # run tests
        for apptype in ['web', 'privileged', 'certified']:
            for all_perms in [True, False]:

                webapi_results = None
                webapi_results_embed_app = None

                appname = '%s WebAPI Verifier' % apptype.capitalize()
                apppath = os.path.join(static_path, 'permissions-test-app')

                install_app(logger, appname, args.version, apptype,
                    apppath, all_perms,
                    {'results_uri.js':
                        'RESULTS_URI="http://%s:%s/webapi_results";' % addr},
                     True)
                try:
                    Wait(timeout=600).until(lambda: webapi_results is not None)
                except wait.TimeoutException:
                    logger.error('Timed out waiting for results')
                    logger.test_end('permissions', 'ERROR')
                    sys.exit(1)

                fxos_appgen.uninstall_app(appname)

                # gather results
                results = webapi_results

                # embed-apps results are posted to a separate URL
                if webapi_results_embed_app:
                    results['embed-apps'] = webapi_results_embed_app['embed-apps']
                else:
                    results['embed-apps'] = False

                # we test open-remote-window separately as opening a remote
                # window might stop the test app
                # TODO: this test causes hangs on some phones, disabling
                #       for now.
                #results['open-remote-window'] = test_open_remote_window(args.version,
                #                                    addr, apptype, all_perms)
                results['open-remote-window'] = False

                results_filename = '%s.%s.%s.json' % (args.version, apptype, ('all_perms' if all_perms else 'no_perms'))
                if args.generate_reference:
                    with open(results_filename, 'w') as f:
                        f.write(json.dumps(results, sort_keys=True, indent=2))

                file_path = pkg_resources.resource_filename( __name__,
                                os.path.sep.join(['expected_permissions_results', results_filename]))

                parse_permissions_results(file_path, results, '%s-%s-' % (apptype, ('all_perms' if all_perms else 'no_perms')), logger, report)

        logger.debug('Done.')
        logger.test_end('permissions', 'OK')

        # clean up embed-apps test app
        fxos_appgen.uninstall_app(embed_appname)

    result_file = open(result_file_path, "w")
    result_file.write(json.dumps(report, indent=2))
    result_file.close()

    logger.debug('Results have been stored in: %s' % result_file_path)

if __name__ == "__main__":
    cli()
