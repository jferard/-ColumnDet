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

from pathlib import Path

from columndet.parser import Parser


class DateDetTest(unittest.TestCase):
    def test_date(self):
        for p in Path("fixtures/date").glob("*.txt"):
            self.helper_test_a_path(p)

    def test_float(self):
        for p in Path("fixtures/float").glob("*.txt"):
            self.helper_test_a_path(p)

    def test_boolean(self):
        for p in Path("fixtures/bool").glob("*.txt"):
            self.helper_test_a_path(p)

    def test_currency(self):
        for p in Path("fixtures/currency").glob("*.txt"):
            self.helper_test_a_path(p)

    def test_percentage(self):
        for p in Path("fixtures/percentage").glob("*.txt"):
            self.helper_test_a_path(p)

    def test_failing(self):
        for p in Path("fixtures/failing").glob("*.txt"):
            self.helper_test_a_path(p)

    def helper_test_a_path(self, p):
        parser = Parser.create(locale_names=['fr_FR', 'en_US'])
        with p.open("r", encoding='utf-8') as source:
            print(p)
            expected = next(source).strip()
            self.assertEqual(expected, str(parser.parse(source)))


if __name__ == "__main__":
    unittest.main()

