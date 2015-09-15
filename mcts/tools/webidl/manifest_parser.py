#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import re
import sys

from os import listdir
from os.path import isfile, join

def main(argv):
    """
    This will generate you a manifest file, and you need to modify it!
    There are three category: files, untested, skipped.
    You can reference current manifest.json.

    usage: manifest_parser.py (GECKO LOCATION: /B2G/gecko/dom/webidl)

    The generated file can then be used with process_idl.py
    """

    argparser = argparse.ArgumentParser()
    argparser.add_argument("gecko", help="/B2G/gecko/dom/webidl")
    args = argparser.parse_args(argv[1:])

    files = [ "gecko/dom/webidl/" + f for f in listdir(args.gecko) if isfile(join(args.gecko,f)) and f.endswith("webidl") ]
    files.sort()

    with open('manifest_generated.json', 'w') as merged:
        merged.write('{\n  "files": [\n')
        merged.write("    \"" + "\",\n    \"".join(files) + "\"\n")
        merged.write('  ],\n  "untested": [\n  ],\n  "skipped": [\n  ]\n}\n')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
