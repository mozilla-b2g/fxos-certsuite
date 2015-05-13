#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import argparse
import mozdevice
import hashlib
import re
import json
import base64
import subprocess
import tempfile
import traceback
import zipfile
import shutil
import pickle
from diff_py import *

from mozlog.structured import structuredlog

JS_FILES = re.compile('\.jsm*$')
MANIFEST_FILES = re.compile('\.manifest$')


def unzip_omnifile(omnifile, path):
    # The following is the right way to do this in python, however that throws a BadZipFile error
    # referencing an incorrect magic number. However the normal unzip command works just fine.
    # NOTE: This will DEPEND on running on linux/mac :-()
    omnizip = None
    try:
        omnizip = zipfile.ZipFile(omnifile, 'r')
        omnizip.extractall(path)
    except zipfile.BadZipfile:
        # Then let's try a hack - only works on mac or linux
        subprocess.call(['unzip', '-d', path, omnifile])
    except:
        print "Error opening omni.ja file: %s" % (omnifile)
        traceback.print_exc()
        sys.exit(1)
    finally:
        if omnizip:
            omnizip.close()


class CleanedTempFolder(object):
    def __init__(self, root_folder=None):
        self.root_folder = root_folder

    def __enter__(self, *args, **kwargs):
        self.folder = tempfile.mkdtemp(dir=self.root_folder)
        return self.folder

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.folder)


class OmniAnalyzer(object):
    def __init__(self, reference_omni_ja, logger=None):
        self.reference_omni_ja = reference_omni_ja
        self.omni_ja_on_device = '/system/b2g/omni.ja'
        if logger is None:
            self.logger = structuredlog.StructuredLogger("omni-analyzer")
        else:
            self.logger = logger

    def getomni(self, workdir):
        # Get the omni.ja from /system/b2g/omni.ja
        # Unzip it
        try:
            dm = mozdevice.DeviceManagerADB()
        except mozdevice.DMError as e:
            print ("Error connecting to device via adb (error: %s). Please be sure device is connected and 'remote debugging' is enabled." % e.msg)
            sys.exit(1)
        omnifile = os.path.join(workdir, 'omni.ja')
        dm.getFile(self.omni_ja_on_device, omnifile)
        unzip_omnifile(omnifile, os.path.join(workdir, 'device'))

    def log_pass(self, testid, message=''):
        self.logger.test_end(testid, 'PASS', expected='PASS', message=message)
        
    def log_ok(self, testid, message=''):
        self.logger.test_end(testid, 'OK', expected='OK', message=message)

    def run(self, results_file=None, html_format=False):
        testid = '%s.%s.%s' % ('cert', 'omni-analyzer', 'check-omni-diff')
        is_run_success = False
        diff = ''
        with CleanedTempFolder() as workdir:
            self.getomni(workdir)
            unzip_omnifile(self.reference_omni_ja, os.path.join(workdir, 'reference'))

            cmd = ['diff', '-U', '8', '--new-file', os.path.join(workdir, 'reference'), os.path.join(workdir, 'device')]
            try:
                diff = subprocess.check_output(cmd)
                self.log_pass(testid, 'The %s on device is the same as reference file omni.ja.' % self.omni_ja_on_device)
                is_run_success = True
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    # return code 1 simply indicates differences were found
                    diff = e.output
                    if html_format:
                        dh = HTMLDiffHelper()
                        result = dh.diff(os.path.join(workdir, 'reference'), os.path.join(workdir, 'device'))
                        diff_result = result.unicode(indent=2).encode('utf8')
                    else:
                        diff_result = diff
                    if results_file is not None:
                        with open(results_file, 'w') as f:
                            f.write(diff_result)
                    diff_message = 'The omni.ja on device is different from reference file omni.ja.'
                    is_run_success = True
                else:
                    diff_message = 'error running diff: %s' % e.returncode
                    self.logger.error(diff_message)
                self.log_ok(testid, diff_message)
        return diff, is_run_success


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-omni-ja", help="Path to reference omni.ja file")
    parser.add_argument("--results-file", help="File in which to store the results",
        default=os.path.join(os.getcwd(), "results.diff"))
    parser.add_argument("--html", help="Output to HTML format", action='store_true')

    args = parser.parse_args(argv[1:])
    omni_analyzer = OmniAnalyzer(args.reference_omni_ja)
    diff, is_run_success = omni_analyzer.run(results_file=args.results_file, html_format=args.html)


if __name__ == "__main__":
    main(sys.argv)
