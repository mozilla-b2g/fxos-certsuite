#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

echo "Setting up virtualenv"

sh `dirname ${0}`/prerun.sh

source certsuite_venv/bin/activate
python setup.py install
echo "Done, running the suite"
runcertsuite $@
deactivate
