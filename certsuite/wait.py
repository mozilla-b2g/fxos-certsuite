# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

class Wait(object):
    """An explicit conditional utility class for waiting until a condition
    evalutes to true or not null.

    """

    def __init__(self, timeout=120, interval=0.1):
        self.timeout = timeout
        self.interval = interval
        self.end = time.time() + self.timeout

    def until(self, condition):
        rv = None
        start = time.time()

        while not time.time() >= self.end:
            try:
                rv = condition()
            except (KeyboardInterrupt, SystemExit) as e:
                raise e

            if isinstance(rv, bool) and not rv:
                time.sleep(self.interval)
                continue

            if rv is not None:
                return rv

            time.sleep(self.interval)

        raise Exception(
            "Timed out after %s seconds" % ((time.time() - start)))
