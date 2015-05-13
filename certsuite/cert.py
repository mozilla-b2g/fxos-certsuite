#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import ConfigParser
import json
import logging
import os
import sys
import pkg_resources
import re
import StringIO
import time
import traceback
import wait

from py.xml import html
from zipfile import ZipFile

import fxos_appgen
import marionette
import mozdevice
import moznetwork
import wptserve

from mozlog.structured import commandline

from omni_analyzer import OmniAnalyzer

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

last_test_started = 'None'
logger = None

supported_versions = ["2.2", "2.1", "2.0", "1.4", "1.3"]


@wptserve.handlers.handler
def webapi_results_handler(request, response):
    global headers
    headers = request.headers

    global webapi_results
    webapi_results = json.loads(request.POST["results"])

    response.headers.set('Access-Control-Allow-Origin', '*')
    response.content = "ok"


@wptserve.handlers.handler
def webapi_results_embed_apps_handler(request, response):
    global webapi_results_embed_app
    webapi_results_embed_app = json.loads(request.POST["results"])

    response.headers.set('Access-Control-Allow-Origin', '*')
    response.content = "ok"


@wptserve.handlers.handler
def webapi_log_handler(request, response):
    global last_test_started
    global logger

    log_string = request.POST["log"]
    index = log_string.find('test started:')
    if index > -1:
        last_test_started = log_string[index + len('test started:'):]
    logger.debug(log_string)

    response.headers.set('Access-Control-Allow-Origin', '*')
    response.content = "ok"


routes = [("POST", "/webapi_results", webapi_results_handler),
          ("POST", "/webapi_results_embed_apps", webapi_results_embed_apps_handler),
          ("POST", "/webapi_log", webapi_log_handler),
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
    fxos_appgen.install_app(appname, 'app.zip', script_timeout=120000)
    if launch:
        logger.debug('launching: %s' % appname)
        fxos_appgen.launch_app(appname)

def test_id(suite, test, subtest):
    return '%s.%s.%s' % (suite, test, subtest)

def log_pass(logger, testid, message=''):
    logger.test_end(testid, 'PASS', expected='PASS', message=message)

def log_ok(logger, testid, message=''):
    logger.test_end(testid, 'OK', expected='OK', message=message)

def log_fail(logger, testid, message=''):
    logger.test_end(testid, 'FAIL', expected='PASS', message=message)

def test_omni_analyzer(logger, report, args):
    testid = test_id('cert', 'omni-analyzer', 'check-omni-diff')
    logger.test_start(testid)
    omni_ref_path = pkg_resources.resource_filename(
                        __name__, os.path.join('expected_omni_results', 'omni.ja.%s' % args.version))
    omni_analyzer = OmniAnalyzer(omni_ref_path, logger=logger)
    if args.html_result_file is not None:
        diff, is_run_success = omni_analyzer.run(html_format=True, results_file=os.path.join(os.path.dirname(args.html_result_file), 'omni_diff_report.html'))
    else:
        diff, is_run_success = omni_analyzer.run()
    report["omni_result"] = diff

def test_webapi(logger, report, args, addr):
    errors = False

    logger.debug('Running webapi verifier tests')

    for apptype in ['web', 'privileged', 'certified']:
        global webapi_results

        webapi_results = None

        appname = '%s WebAPI Verifier' % apptype.capitalize()
        apppath = os.path.join(static_path, 'webapi-test-app')
        install_app(logger, appname, args.version, apptype, apppath, True,
                    {'results_uri.js':
                        'RESULTS_URI="http://%s:%s/webapi_results";LOG_URI="http://%s:%s/webapi_log";' % (addr * 2)},
                    True)

        try:
            wait.Wait(timeout=120).until(lambda: webapi_results is not None)
        except wait.TimeoutException:
            logger.error('Timed out waiting for results for test: %s' % last_test_started)
            errors = True

        logger.debug('uninstalling: %s' % appname)
        fxos_appgen.uninstall_app(appname)

        if webapi_results is None:
            continue

        if "headers" not in report:
            report["headers"] = headers

        results_filename = '%s.%s.json' % (args.version, apptype)
        if args.generate_reference:
            with open(results_filename, 'w') as f:
                f.write(json.dumps(webapi_results, sort_keys=True, indent=2))
        else:
            file_path = pkg_resources.resource_filename(
                            __name__, os.path.sep.join(['expected_webapi_results', results_filename]))

            parse_webapi_results(file_path, webapi_results, '%s-' % apptype, logger, report)

    logger.debug('Done.')
    if errors:
        logger.error('Test webapi with errors')

def test_permissions(logger, report, args, addr):
    errors = False

    #logger.test_start('permissions')
    logger.debug('Running permissions tests')

    permissions = get_permissions()

    # test default permissions
    for apptype in ['web', 'privileged', 'certified']:
        logger.debug('Testing default permissions: %s' % apptype)
        results = {}
        expected_webapi_results = None

        appname = 'Default Permissions Test App'
        fxos_appgen.uninstall_app(appname)
        installed_appname = appname.lower().replace(" ", "-")
        fxos_appgen.generate_app(appname, install=True, app_type=apptype,
                                 all_perm=True)

        for permission in permissions:
            result = get_permission(permission, installed_appname)
            results[permission] = result

        results_filename = '%s.%s.json' % (args.version, apptype)
        if args.generate_reference:
            with open(results_filename, 'w') as f:
                f.write(json.dumps(results, sort_keys=True, indent=2))
        else:
            file_path = pkg_resources.resource_filename(__name__,
                        os.path.sep.join(['expected_permissions_results',
                        results_filename]))
            parse_permissions_results(file_path, results, '%s-' % apptype,
                logger, report)

        fxos_appgen.uninstall_app(appname)

    # test individual permissions
    logger.debug('Testing individual permissions')
    results = {}

    # first install test app for embed-apps permission test
    embed_appname = 'Embed Apps Test App'
    apppath = os.path.join(static_path, 'embed-apps-test-app')
    install_app(logger, embed_appname, args.version, 'certified', apppath, True,
                {'results_uri.js': 'RESULTS_URI="http://%s:%s/webapi_results_embed_apps";' % addr},
                 False)

    appname = 'Permissions Test App'
    installed_appname = appname.lower().replace(" ", "-")
    apppath = os.path.join(static_path, 'permissions-test-app')
    install_app(logger, appname, args.version, 'web', apppath, False,
            {'results_uri.js':
                'RESULTS_URI="http://%s:%s/webapi_results";LOG_URI="http://%s:%s/webapi_log";' % (addr * 2)})

    for permission in [None] + permissions:
        global webapi_results
        global webapi_results_embed_app
        webapi_results = None
        webapi_results_embed_app = None

        # if we try to launch after killing too quickly, the app seems
        # to not fully launch
        time.sleep(5)

        if permission is not None:
            logger.debug('testing permission: %s' % permission)
            set_permission(permission, u'allow', installed_appname)
        else:
            logger.debug('testing permission: None')
        fxos_appgen.launch_app(appname)

        try:
            wait.Wait(timeout=60).until(lambda: webapi_results is not None)

            # embed-apps results are posted to a separate URL
            if webapi_results_embed_app:
                webapi_results['embed-apps'] = webapi_results_embed_app['embed-apps']
            else:
                webapi_results['embed-apps'] = False

            if permission is None:
                expected_webapi_results = webapi_results
            else:
                results[permission] = diff_results(expected_webapi_results, webapi_results)
        except wait.TimeoutException:
            logger.error('Timed out waiting for results')
            errors = True
            if permission is not None:
                results[permission] = 'timed out'
            else:
                # If we timeout on our baseline results there is
                # no point in proceeding.
                logger.error('Could not get baseline results for permissions. Skipping tests.')
                break

        kill('app://' + installed_appname)
        if permission is not None:
            set_permission(permission, u'deny', installed_appname)

    logger.debug('uninstalling: %s' % appname)
    fxos_appgen.uninstall_app(appname)

    # we test open-remote-window separately as opening a remote
    # window might stop the test app
    results['open-remote-window'] = test_open_remote_window(logger,
                                        args.version, addr)

    results_filename = '%s.permissions.json' % args.version
    if args.generate_reference:
        with open(results_filename, 'w') as f:
            f.write(json.dumps(results, sort_keys=True, indent=2))
    else:
        file_path = pkg_resources.resource_filename(__name__,
                    os.path.sep.join(['expected_permissions_results',
                    results_filename]))
        parse_permissions_results(file_path, results, 'individual-',
            logger, report)

    logger.debug('Done.')
    if errors:
        logger.error('Test individual with errors')

    # clean up embed-apps test app
    logger.debug('uninstalling: %s' % embed_appname)
    fxos_appgen.uninstall_app(embed_appname)

def test_crash_reporter(logger, report):
    testid = test_id('cert','crash-reporter', 'crash-report-toggle')
    logger.test_start(testid)
    logger.debug('start checking test reporter')

    crash_report_toggle = (report.get('application_ini', {})
                                 .get('Crash Reporter', {})
                                 .get('enabled'))

    if crash_report_toggle == '1':
        log_pass(logger, testid)
    else:
        log_fail(logger, testid, 'crash report toggle = %s' % crash_report_toggle)

def test_user_agent(logger, report):
    testid = test_id('cert','user-agent', 'user-agent-string')

    logger.test_start(testid)
    logger.debug('Running user agent tests')

    user_agent = run_marionette_script("return navigator.userAgent;")

    # See https://developer.mozilla.org/en-US/docs/Gecko_user_agent_string_reference#Firefox_OS
    # and https://wiki.mozilla.org/B2G/User_Agent/Device_Model_Inclusion_Requirements
    logger.debug('UserAgent: %s' % user_agent)
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
        log_pass(logger, testid)
    else:
        log_ok(logger, testid, 'current user-agent string: %s: %s' % (user_agent, message))

def test_open_remote_window(logger, version, addr):
    global webapi_results

    results = {}
    for value in ['deny', 'allow']:
        result = False
        webapi_results = None

        appname = 'Open Remote Window Test App'
        installed_appname = appname.lower().replace(" ", "-")
        apppath = os.path.join(static_path, 'open-remote-window-test-app')
        install_app(logger, appname, version, 'web', apppath, False,
            {'results_uri.js':
                'RESULTS_URI="http://%s:%s/webapi_results";' % addr})

        set_permission('open-remote-window', value, installed_appname)
        fxos_appgen.launch_app(appname)
        try:
            wait.Wait(timeout=30).until(lambda: webapi_results is not None)
        except wait.TimeoutException:
            results[value] = 'timed out'

        if webapi_results is not None:
            result = webapi_results['open-remote-window']

        # launching here will force the remote window (if any) to be hidden
        # but will not retrigger the test.
        fxos_appgen.launch_app(appname)
        logger.debug('uninstalling: %s' % appname)
        fxos_appgen.uninstall_app(appname)

        results['open-remote-window-' + value] = result

    return results


def diff_results(a, b):

    a_set = set(a.keys())
    b_set = set(b.keys())

    result = list(b_set.difference(a_set))

    same_keys = a_set.intersection(b_set)
    for key in same_keys:
        if type(a[key]) is dict:
            if type(b[key]) is not dict:
                result.append(key + ' (expected object)')
            else:
                result.extend([key + '.' + item for item in diff_results(a[key], b[key])])

    return result

def log_results(diff, logger, report, test_group, name):
    testid = test_id('cert', test_group, name)
    if diff:
        report[name.replace('-', '_')] = diff
        for result in diff:
            logger.test_start(testid)
            try:
                log_fail(logger, testid, 'Unexpected result for: %s' % result['name'])
            except TypeError:
                log_fail(logger, testid, 'Unexpected result for: %s' % result)
    else:
        logger.test_start(testid)
        log_pass(logger, testid)

def parse_webapi_results(expected_results_path, results, prefix, logger, report):
    with open(expected_results_path) as f:
        expected_results = json.load(f)

    #compute difference in window functions
    expected_window = expected_results["windowList"]
    window = results["windowList"]

    missing_window = diff_results(window, expected_window)
    log_results(missing_window, logger, report, 'webapi', prefix + 'missing-window-functions')

    added_window = diff_results(expected_window, window)
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


def run_marionette_script(script, chrome=False, async=False):
    """Create a Marionette instance and run the provided script"""
    m = marionette.Marionette()
    m.start_session()
    if chrome:
        m.set_context(marionette.Marionette.CONTEXT_CHROME)
    if not async:
        result = m.execute_script(script)
    else:
        result = m.execute_async_script(script)
    m.delete_session()
    return result


def kill(name):
    """Kill the specified app"""
    script = """
      let manager = window.wrappedJSObject.appWindowManager || new window.wrappedJSObject.AppWindowManager();
      manager.kill('%s');
    """
    return run_marionette_script(script % name)


def get_permission(permission, app):
    # The object created to wrap PermissionSettingsModule is to work around
    # an intermittent bug where it will sometimes be undefined.
    script = """
      const {classes: Cc, interfaces: Ci, utils: Cu, results: Cr} = Components;
      var a = {b: Cu.import("resource://gre/modules/PermissionSettings.jsm")};

      return a.b.PermissionSettingsModule.getPermission('%s', '%s/manifest.webapp', '%s', '', false);
    """
    app_url = 'app://' + app
    return run_marionette_script(script % (permission, app_url, app_url), True)


def get_permissions():
    """Return permissions in PermissionsTable.jsm"""
    script = """
      const {classes: Cc, interfaces: Ci, utils: Cu, results: Cr} = Components;
      Cu.import("resource://gre/modules/PermissionsTable.jsm");

      result = []
      for (permission in PermissionsTable) {
        result.push(permission);
      }

      return result;
    """
    return run_marionette_script(script, True)


def set_permission(permission, value, app):
    """Set a permission for the specified app
       Value should be 'deny' or 'allow'
    """
    # The object created to wrap PermissionSettingsModule is to work around
    # an intermittent bug where it will sometimes be undefined.
    script = """
      const {classes: Cc, interfaces: Ci, utils: Cu, results: Cr} = Components;
      var a = {b: Cu.import("resource://gre/modules/PermissionSettings.jsm")};
      return a.b.PermissionSettingsModule.addPermission({
        type: '%s',
        origin: '%s',
        manifestURL: '%s/manifest.webapp',
        value: '%s',
        browserFlag: false
      });
    """
    app_url = 'app://' + app
    run_marionette_script(script % (permission, app_url, app_url, value), True)


def make_html_report(path, report):
    def tabelize(value):
        try:
            rows = []
            for key in value.keys():
                rows.append(html.tr(html.td(html.pre(key)), html.td(tabelize(value[key]))))
            return html.table(rows)
        except AttributeError:
            if type(value) == type([]):
                return html.table(map(tabelize, value))
            else:
                return html.pre(value)

    body_els = []
    keys = report.keys()
    keys.sort()
    links = []
    for key in keys:
        links.append(html.li(html.a(key, href="#" + key)))
    body_els.append(html.ul(links))
    for key in keys:
        body_els.append(html.a(html.h1(key), id=key))
        body_els.append(tabelize(report[key]))
    with open(path, 'w') as f:
        doc = html.html(html.head(html.style('table, td {border: 1px solid;}')), html.body(body_els))
        f.write(str(doc))


def get_application_ini(dm):
    # application.ini information
    appinicontents = dm.pullFile('/system/b2g/application.ini')
    sf = StringIO.StringIO(appinicontents)
    config = ConfigParser.ConfigParser()
    config.readfp(sf)
    application_ini = {}
    for section in config.sections():
        application_ini[section] = dict(config.items(section))
    return application_ini


def get_buildprop(dm):
    # get build properties
    buildprops = {}
    buildpropoutput = dm.shellCheckOutput(["cat", "/system/build.prop"])
    for buildprop in [line for line in buildpropoutput.splitlines() if '=' \
                          in line]:
        eq = buildprop.find('=')
        prop = buildprop[:eq]
        val = buildprop[eq + 1:]
        buildprops[prop] = val
    return buildprops


def get_processes_running(dm):
    return map(lambda p: {'name': p[1], 'user': p[2]}, dm.getProcessList())


def get_kernel_version(dm):
    return dm.shellCheckOutput(["cat", "/proc/version"])


def _run(args, logger):
    # This function is to simply make the cli() function easier to handle

    test_groups = [
        'omni-analyzer',
        'permissions',
        'webapi',
        'user-agent',
        'crash-reporter'
        ]
    if args.list_test_groups:
        for t in test_groups:
            print t
        return 0

    skip_tests = []
    test_groups = set(args.include if args.include else test_groups)

    if args.device_profile:
        skiplist = []
        with open(args.device_profile, 'r') as device_profile_file:
            skiplist = json.load(device_profile_file)['result']['cert']
        skip_tests = [x for x in test_groups if x in skiplist]
        test_groups = [x for x in test_groups if x not in skiplist]

    report = {'buildprops': {}}

    logging.basicConfig()
    # Step 1: Get device information
    try:
        dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
    except mozdevice.DMError as e:
        print "Error connecting to device via adb (error: %s). Please be " \
            "sure device is connected and 'remote debugging' is enabled." % \
            e.msg
        raise

    # wait here to make sure marionette is running
    logger.debug('Attempting to set up port forwarding for marionette')
    dm.forward("tcp:2828", "tcp:2828")

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
        raise Exception("%s is not a valid version" % args.version)

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
        raise

    report['buildprops'] = get_buildprop(dm)

    report['processes_running'] = get_processes_running(dm)

    report['kernel_version'] = get_kernel_version(dm)

    report['application_ini'] = get_application_ini(dm)

    logger.suite_start(tests=[])

    # record skipped test to report
    for test in skip_tests:
        logger.test_start(test)
        logger.test_end(test, 'SKIP', message='Skipped by device profile')

    # run the omni.ja analyzer
    if 'omni-analyzer' in test_groups:
        test_omni_analyzer(logger, report, args)

    # start webserver
    if 'webapi' in test_groups or 'permissions' in test_groups:
        httpd = wptserve.server.WebTestHttpd(
            host=moznetwork.get_ip(), port=8000, routes=routes, doc_root=static_path)
        httpd.start()
        addr = (httpd.host, httpd.port)

    # run webapi and webidl tests
    if 'webapi' in test_groups:
        test_webapi(logger, report, args, addr)

    if 'permissions' in test_groups:
        test_permissions(logger, report, args, addr)

    if 'user-agent' in test_groups:
        test_user_agent(logger, report)

    if 'crash-reporter' in test_groups:
        test_crash_reporter(logger, report)

    logger.suite_end()

    with open(result_file_path, "w") as result_file:
        result_file.write(json.dumps(report, indent=2))
    logger.debug('Results have been stored in: %s' % result_file_path)

    if args.html_result_file is not None:
        make_html_report(args.html_result_file, report)
        logger.debug('HTML Results have been stored in: %s' % args.html_result_file)


def cli():
    global logger
    global webapi_results
    global webapi_results_embed_app

    reload(sys)
    sys.setdefaultencoding('utf-8')

    parser = argparse.ArgumentParser()
    parser.add_argument("--version",
                        help="version of FxOS under test",
                        default="2.2",
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
    parser.add_argument("--html-result-file",
                        help="absolute file path to store the resulting html.",
                        action="store")
    parser.add_argument("--generate-reference",
                        help="Generate expected result files",
                        action="store_true")
    parser.add_argument('-p', "--device-profile", action="store",  type=os.path.abspath,
                        help="specify the device profile file path which could include skipped test case information")
    commandline.add_logging_group(parser)

    args = parser.parse_args()

    if not args.debug:
        logging.disable(logging.ERROR)

    logger = commandline.setup_logging("certsuite", vars(args), {})

    try:
        _run(args, logger)
    except:
        logger.critical(traceback.format_exc())
        raise


if __name__ == "__main__":
    cli()
