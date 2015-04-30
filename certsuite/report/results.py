# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import defaultdict

from mozlog.structured import reader


result_status = dict((v,k) for k,v in
                     enumerate(["PASS", "FAIL", "OK", "SKIP", "ERROR", "TIMEOUT", "CRASH"]))

KEY_MAIN = 'MAIN'

def is_skip(data):
    return data['status'] == 'SKIP'

def is_regression(data):
    if "expected" not in data:
        return False

    return result_status[data["status"]] > result_status[data["expected"]]

class LogHandler(reader.LogHandler):
    def __init__(self):
        self.results = Results()

    def suite_start(self, data):
        self.results.name = data["source"]

    def test_id(self, data):
        if isinstance(data["test"], unicode):
            return data["test"]
        else:
            return tuple(data["test"])

    def test_status(self, data):
        test_id = self.test_id(data)

        if data["status"] == 'FAIL':
            self.results.fails = self.results.fails + 1

        self.results.regressions[test_id][data["subtest"]] = data

    def test_end(self, data):
        test_id = self.test_id(data)

        if data["status"] == 'FAIL':
            self.results.fails = self.results.fails + 1

        self.results.regressions[test_id][KEY_MAIN] = data

    def log(self, data):
        if data["level"] in ("ERROR", "CRITICAL"):
            self.results.errors.append(data)

class Results(object):
    def __init__(self):
        self.name = None
        self.regressions = defaultdict(dict)
        self.errors = []
        self.map = {}
        self.fails = 0

    @property
    def is_pass(self):
        return not (self.has_regressions or self.has_errors)

    @property
    def has_regressions(self):
        return len(self.regressions) > 0

    @property
    def has_fails(self):
        return self.fails > 0

    @property
    def has_errors(self):
        return len(self.errors) > 0

    def has(self, key):
        return key in self.map.keys()

    def set(self, key, value):
        self.map[key] = value

    def get(self, key):
        return self.map[key] if self.has(key) else None
