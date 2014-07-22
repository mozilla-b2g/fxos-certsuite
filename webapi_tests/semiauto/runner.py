# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import unittest

def serialize_suite(tests, ov=[]):
    """Serialize a ``unittest.TestSuite`` instance for transportation
    across the wire.

    Tests are represented by their hash as we have no desire to
    replicate the full Test instance object on the client side.

    :param tests: Instance of ``unittest.suite.TestSuite`` to be
        serialized.

    :returns: List of test dicts represented by `id` and
        `description`.

    """

    rv = ov
    if isinstance(tests, collections.Iterable):
        # [TestCase, ...] or [<TestSuite ...>, <TestSuite ...>]
        for test in tests:
            if isinstance(test, unittest.suite.TestSuite):
                rv = serialize_suite(test, rv)
            else:
                rv.append(test.id())
    elif hasattr(tests, "_tests"):
        # <unittest.suite.TestSuite _tests=[...]>
        rv = serialize_suite(tests._tests, rv)

    return rv
