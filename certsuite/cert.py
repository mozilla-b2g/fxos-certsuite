#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import StringIO
import argparse
import json
import mozdevice
import moznetwork
import os
import sys
import wptserve
import pkg_resources

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
    args = parser.parse_args()

    report = {'buildprops': {}}

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

    # Step 2: Navigate to local hosted web server to install app for
    # WebIDL iteration and fetching HTTP headers
    addr = (moznetwork.get_ip(), 8080)
    httpd = wptserve.server.WebTestHttpd(
        host=addr[0], port=addr[1], routes=routes, doc_root=static_path)
    httpd.start()

    print >> sys.stderr, \
        "#1: On your phone, please navigate to http://%s:%d/" % \
        (httpd.host, httpd.port)
    Wait(timeout=240).until(lambda: connected is True)

    print >> sys.stderr, \
        "#2: Please click the link on the web page to connect your device"
    Wait().until(lambda: headers is not None)
    report["headers"] = headers

    print >> sys.stderr, "#3: Please click the button to install the app"
    Wait().until(lambda: installed is True)

    print >> sys.stderr, \
        "#4: Please follow the instructions to install the app, then launch " \
        "<strong>WebAPIVerifier</strong> from the homescreen"
    Wait().until(lambda: webapi_results is not None)
    print >> sys.stderr, \
        "Processing results..."
    file_path = pkg_resources.resource_filename(
                        __name__, 'expected_results.json')
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

    print json.dumps(report)

if __name__ == "__main__":
    cli()
