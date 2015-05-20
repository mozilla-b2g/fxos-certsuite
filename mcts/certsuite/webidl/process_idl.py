#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import os
import re
import sys

# Map to types recognized by the idlharness.js tests
typenames = {
    "Boolean" : "boolean",
    "Double" : "double",
    "UnrestrictedDouble" : "double",
}

def jsonify_interface(intf):
    result = {}

    result['name'] = intf.identifier.name
    result['type'] = "interface"
    result['extAttrs'] = []

    # nothing further for externals
    if intf.isExternal():
        return result

    # there doesn't seem to be a clean way to test for this
    try:
        result['partial'] = intf._isPartial
    except AttributeError:
        result['partial'] = False

    members = []
    for intf_member in intf.members:
        member = {}
        member['extAttrs'] = []
        if intf_member.isAttr():
            member['name'] = intf_member.identifier.name
            member['type'] = 'attribute'
            member['readonly'] = intf_member.readonly
            member['idlType'] = jsonify_type(intf_member.type)
        elif intf_member.isMethod():
            member['name'] = intf_member.identifier.name
            member['type'] = 'operation'
            member['getter'] = intf_member.isGetter()
            member['setter'] = intf_member.isSetter()
            member['creator'] = intf_member.isCreator()
            member['deleter'] = intf_member.isDeleter()
            member['stringifier'] = intf_member.isStringifier()
            member['jsonofier'] = intf_member.isJsonifier()
            member['legacycaller'] = intf_member.isLegacycaller()

            overloads = intf_member.signatures()
            for overload in overloads:
                ret = overload[0]
                member['idlType'] = jsonify_type(ret)
                args = overload[1]
                arguments = []
                for arg in args:
                    argument = {}
                    argument['name'] = arg.identifier.name
                    argument['optional'] = False #TODO
                    argument['variadic'] = False #TODO
                    argument['idlType'] = jsonify_type(arg.type)
                    arguments.append(argument)
                member['arguments'] = arguments
                # idlharness can only handle one overload at the moment
                break

        members.append(member)
    result['members'] = members

    return json.dumps(result)

def jsonify_type(t):
    result = {}
    result['sequence'] = t.isSequence()
    result['nullable'] = t.nullable()
    result['array'] = t.isArray()
    result['union'] = t.isUnion()
    result['idlType'] = typenames.get(str(t), str(t))
    return result

def jsonify_typedef(typedef):
    result = {}

    result['name'] = typedef.identifier.name
    result['type'] = "typedef"
    result['extAttrs'] = []

    return json.dumps(result)

def main(argv):
    """
    This parses a json manifest file containing list of webidl files and
    generates a file containing javascript arrays of json objects for
    each webidl file.

    usage: process_idl.py manifest.json ~/B2G

    The generated js file can then be included with the test app.
    """

    argparser = argparse.ArgumentParser()
    argparser.add_argument("manifest", help="Manifest file for the idl")
    argparser.add_argument("b2g", help="Path to b2g directory (e.g. ~/B2G")
    args = argparser.parse_args(argv[1:])

    with open(args.manifest, 'r') as f:
        manifest = json.loads(f.read())

    # import WebIDL using a path relative to the gecko tree
    sys.path.append(os.path.join(args.b2g, 'gecko', 'dom', 'bindings', 'parser'))
    import WebIDL

    parser = WebIDL.Parser()

    webidl_path = args.b2g

    # embed idl files in individual script tags
    for filename in manifest['files']:
        path = os.path.realpath(os.path.join(webidl_path, filename))
        with open(path, 'r') as f:
            parser.parse(''.join([line for line in f.readlines() if not line.startswith('#')]))

    results = parser.finish()
    tested = []
    untested = []
    for result in results:
        if isinstance(result, WebIDL.IDLImplementsStatement):
            continue

        if isinstance(result, WebIDL.IDLTypedefType):
            tested.append(jsonify_typedef(result))
            continue

        if result.isInterface():

            if result.isExternal():
                continue

            print(result.identifier.name)
            if result.identifier.name in manifest['untested']:
                untested.append(jsonify_interface(result))
            else:
                tested.append(jsonify_interface(result))

    with open('merged_idl.js', 'w') as merged:
        merged.write('TESTED_IDL=')
        merged.write(json.dumps(tested))
        merged.write(';\n')
        merged.write('UNTESTED_IDL=')
        merged.write(json.dumps(untested))
        merged.write(';\n')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
