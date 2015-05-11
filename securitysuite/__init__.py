# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# The "securitycli" entry point for setuptools is imported from suite.py
from suite import *

# Import all available test groups (one group per module) here:
import filesystem
import ssl
import kernel
