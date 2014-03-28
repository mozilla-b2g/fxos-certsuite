# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from testcase import TestCase


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

    @unittest.expectedFailure
    def test_instruct_cancel(self):
        self.instruct("Click cancel")

    def test_confirm(self):
        self.confirm("Click Yes")

    @unittest.expectedFailure
    def test_confirm_no(self):
        self.confirm("Click No")
