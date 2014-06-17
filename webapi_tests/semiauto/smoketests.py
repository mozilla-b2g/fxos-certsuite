# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from webapi_tests.semiauto import TestCase


class Smoketests(TestCase):
    def test_prompt(self):
        answer = self.prompt("Enter \"foo\"")
        self.assertEqual(answer, "foo")

    def test_prompt_number(self):
        answer = self.prompt("Enter 42")
        self.assertEqual(answer, "42")

    def test_prompt_empty(self):
        answer = self.prompt("Click OK")
        self.assertIsNone(answer)

    def test_instruct(self):
        self.instruct("Click OK")

    def test_instruct_cancel(self):
        with self.assertRaises(Exception):
            self.instruct("Click cancel")

    def test_confirm(self):
        self.confirm("Click Yes")

    def test_confirm_no(self):
        with self.assertRaises(Exception):
            self.confirm("Click No")

    def test_long_response(self):
        msg = "o" * 200
        resp = self.prompt(
            "Copy this exact string into the text field below: \"%s\"" % msg)
        self.assertEqual(resp, msg)

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.instruct("Click cancel")

    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.instruct("Click OK")

    @unittest.skip("This test should be marked as skipped.")
    def test_skip(self):
        pass
