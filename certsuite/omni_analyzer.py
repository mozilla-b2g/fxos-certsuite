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

class OmniAnalyzer:
    def __init__(self, vfile, results, dir, mode=None, vserver=None, logger=structuredlog.StructuredLogger("omni-analyzer")):
        self.generate_reference = mode
        self.verification_server = vserver
        self.verify_file = vfile
        self.results_file = results
        self.results_dict = {}
        self.workdir = dir
        self.logger = logger
        warnings = 0

        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

        self.results_dict = self.run()
        if not self.generate_reference:
            ref = self._get_reference()
            warnings, self.results_dict = self.verify(ref, self.results_dict)

        f = open(self.results_file, "w")
        json.dump(self.results_dict, f)
        f.close()

        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

    def getomni(self):
        # Get the omni.ja from /system/b2g/omni.ja
        # Unzip it
        try:
            dm = mozdevice.DeviceManagerADB()
        except mozdevice.DMError, e:
            print "Error connecting to device via adb (error: %s). Please be " \
                "sure device is connected and 'remote debugging' is enabled." % \
                e.msg
            sys.exit(1)
        omnifile = os.path.join(self.workdir, 'omni.ja')
        dm.getFile('/system/b2g/omni.ja', omnifile)

        # Try to unzip it
        unzip_omnifile(omnifile, self.workdir)

    def run(self):
        # iterate over the modules, greprefs.js, defaults/pref/b2g.js and the top level files in chrome/chrome/content and components
        # and hash each file using md5. Organize them into logical areas in the resulting directionary.
        self.getomni()
        analysis = {'directories': {}}

        # Analyze contents of <workdir>/chrome for chrome files
        analysis['directories']['chrome'] = self._walker(os.path.join(self.workdir, 'chrome'))

        # Analyze components directory: <workdir>/components
        analysis['directories']['components'] = self._walker(os.path.join(self.workdir, 'components'))

        # Analyze the modules dir: <workdir>/modules
        analysis['directories']['modules'] = self._walker(os.path.join(self.workdir, 'modules'))

        # Analyze the defaults dir: <workdir>/defaults
        analysis['directories']['defaults'] = self._walker(os.path.join(self.workdir, 'defaults'))

        # And grab the greprefs file from the root
        analysis['directories']['root'] = {'greprefs.js': self._hash_file(os.path.join(self.workdir, 'greprefs.js'))}

        return analysis

    def _walker(self, root_dir):
        r = {}

        # walk <workdir>/chrome/chrome/content - chrome files
        for root, dirs, files in os.walk(root_dir):
            # we want to be able to store the relative path from the workdir
            skip = len(os.path.commonprefix([root, self.workdir])) + 1
            for f in files:
                if JS_FILES.search(f) or MANIFEST_FILES.search(f):
                    path = os.path.join(root, f)
                    r[path[skip:]] = self._hash_file(path)
        return r

    def _hash_file(self, path):
        f = open(path, "rb")
        if f==None:
            print 'warning: could not hash: %s: file not found' % path
            return ''
        md5 = hashlib.md5()
        while 1:
            data = f.read(1024)
            if not data:
                break
            md5.update(data)
        f.close()
        ret = md5.hexdigest()
        return ret

    def _get_reference(self):
        # We can potentially grab the reference file from a server or from a local file. The server would be
        # a REST endpoint we could call and get the JSON file back (the JSON is formatted just like what
        # we generate using our run method)
        ref = {}
        if self.verification_server:
            # Hit server end point and save Reference file
            raise "Not Implemented Yet"
        else:
            try:
                f = open(self.verify_file, "r")
                ref = json.load(f)
            except:
                print "ERROR: Could not load reference file %s" % self.verify_file
                traceback.print_exc()
            finally:
                f.close()
        return ref

    def _encode_base64(self, filename):
        encoded = ''
        f = None
        try:
            f = open(os.path.join(self.workdir, filename), 'rb')
            encoded = base64.b64encode(f.read())
        except:
            print "Failed to encode file %s" % (filename)
            traceback.print_exc()
        finally:
            if f:
                f.close()
        return encoded

    def verify(self, reference, device):
        # Verifies the device JSON structure matches that of the reference JSON for this release
        # If we find a discrepancy, package the file for later analysis
        warn_count = 0
        self.logger.test_start('omni-analyzer')
        res = {'directories': {}}
        for d in device['directories'].keys():
            dirresults = {}
            for filename in device['directories'][d].keys():
                # Check to see if the filename exists in the reference and that the hashes are the same
                if filename not in reference['directories'][d]:
                    # File found in device not in reference, partner has added file, so tag it for analysis
                    dirresults[filename] = {'reason': 'PARTNER_FILE', 'file-contents': self._encode_base64(filename)}
                    warn_count += 1
                elif reference['directories'][d][filename] != device['directories'][d][filename]:
                    # Hash mismatch, partner changed file from reference, tag for analysis
                    dirresults[filename] = {'reason': 'PARTNER_CHANGE', 'file-contents': self._encode_base64(filename)}
                    warn_count += 1
            res['directories'][d] = dirresults

        # Also check for files present in reference but missing from device
        for d in reference['directories'].keys():
            for filename in reference['directories'][d].keys():
                if filename not in device['directories'][d]:
                    res['directories'][d][filename] = {'reason': 'PARTNER_CHANGE', 'file-contents': ''}
                    warn_count += 1

        self.logger.debug('omni-analyzer found %d changes in omni.ja' % warn_count)
        self.logger.test_end('omni-analyzer', 'OK')
        return warn_count, res

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", help="Generate the reference file", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verifyserver", help="Pull verification file from server to perform verification")
    group.add_argument("--verifyfile", help="Use local file for verification.")
    parser.add_argument("--resultsfile", help="File to store the results in (JSON format)",
        default=os.path.join(os.getcwd(), "results.json"))
    parser.add_argument("--workingdir", help="Directory to work in - will be removed",
        default=os.path.join(os.getcwd(), "omnidir"))

    args = parser.parse_args(argv[1:])
    omni_analyzer = OmniAnalyzer(vfile=args.verifyfile, results=args.resultsfile, dir=args.workingdir,
                                 mode=args.generate, vserver=args.verifyserver)

if __name__ == "__main__":
    main(sys.argv)
