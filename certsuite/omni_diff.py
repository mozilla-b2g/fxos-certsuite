#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys

from omni_analyzer import unzip_omnifile

class OmniDiff(object):
    def __init__(self, resultspath, omnipath, outputpath, workdir):
        self.resultspath = resultspath
        self.omnipath = omnipath
        self.outputpath = outputpath
        self.workdir = workdir

        # clean up in case we were interrupted last run
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

    def run(self):

        # unzip reference omni.ja
        unzip_omnifile(self.omnipath, self.workdir)

        # read results json
        with open(self.resultspath, 'r') as f:
            json_results = json.loads(f.read())

        if 'omni_result' in json_results:
            directories = json_results['omni_result']['directories']
        else:
            directories = json_results['directories']

        warnings = False
        with open(self.outputpath, 'w') as output:
            for directory in directories:
                pathes = directories[directory]
                for path in pathes:
                    reason = pathes[path]['reason']
                    if reason == 'PARTNER_FILE':
                        # this is a new file, so use an empty file for diff
                        ref_path = os.path.join(self.workdir, 'empty')
                        if not os.path.isfile(ref_path):
                            f = open(ref_path, 'w')
                            f.close()
                    else:
                        ref_path = os.path.join(self.workdir, path)

                    contents = pathes[path]['file-contents']
                    cmd = ['diff', ref_path, '-']
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    diff, err = proc.communicate(input=base64.b64decode(contents))

                    if err:
                        print('warning: error running diff on file: %s: %s' % (path, err))
                        warnings = True
                        continue

                    output.write('file: ')
                    output.write(path)
                    output.write('\n')
                    output.write(diff)
                    output.write('\n')
                    output.write('\n')

        if warnings:
            print('There were problems running diff. Are you certain you specified the correct omni.ja?')

        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("resultspath", help="Path to file containing results of the omni analyzer")
    parser.add_argument("omnipath", help="Path to omni.ja for verification.")
    parser.add_argument("outputpath", help="File to store the diff results in ")
    parser.add_argument("--workdir", help="Directory to work in - will be removed",
        default=os.path.join(os.getcwd(), "omnidir"))
    args = parser.parse_args(argv[1:])
    omni_diff = OmniDiff(args.resultspath, args.omnipath, args.outputpath, args.workdir)
    omni_diff.run()

if __name__ == "__main__":
    main(sys.argv)
