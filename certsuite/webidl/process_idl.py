#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import os
import re
import sys

def preprocess(f, defines):
    """Run preprocessor on file using specified defines"""

    skip = False
    lines = []
    for line in f:
        if line.startswith('#'):
            m = re.match('#ifdef (\w+)', line)
            if m:
                define = m.group(1)
                if not define in defines:
                    # Skip lines until we see an #endif
                    # TODO: handle nesting
                    skip = True
            if line.startswith('#endif'):
                skip = False
        elif not skip:
            lines.append(line)

    return lines

def remove_bodyless_interfaces(lines):
    return [line for line in lines if not re.match('interface\s+\w+\s*;', line)]

def main(argv):
    """
    This parses a json manifest file containing list of webidl files and
    generates a file containing one script tag for each webidl file.

    usage: process_idl.py manifest.json ~/B2G/gecko/dom/webidl

    The generated html file can then be appended to the test app.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", help="Manifest file for the idl")
    parser.add_argument("webidlpath", help="Path to webidl directory (e.g. gecko/dom/webidl")
    args = parser.parse_args(argv[1:])

    with open(args.manifest, 'r') as f:
        manifest = json.loads(f.read())

    merged = open('merged_idl.html', 'w')

    # embed idl files in individual script tags
    for filename in manifest['files']:
        with open(os.path.join(args.webidlpath, filename), 'r') as f:
            lines = preprocess(f, manifest['defines'])
            lines = remove_bodyless_interfaces(lines)
            merged.write('<script id="' + filename + '" class="idl" type="text/plain">\n')
            merged.write(''.join(lines))
            merged.write('</script>\n')

    # generate empty interfaces for interfaces we will not test 
    for interface in manifest['untested']:
        merged.write('<script class="untested" type="text/plain">\n')
        merged.write('interface ' + interface + ' {};\n')
        merged.write('</script>\n')

    merged.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
