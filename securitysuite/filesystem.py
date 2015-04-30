# -*- encoding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import os
import sys
import subprocess
import mozdevice

# getter for shared logger instance
from mozlog.structured import get_default_logger


# ######################################################################################################################
# shared module functions
#########################

def parse_ls(out):
    """
    Parser for Android's ls -lR output.
    Takes a string, returns parsed structure.
    """

    # assumed ls -lR line format:
    # -rw-r--r-- root     shell           0 2013-07-05 02:26 tasks
    # drwxr-xr-x root     root              2013-07-05 02:26 log
    # brw------- root     root     179,   0 2013-07-05 02:26 mmcblk0
    # lrwxrwxrwx root     root              2013-07-05 02:34 subsystem -> ../class/bdi

    # CAVE: format may change through versions.
    # TODO: implement plausibility test.

    mode = r'^(.)'
    field = r'([^ ]+) +'
    dev = r'(\d+), +(\d+) '
    date = r'(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}) '
    name = r'(.+)$'
    link = r'(.+) -> (.+)$'

    logger = get_default_logger()

    # adb returns newline as \r\n
    # but mozdevice uses \n
    for dirstr in out[2:-2].split('\n\n'):
        lines = dirstr.split('\n')
        dirname = lines[0][:-1]
        if len(lines) == 2 and lines[1].startswith("opendir failed"):
            continue
        for filestr in lines[1:]:
            if filestr.endswith(": No such file or directory"):
                continue
            if filestr.endswith(": Permission denied"):
                continue
            specs = None
            if filestr[0] in 'dsp':  # directory, socket, pipe
                regexp = mode + field * 3 + date + name
                m = re.search(regexp, filestr)
                specs = {
                'mode': m.group(1),
                'perm': m.group(2),
                'uid': m.group(3),
                'gid': m.group(4),
                'date': m.group(5),
                'name': m.group(6)
                }
            elif filestr[0] == 'l':  # symbolic link
                regexp = mode + field * 3 + date + link
                m = re.search(regexp, filestr)
                specs = {
                'mode': m.group(1),
                'perm': m.group(2),
                'uid': m.group(3),
                'gid': m.group(4),
                'date': m.group(5),
                'name': m.group(6),
                'link': m.group(7)
                }
            elif filestr[0] in 'cb':  # device
                regexp = mode + field * 3 + dev + date + name
                m = re.search(regexp, filestr)
                specs = {
                'mode': m.group(1),
                'perm': m.group(2),
                'uid': m.group(3),
                'gid': m.group(4),
                'major': m.group(5),
                'minor': m.group(6),
                'date': m.group(7),
                'name': m.group(8)
                }
            else:  # rest
                try:
                    regexp = mode + field * 4 + date + name
                    m = re.search(regexp, filestr)
                    specs = {
                    'mode': m.group(1),
                    'perm': m.group(2),
                    'uid': m.group(3),
                    'gid': m.group(4),
                    'size': m.group(5),
                    'date': m.group(6),
                    'name': m.group(7)
                    }
                except:
                    logger.error("parse error on %s" % filestr)

            try:
                specs['name'] = '/' + os.path.relpath("%s/%s" % (dirname, specs['name']), '/')
                if 'link' in specs.keys():
                    specs['link'] = '/' + os.path.relpath("%s/%s" % (dirname, specs['link']), '/')
            except:
                logger.warning("no name from %s" % filestr)

            yield specs


#######################################################################################################################
# Test implementations
################################

# derived from shared test class
from suite import ExtraTest


#######################################################################################################################
# filesystem.wordwritable_info

class worldwritable_info(ExtraTest):
    """
    Test that checks gonk file system for world-writable files.
    """

    group = "filesystem"
    module = sys.modules[__name__]

    whitelist = {
    'ok': [
        '^/proc/.*$',  # whitelisting for now
        '^/sys/.*$',  # whitelisting for now
        '^/system/.*$',  # /system/ is supposed to be read-only
        '^/dev/null$',
        '^/dev/zero$',
        '^/dev/full$',
        '^/dev/urandom$',
        '^/dev/random$',
        '^/dev/ashmem$',
        '^/dev/ptmx$',
        '^/dev/console$',
        '^/dev/tty$',
        '^/proc/.*/net/xt_qtaguid/ctrl$'
    ],
    'unchecked': [
        '^/dev/genlock$',
        '^/dev/binder$',
        '^/dev/kgsl-3d0$',
        '^/dev/socket/keystore$',
        '^/dev/socket/property_service$',
        '^/dev/log/.*$',
        '^/acct/uid/.*/cgroup.event_control$'
    ]
    }

    @classmethod
    def whitelist_check(cls, name, flag='ok', whitelist=None):
        if whitelist is None:
            whitelist = cls.whitelist
        r = re.compile('|'.join(whitelist[flag]))
        return r.match(name) is not None

    @classmethod
    def run(cls, version=None):
        logger = get_default_logger()

        try:
            dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
        except mozdevice.DMError as e:
            logger.error("Error connecting to device via adb (error: %s). Please be " \
                         "sure device is connected and 'remote debugging' is enabled." % \
                         e.msg)
            raise

        try:
            out = dm.shellCheckOutput(['ls', '-alR', '/'], root=True)
        except mozdevice.DMError as e:
            cls.log_status('FAIL', 'Failed to gather filesystem information from device via adb: %s' % e.msg)
            return False

        found = []
        for f in parse_ls(out):
            if f['perm'][7] == 'w' and f['mode'] != 'l':
                if not cls.whitelist_check(f['name']):
                    found.append(f['name'])
        if len(found) > 0:
            cls.log_status('PASS',
                           'Please ensure that the following world-writable files will not pose a security risk:\n%s' % '\n'.join(
                               found))
        else:
            cls.log_status('PASS', 'No unexpected suidroot executables found.')

        return True


#######################################################################################################################
# filesystem.suidroot_info

class suidroot_info(ExtraTest):
    """
    Test that checks gonk file system for suid root binaries.
    """

    group = "filesystem"
    module = sys.modules[__name__]

    whitelist = {
    'ok': [
        '^/system/bin/run-as$'
    ],
    'unchecked': [
        '^/system/bin/diag_mdlog$'
    ]
    }

    @classmethod
    def whitelist_check(cls, name, flag='ok', whitelist=None):
        if whitelist is None:
            whitelist = cls.whitelist
        r = re.compile('|'.join(whitelist[flag]))
        return r.match(name) is not None

    @classmethod
    def run(cls, version=None):
        logger = get_default_logger()

        try:
            dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
        except mozdevice.DMError as e:
            logger.error("Error connecting to device via adb (error: %s). Please be " \
                         "sure device is connected and 'remote debugging' is enabled." % \
                         e.msg)
            raise

        try:
            out = dm.shellCheckOutput(['ls', '-alR', '/'], root=True)
        except mozdevice.DMError as e:
            cls.log_status('FAIL', 'Failed to gather filesystem information from device via adb: %s' % e.msg)
            return False

        found = []
        for f in parse_ls(out):
            if f['perm'][2] == 's' and f['uid'] == 'root':
                if not cls.whitelist_check(f['name']):
                    found.append(f['name'])
        if len(found) > 0:
            cls.log_status('PASS',
                           'Please ensure that the following suid root files are no security risk:\n%s' % '\n'.join(
                               found))
        else:
            cls.log_status('PASS', 'No unexpected suidroot executables found.')

        return True
