#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import StringIO
import argparse
import json
import logging
from marionette import Marionette
import mozdevice
import moznetwork
import os
import pkg_resources
import sys
import wptserve
from zipfile import ZipFile
from fxos_appgen import install_app

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
webapi_results_priv = None
webapi_results_cert = None

supported_versions = ["1.4", "1.3"]

@wptserve.handlers.handler
def connect_handler(request, response):
    response.headers.set("Content-Type", "text/html")
    response.content = "<head><meta charset=utf-8 name=\"viewport\" content=\"width=device-width\"></head>" \
                       "<p><a href='/headers'><h1>Click me</h1></a></p>"

    global connected
    connected = True

@wptserve.handlers.handler
def headers_handler(request, response):
    response.headers.set("Content-Type", "text/html")
    response.content = "<head><meta charset=utf-8 name=\"viewport\" content=\"width=device-width\"></head>" \
                       "<p><a href='/install.html'><h1>Click me to go to the app install page<h1></a></p>"

    global headers
    headers = request.headers

@wptserve.handlers.handler
def installed_handler(request, response):
    global installed
    installed = True

@wptserve.handlers.handler
def webapi_results_handler(request, response):
    global webapi_results
    webapi_results = json.loads(request.POST["results"])

@wptserve.handlers.handler
def webapi_results_priv_handler(request, response):
    global webapi_results_priv
    webapi_results_priv = json.loads(request.POST["results"])

@wptserve.handlers.handler
def webapi_results_cert_handler(request, response):
    global webapi_results_cert
    webapi_results_cert = json.loads(request.POST["results"])

static_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "static"))

routes = [("GET", "/", connect_handler),
          ("GET", "/headers", headers_handler),
          ("GET", "/installed", installed_handler),
          ("POST", "/webapi_results", webapi_results_handler),
          ("POST", "/webapi_results_priv", webapi_results_priv_handler),
          ("POST", "/webapi_results_cert", webapi_results_cert_handler),
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
                with open(os.path.join(root, f), 'r') as data:
                    zip_file.write(os.path.join(root, f), f)
        for f in extrafiles:
            zip_file.writestr(f, extrafiles[f])

def install_app(app_name, app_path, adb_path=None, timeout=5000):
    dm = None
    if adb_path:
        dm = mozdevice.DeviceManagerADB(adbPath=adb_path)
    else:
        dm = mozdevice.DeviceManagerADB()

    #TODO: replace with app name
    installed_app_name = app_name.lower()
    installed_app_name = installed_app_name.replace(" ", "-")
    if dm.dirExists("/data/local/webapps/%s" % installed_app_name):
        raise Exception("%s is already installed" % app_name)
        sys.exit(1)
    app_zip = os.path.basename(app_path)
    dm.pushFile("%s" % app_path, "/data/local/%s" % app_zip)
    # forward the marionette port
    ret = dm.forward("tcp:2828", "tcp:2828")
    if ret != 0:
        raise Exception("Can't use localhost:2828 for port forwarding." \
                        "Is something else using port 2828?")

    # install the app
    install_js = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "app_install.js"))
    f = open(install_js, "r")
    script = f.read()
    f.close()
    script = script.replace("YOURAPPID", installed_app_name)
    script = script.replace("YOURAPPZIP", app_zip)
    m = Marionette()
    m.start_session()
    m.set_context("chrome")
    m.set_script_timeout(timeout)
    m.execute_async_script(script)
    m.delete_session()

def diff_results(a, b, checkNull):

    a_set = set(a.keys())
    b_set = set(b.keys())

    if checkNull:
        a_nullset = set([key for key in a.keys() if a[key] is None])
        b_nullset = set([key for key in b.keys() if b[key] is None])
        result = list(b_nullset.difference(a_nullset))
    else:
        result = list(b_set.difference(a_set))

    same_keys = a_set.intersection(b_set)
    for key in same_keys:
        if type(a[key]) is dict:
            if type(b[key]) is not dict:
                result.extend(key)
            else:
                result.extend([key + '.' + item for item in diff_results(a[key], b[key], checkNull)])

    return result

def log_results(diff, logger, report, name):
    if diff:
        report[name.replace('-', '_')] = diff 
        try:
            logger.test_status('webapi', name, 'FAIL', message=','.join([result['name'] for result in diff]))
        except TypeError: 
            logger.test_status('webapi', name, 'FAIL', message=','.join(diff))
    else:
        logger.test_status('webapi', name, 'PASS')

def parse_results(expected_results_path, results, prefix, logger, report):
    expected_results_json = open(expected_results_path, 'r').read()
    expected_results = json.loads(expected_results_json)
    #compute difference in navigator functions
    expected_nav = expected_results["navList"]
    nav = results["navList"]

    logger.test_start('webapi')
    webapi_passed = True

    missing_nav = diff_results(expected_nav, nav, False)
    log_results(missing_nav, logger, report, prefix + 'missing-navigator-functions')

    added_nav = diff_results(nav, expected_nav, False)
    log_results(added_nav, logger, report, prefix + 'added-navigator-functions')
    if missing_nav or added_nav:
        webapi_passed = False

    # NOTE: privileged functions in an unprivileged app are null
    # compute difference in navigator "null" functions, ie: privileged functions
    missing_nav_null = diff_results(expected_nav, nav, True)
    log_results(missing_nav_null, logger, report, prefix + 'missing-navigator-unprivileged-functions')

    added_nav_null = diff_results(nav, expected_nav, True)
    log_results(added_nav_null, logger, report, prefix + 'added-navigator-unprivileged-functions')
    if missing_nav_null or added_nav_null:
        webapi_passed = False

    #computer difference in window functions
    expected_window = expected_results["windowList"]
    window = results["windowList"]

    missing_window = diff_results(expected_window, window, False)
    log_results(missing_window, logger, report, prefix + 'missing-window-functions')

    added_window = diff_results(window, expected_window, False)
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
        'omnijar-analyzer',
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

    # Step 2: Navigate to local hosted web server to install app for
    # WebIDL iteration and fetching HTTP headers
    if 'webapi' in test_groups:
        addr = (moznetwork.get_ip(), 8080)
        httpd = wptserve.server.WebTestHttpd(
            host=addr[0], port=addr[1], routes=routes, doc_root=static_path)
        httpd.start()

        print "\n#1: On your phone, please launch the browser app and navigate to "\
            "http://%s:%d/" % (httpd.host, httpd.port)
        Wait(timeout=600).until(lambda: connected is True)

        print "\n#2: On the web page that's loaded, please click the 'Click me' link"
        Wait().until(lambda: headers is not None)
        report["headers"] = headers

        print "\n#3: Next, click the link which reads 'Click me to go to the app " \
            "install page', then click the button which appears to install the test app"
        Wait().until(lambda: installed is True)

        print "\n#4: Please follow the instructions to install the app, then launch " \
            "WebAPI Verifier from the homescreen. This will start the WebAPI tests " \
            "and may take a couple minutes to complete."
        Wait(timeout=600).until(lambda: webapi_results is not None)

        if args.generate_reference:
            with open('webapi_results.json', 'w') as f:
                f.write(json.dumps(webapi_results))

        print "Processing results..."
        file_path = pkg_resources.resource_filename(
                            __name__, os.path.sep.join(['expected_webapi_results', '%s.json' % args.version]))

        webapi_passed = parse_results(file_path, webapi_results, 'unpriv-', logger, report)

        # Run privileged app
        print "\n#5: Installing the privileged app. This will take a minute... "

        apppath = os.path.join(static_path, 'webapi-test-app')
        apppath_priv = os.path.join(static_path, 'webapi-test-app-priv')
        manifest = read_manifest(apppath_priv)
        appname = json.loads(manifest)['name']
        package_app(apppath, {'results_uri.js': 'RESULTS_URI="http://%s:%s/webapi_results_priv";' % addr,
                              'manifest.webapp': manifest})
        install_app(appname, 'app.zip', timeout=30000)

        print "Done. Please run the Privileged WebAPI Verifier from the home screen."

        Wait(timeout=600).until(lambda: webapi_results_priv is not None)

        if args.generate_reference:
            with open('webapi_results_priv.json', 'w') as f:
                f.write(json.dumps(webapi_results_priv))

        print "Processing results..."
        file_path = pkg_resources.resource_filename(
                            __name__, os.path.sep.join(['expected_webapi_results', '%s.priv.json' % args.version]))
        webapi_passed = parse_results(file_path, webapi_results_priv, 'priv-', logger, report) and webapi_passed

        # Run certified app
        print "\n#6: Installing the certified app. This will take a minute... "

        apppath = os.path.join(static_path, 'webapi-test-app')
        apppath_cert = os.path.join(static_path, 'webapi-test-app-cert')
        manifest = read_manifest(apppath_cert)
        appname = json.loads(manifest)['name']
        package_app(apppath, {'results_uri.js': 'RESULTS_URI="http://%s:%s/webapi_results_cert";' % addr,
                              'manifest.webapp': manifest})
        install_app(appname, 'app.zip', timeout=30000)
        os.remove('app.zip')
        print "Done. Please run the Certified WebAPI Verifier from the home screen."

        Wait(timeout=600).until(lambda: webapi_results_cert is not None)

        if args.generate_reference:
            with open('webapi_results_cert.json', 'w') as f:
                f.write(json.dumps(webapi_results_cert))

        print "Processing results..."
        file_path = pkg_resources.resource_filename(
                            __name__, os.path.sep.join(['expected_webapi_results', '%s.cert.json' % args.version]))
        webapi_passed = parse_results(file_path, webapi_results_cert, 'cert-', logger, report) and webapi_passed

        logger.test_end('webapi', 'PASS' if webapi_passed else 'FAIL')

    result_file_path = args.result_file
    if not result_file_path:
        result_file_path = "results.json"
    result_file = open(result_file_path, "w")
    result_file.write(json.dumps(report, indent=2))
    result_file.close()

    print "\nResults have been stored in: %s" % result_file_path

if __name__ == "__main__":
    cli()
