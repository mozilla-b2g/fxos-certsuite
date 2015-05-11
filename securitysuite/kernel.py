# -*- encoding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import mozdevice

# getter for shared logger instance
from mozlog.structured import get_default_logger

from certsuite.harness import check_adb

# ######################################################################################################################
# shared module functions
#########################


# Sample b2g-ps output:

### ZTE Open C v1.3
# APPLICATION      USER     PID   PPID  VSIZE  RSS     WCHAN    PC         NAME
# b2g              root      294   1     226612 75984 ffffffff b6f1b63c S /system/b2g/b2g
# (Nuwa)           root      929   294   51484  20420 ffffffff b6f5a63c S /system/b2g/plugin-container
# Usage            u0_a981   981   929   65888  21792 ffffffff b6f5a63c S /system/b2g/plugin-container
# Homescreen       u0_a989   989   929   72748  26680 ffffffff b6f5a63c S /system/b2g/plugin-container
# (Preallocated a  root      1067  929   61724  16888 ffffffff b6f5a63c S /system/b2g/plugin-container

### Flame v2.2 nightly eng
# APPLICATION    SEC USER     PID   PPID  VSIZE  RSS     WCHAN    PC         NAME
# b2g              0 root      206   1     214984 90160 ffffffff b6eaf8ac S /system/b2g/b2g
# (Nuwa)           0 root      499   206   66600  22664 ffffffff b6eaf8ac S /system/b2g/b2g
# Built-in Keyboa  2 u0_a1010  1010  499   73204  26460 ffffffff b6eaf8ac S /system/b2g/b2g
# Homescreen       2 u0_a1179  1179  206   136856 44632 ffffffff b6f338ac S /system/b2g/plugin-container
# Find My Device   2 u0_a1202  1202  499   72800  22800 ffffffff b6eaf8ac S /system/b2g/b2g
# (Preallocated a  2 u0_a1785  1785  499   71500  18248 ffffffff b6eaf8ac S /system/b2g/b2g

class b2gps(object):
    """
    Class to retrieve and interpret output from the b2g-ps shell command
    """

    def __init__(self):
        self.logger = get_default_logger()
        try:
            self.dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
        except mozdevice.DMError as e:
            self.logger.error("Error connecting to device via adb (error: %s). Please be "
                              "sure device is connected and 'remote debugging' is enabled." %
                              e.msg)
            raise

        try:
            self.ps = self.dm.shellCheckOutput(['b2g-ps'], root=True).split('\n')
        except mozdevice.DMError as e:
            self.logger.error("Error reading b2g-ps result from device: %s" % e.msg)
            raise

    def has_known_format(self):
        known = [
            'APPLICATION    SEC USER     PID   PPID  VSIZE  RSS     WCHAN    PC         NAME',
            'APPLICATION      USER     PID   PPID  VSIZE  RSS     WCHAN    PC         NAME'
        ]
        return self.ps[0] in known

    def seccomp_is_enabled(self):
        return " SEC " in self.ps[0]

    def b2g_uses_seccomp(self):
        # Working hypothesis: if Homescreen has seccomp, then b2g uses seccomp
        for psline in self.ps:
            if psline.startswith('Homescreen       2 '):
                return True
        return False


class procpid(object):
    """
    Class to retrieve and analyze process information in /proc
    """

    def __init__(self):
        self.logger = get_default_logger()
        try:
            self.dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
        except mozdevice.DMError as e:
            self.logger.error("Error connecting to device via adb (error: %s). Please be "
                              "sure device is connected and 'remote debugging' is enabled." %
                              e.msg)
            raise

    def get_pidlist(self):
        out = self.dm.shellCheckOutput(['ls', '/proc/*/status'], root=True)
        proclines = out.split('\n')[-1]  # skip 'self' which is always last
        pids = [x.split('/')[2] for x in proclines]
        return pids


#######################################################################################################################
# Test implementations
################################

# derived from shared test class
from suite import ExtraTest


#######################################################################################################################
# kernel.seccomp

class seccomp(ExtraTest):
    """
    Test that checks seccomp status.
    """

    group = "kernel"
    module = sys.modules[__name__]

    @classmethod
    def run(cls, version=None):
        logger = get_default_logger()

        try:
            ps = b2gps()
        except:
            cls.log_status('FAIL', 'Failed to retrieve b2g-ps info.')
            return False

        # list of b2g versions that don't have seccomp support
        without_seccomp = ['1.0', '1.1', '1.2', '1.3', '1.3t', '1.4']
        if version is not None and version in without_seccomp:
            cls.log_status('PASS', "Target version %s doesn't support SECCOMP" % version)
            return True

        if not ps.has_known_format():
            cls.log_status('FAIL', "b2g-ps output from device has unknown format")
            return False

        if not ps.seccomp_is_enabled():
            cls.log_status('FAIL', "Please enable SECCOMP support on the device. The B2G version should support it.")
            return False

        if not ps.b2g_uses_seccomp():
            cls.log_status('FAIL', "Gonk has SECCOMP support, but the B2G process doesn't. Please enable.")
            return False

        cls.log_status('PASS', "SECCOMP enabled in Gonk and B2G process")
        return True

