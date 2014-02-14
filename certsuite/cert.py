#!/usr/bin/env python

import ConfigParser
import StringIO
import argparse
import json
import mozdevice
import sys

def cli():

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reboot", help="don't reboot device before running test",
                        action="store_true")
    args = parser.parse_args()

    report = { 'buildprops': {} }

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

    print json.dumps(report)


if __name__ == "__main__":
    cli()
