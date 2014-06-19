# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

"""Shim to allow ``python -m semiauto``.  Only works in Python 2.7+."""

import sys

from webapi_tests.semiauto import main

if __name__ == "__main__":
    main(sys.argv)
