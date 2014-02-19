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

JS_FILES = re.compile('\.jsm*$')
MANIFEST_FILES = re.compile('\.manifest$')

class OmniAnalyzer:
    def __init__(self, vfile, results, dir, mode=None, vserver=None, dump=False):
        self.generate_reference = mode
        self.verification_server = vserver
        self.verify_file = vfile
        self.results_file = results
        self.results_dict = {}
        self.workdir = dir
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

        # Also print our results to stdout - TODO: Necessary or desired?
        if dump:
            print json.dumps(self.results_dict, indent=2)
        if warnings:
            print "Found %s changes in omni.ja" % warnings
        else:
            print "No warnings detected in omni.ja"

    def getomni(self):
        # Get the omni.ja from /system/b2g/omni.ja
        # Unzip it
        omnizip = None
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
        # The following is the right way to do this in python, however that throws a BadZipFile error
        # referencing an incorrect magic number. However the normal unzip command works just fine.
        # NOTE: This will DEPEND on running on linux/mac :-()
        try:
            omnizip = zipfile.ZipFile(omnifile, 'r')
            omnizip.extractall(path=self.workdir)
        except zipfile.BadZipfile:
            # Then let's try a hack - only works on mac or linux
            subprocess.call(['unzip', '-d', self.workdir, omnifile])
        except:
            print "Error opening omni.ja file: %s" % (omnifile)
            traceback.print_exc()
            sys.exit(1)
        finally:
            if omnizip:
                omnizip.close()


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
            for f in files:
                if JS_FILES.search(f) or MANIFEST_FILES.search(f):
                    r[f] = self._hash_file(os.path.join(root, f))
        return r

    def _hash_file(self, path):
        f = open(path, "rb")
        if f==None:
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
        for root, dirs, files in os.walk(self.workdir):
            if filename in files:
                path = os.path.join(root, filename)
                break
        try:
            f = open(path, 'rb')
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
        # TODO: If we decide to use a docker system so that we can have a known environment, we might want
        #       to explore using a database for storing the reference and all the reference files. Then
        #       we can just provide diffs as our output from this function.  If we don't provide diffs from
        #       this function, we should write something that takes the JSON output of this method, and uses
        #       a generated reference JSON to get file by file diffs by base 64 decoding the file-contents in the JSON.
        warn_count = 0
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
    parser.add_argument("--dump", help="Dumps the resulting json to stdout", action="store_true")

    args = parser.parse_args(argv[1:])
    omni_analyzer = OmniAnalyzer(vfile=args.verifyfile, results=args.resultsfile, dir=args.workingdir,
                                 mode=args.generate, vserver=args.verifyserver, dump=args.dump)

if __name__ == "__main__":
    main(sys.argv)
