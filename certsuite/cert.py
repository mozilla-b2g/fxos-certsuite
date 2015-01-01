#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import ConfigParser
import json
import logging
import os
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

supported_versions = ["2.1", "2.0", "1.4", "1.3"]

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

@wptserve.handlers.handler
def webapi_log_handler(request, response):
    global last_test_started

    log_string = request.POST["log"]
    index = log_string.find('test started:')
    if index > -1:
        last_test_started = log_string[index + len('test started:'):]
    logger.debug(log_string)

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
        logger.test_status('user-agent', 'user-agent-string', 'PASS')
    else:
        logger.test_status('user-agent', 'user-agent-string', 'FAIL', message='Invalid user-agent string: %s: %s' % (user_agent, message))

    return valid

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
      let manager = window.wrappedJSObject.AppWindowManager || window.wrappedJSObject.WindowManager;
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

def _run(args, logger):
    # This function is to simply make the cli() function easier to handle

    test_groups = [
        'omni-analyzer',
        'permissions',
        'webapi',
        'user-agent',
        'crash-reporter',
        'search-id',
        ]
    if args.list_test_groups:
        for t in test_groups:
            print t
        return 0

    test_groups = set(args.include if args.include else test_groups)
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

    # get build properties
    buildpropoutput = dm.shellCheckOutput(["cat", "/system/build.prop"])
    for buildprop in [line for line in buildpropoutput.splitlines() if '=' \
                          in line]:
        eq = buildprop.find('=')
        prop = buildprop[:eq]
        val = buildprop[eq + 1:]
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

    logger.suite_start(tests=[])
    # run the omni.ja analyzer
    if 'omni-analyzer' in test_groups:
        omni_ref_path = pkg_resources.resource_filename(
                            __name__, os.path.join('expected_omni_results', 'omni.ja.%s' % args.version))
        omni_analyzer = OmniAnalyzer(omni_ref_path, logger=logger)
        diff = omni_analyzer.run()
        report["omni_result"] = diff

    # start webserver
    if 'webapi' in test_groups or 'permissions' in test_groups:
        httpd = wptserve.server.WebTestHttpd(
            host=moznetwork.get_ip(), port=8000, routes=routes, doc_root=static_path)
        httpd.start()
        addr = (httpd.host, httpd.port)

    # run webapi and webidl tests
    if 'webapi' in test_groups:
        errors = False

        logger.test_start('webapi')
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
            logger.test_end('webapi', 'ERROR')
        else:
            logger.test_end('webapi', 'OK')

    if 'permissions' in test_groups:
        errors = False

        logger.test_start('permissions')
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
            webapi_results = None
            webapi_results_embed_app = None

            # if we try to launch after killing too quickly, the app seems
            # to not fully launch
            time.sleep(5)

            if permission is not None:
                logger.debug('testing permission: %s' % permission)
                set_permission(permission, u'allow', installed_appname)
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
            logger.test_end('permissions', 'ERROR')
        else:
            logger.test_end('permissions', 'OK')

        # clean up embed-apps test app
        logger.debug('uninstalling: %s' % embed_appname)
        fxos_appgen.uninstall_app(embed_appname)

    if 'user-agent' in test_groups:
        logger.test_start('user-agent')
        logger.debug('Running user agent tests')

        user_agent_string = run_marionette_script("return navigator.userAgent;")
        logger.debug('UserAgent: %s' % user_agent_string)
        valid = test_user_agent(user_agent_string, logger)

        if valid:
            logger.test_end('user-agent', 'OK')
        else:
            logger.test_end('user-agent', 'ERROR')

    if 'crash-reporter' in test_groups:
        logger.test_start('crash-reporter')
        logger.debug('start checking test reporter')

        crash_report_toggle = (report.get('application_ini', {})
                                     .get('Crash Reporter', {})
                                     .get('enabled'))

        if crash_report_toggle == '1':
            logger.test_end('crash-reporter', 'OK')
        else:
            logger.test_end('crash-reporter', 'ERROR')

    if 'search-id' in test_groups:
        logger.test_start('search-id')
        fxos_appgen.launch_app('browser')

        script = """
          result = window.wrappedJSObject.UrlHelper.getUrlFromInput('hello world');
          return result;
        """

        m = marionette.Marionette('localhost', 2828)
        m.start_session()
        browser = m.find_element('css selector', 'iframe[src="app://search.gaiamobile.org/newtab.html"]')
        m.switch_to_frame(browser)
        url = m.execute_script(script)
        m.delete_session()

        report['search-oemid'] = url

        oemid_rexp = re.compile('client=mobile-firefoxos&channel=fm:org.mozilla:([A-Z0-9.]+):official&')

        match = oemid_rexp.match(url)
        if match:
            logger.test_status('search-id', 'oemid', 'PASS', message='oemid: %s' % match.groups()[0])
        else:
            logger.test_status('search-id', 'oemid', 'FAIL', message='no oemid found in url: %s' % url)

        logger.test_end('search-id', 'OK')

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

    parser = argparse.ArgumentParser()
    parser.add_argument("--version",
                        help="version of FxOS under test",
                        default="2.1",
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
