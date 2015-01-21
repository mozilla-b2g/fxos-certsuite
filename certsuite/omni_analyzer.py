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
        dm.getFile('/system/b2g/omni.ja', omnifile)
        unzip_omnifile(omnifile, os.path.join(workdir, 'device'))

    def run(self):
        diff = ''
        with CleanedTempFolder() as workdir:
            self.getomni(workdir)
            unzip_omnifile(self.reference_omni_ja, os.path.join(workdir, 'reference'))

            cmd = ['diff', '-u', '8', '--new-file', os.path.join(workdir, 'reference'), os.path.join(workdir, 'device')]
            try:
                diff = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    # return code 1 simply indicates differences were found
                    diff = e.output
                else:
                    self.logger.error('error running diff: %s' % e.returncode)

        return diff

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-omni-ja", help="Path to reference omni.ja file")
    parser.add_argument("--results-file", help="File in which to store the results",
        default=os.path.join(os.getcwd(), "results.diff"))

    args = parser.parse_args(argv[1:])
    omni_analyzer = OmniAnalyzer(args.reference_omni_ja)
    diff = omni_analyzer.run()
    with open(args.results_file, 'w') as f:
        f.write(diff)

if __name__ == "__main__":
    main(sys.argv)
