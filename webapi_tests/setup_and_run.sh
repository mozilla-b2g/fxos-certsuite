#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

source setup_venv.sh
echo "Installing Certified App"
fxos_appgen --install --type=certified --version=1.3 --all-permissions "CertTest App"
adb forward tcp:2828 tcp:2828
echo "Done, running the suite"
webapirunner
deactivate
