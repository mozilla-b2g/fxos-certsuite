#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import StringIO
import argparse
import json
import logging
import mozdevice
import moznetwork
import os
import sys
import wptserve
import pkg_resources

from wait import Wait
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

static_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "static"))

routes = [("GET", "/", connect_handler),
          ("GET", "/headers", headers_handler),
          ("GET", "/installed", installed_handler),
          ("POST", "/webapi_results", webapi_results_handler),
          ("GET", "/*", wptserve.handlers.file_handler)]

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
    parser.add_argument("--result-file",
                        help="absolute file path to store the resulting json." \
                             "Defaults to results.json on your current path",
                        action="store")
    args = parser.parse_args()

    report = {'buildprops': {}}

    logging.basicConfig()
    if not args.debug:
        logging.disable(logging.ERROR)

    # Step 1: Get device information
    try:
        dm = mozdevice.DeviceManagerADB()
    except mozdevice.DMError, e:
        print "Error connecting to device via adb (error: %s). Please be " \
            "sure device is connected and 'remote debugging' is enabled." % \
            e.msg
        sys.exit(1)

    # Reboot phone so it is in a fresh state
    if not args.no_reboot:
        print "Rebooting device..."
        dm.reboot(wait=True)

    if args.version not in supported_versions:
        print "%s is not a valid version. Please enter one of %s" % \
              (args.version, supported_versions)
        sys.exit(1)
        
    file_path = pkg_resources.resource_filename(
                        __name__, os.path.sep.join(['expected_webapi_results', '%s.json' % args.version]))

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
    omni_results_path = pkg_resources.resource_filename(
                        __name__, 'omni.json')
    omni_verify_file = pkg_resources.resource_filename(
                        __name__, os.path.sep.join(['expected_omni_results', '%s.json' % args.version]))
    omni_work_dir = pkg_resources.resource_filename(
                        __name__, 'omnidir')
    omni_analyzer = OmniAnalyzer(vfile=omni_verify_file, results=omni_results_path, dir=omni_work_dir)
    omni_analyzer.run()
    omni_results = open(omni_results_path, 'r').read()
    report["omni_result"] = json.loads(omni_results)
    os.remove(omni_results_path)

    # Step 2: Navigate to local hosted web server to install app for
    # WebIDL iteration and fetching HTTP headers
    addr = (moznetwork.get_ip(), 8080)
    httpd = wptserve.server.WebTestHttpd(
        host=addr[0], port=addr[1], routes=routes, doc_root=static_path)
    httpd.start()

    print "\n #1: On your phone, please navigate to http://%s:%d/" % \
        (httpd.host, httpd.port)
    Wait(timeout=240).until(lambda: connected is True)

    print "\n#2: Please click the link on the web page to connect your device"
    Wait().until(lambda: headers is not None)
    report["headers"] = headers

    print "\n#3: Please click the button to install the app"
    Wait().until(lambda: installed is True)

    print "\n#4: Please follow the instructions to install the app, then launch " \
        "<strong>WebAPIVerifier</strong> from the homescreen"
    Wait().until(lambda: webapi_results is not None)
    print "Processing results..."
    expected_results_json = open(file_path, 'r').read()
    expected_results = json.loads(expected_results_json)
    #compute difference in navigator functions
    expected_nav = set(expected_results["navList"])
    nav = set(webapi_results["navList"])

    missing_nav = expected_nav.difference(nav)
    if missing_nav:
        report['missing_navigator_functions'] = list(missing_nav)
    added_nav = nav.difference(expected_nav)
    if added_nav:
        report['added_navigator_functions'] = list(added_nav)

    # NOTE: privileged functions in an unprivileged app are null
    # compute difference in navigator "null" functions, ie: privileged functions
    expected_nav_null = set(expected_results["navNullList"])
    nav_null = set(webapi_results["navNullList"])

    missing_nav_null = expected_nav_null.difference(nav_null)
    if missing_nav_null:
        report['missing_navigator_unprivileged_functions'] = list(missing_nav_null)
    added_nav_null = nav_null.difference(expected_nav_null)
    if added_nav_null:
        report['added_navigator_privileged_functions'] = list(added_nav_null)

    #computer difference in window functions
    expected_window = set(expected_results["windowList"])
    window = set(webapi_results["windowList"])

    missing_window = expected_window.difference(window)
    if missing_window:
        report['missing_window_functions'] = list(missing_window)
    added_window = window.difference(expected_window)
    if added_window:
        report['added_window_functions'] = list(added_window)

    result_file_path = args.result_file
    if not result_file_path:
        result_file_path = "results.json"
    result_file = open(result_file_path, "w")
    result_file.write(json.dumps(report))
    result_file.close()

    print "\nResults have been stored in: %s" % result_file_path

if __name__ == "__main__":
    cli()
