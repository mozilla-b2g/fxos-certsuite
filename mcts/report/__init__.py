# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozlog.structured import (
    structuredlog,
    handlers,
    formatters,
    reader,
)

import results
import subsuite
import summary

def parse_log(path):
    with open(path) as f:
        regression_handler = results.LogHandler()
        reader.handle_log(reader.read(f),
                          regression_handler)
        return regression_handler.results
