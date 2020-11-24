# coding: utf-8

#  ColumnDet - A column type detector
#      Copyright (C) 2020 J. Férard <https://github.com/jferard>
#
#   This file is part of ColumnDet.
#
#   ColumnDet is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   ColumnDet is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os
from pathlib import Path

from columndet.parser import Parser


class FixtureTest(unittest.TestCase):
    def test_boolean(self):
        self.helper_test_dir(self._get_fixture("bool"))

    def test_currency(self):
        self.helper_test_dir(self._get_fixture("currency"))

    def test_date(self):
        self.helper_test_dir(self._get_fixture("date"))

    def test_datetime(self):
        self.helper_test_dir(self._get_fixture("datetime"))

    def test_float(self):
        self.helper_test_dir(self._get_fixture("float"))

    def test_integer(self):
        self.helper_test_dir(self._get_fixture("integer"))

    def test_percentage(self):
        self.helper_test_dir(self._get_fixture("percentage"))

    def test_text(self):
        self.helper_test_dir(self._get_fixture("text"))

    def test_failing(self):
        self.helper_test_dir(self._get_fixture("failing"))

    def helper_test_dir(self, dir_path):
        for p in Path(dir_path).glob("*.txt"):
            self.helper_test_a_path(p)

    def helper_test_a_path(self, p):
        if p.stem.startswith("FR"):
            parser = Parser.create(prefer_dot_as_decimal_separator=False)
        else:
            parser = Parser.create()
        with p.open("r", encoding='utf-8') as source:
            print(p)
            expected = next(source).strip("\n")
            self.assertEqual(expected, str(parser.parse(source)))

    def _get_fixture(self, fixture_name: str) -> str:
        return os.path.abspath(
        os.path.join(__file__, "../fixtures", fixture_name))

if __name__ == "__main__":
    unittest.main()

