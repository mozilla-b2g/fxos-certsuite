# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import json
import unittest


class TestLoader(unittest.loader.TestLoader):
    """Loads tests according to various criteria and returns them wrapped
    in `unittest.TestSuite`.

    Unlike `unittest.TestLoader` it allows forwarding construction
    arguments to the test case classes constructed herein.

    """

    def __init__(self, **kwargs):
        try:
            version = kwargs.pop('version')
        except:
            config_path = os.path.abspath(os.path.join(os.path.realpath(__file__), "../../../config.json"))
            with open(config_path) as f:
                config = json.load(f)
            version = config['version']
        super(TestLoader, self).__init__()
        self.opts = kwargs
        self.opts.update({'version': version})

    def loadTestsFromTestCase(self, klass):
        """Return a suite of all tests cases contained in ``klass``.

        This emulates the behaviour of the method it's overriding, but
        allows the keyword arguments passed in at construction time of
        this class to be forwarded to the test classes that it
        constructs.

        """

        if issubclass(klass, unittest.suite.TestSuite):
            raise TypeError("Test cases should not be derived from TestSuite")
        tc_names = super(TestLoader, self).getTestCaseNames(klass)
        if not tc_names and hasattr(klass, "runTest"):
            tc_names = ["runTest"]
        loaded_suite = super(TestLoader, self).suiteClass(
            map(self.class_wrapper(klass), tc_names))
        return loaded_suite

    def class_wrapper(self, klass):
        def rv(*args, **kwargs):
            kwargs = dict(self.opts.items() + kwargs.items())
            return klass(*args, **kwargs)
        return rv
