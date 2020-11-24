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
#

import unittest

from columndet.field_description import TextDescription
from columndet.parser import Parser


class ColumnDetTest(unittest.TestCase):
    def test(self):
        parser = Parser.create()
        self.assertEqual("text", str(parser.parse(["entrée"] * 100)))

    def test2(self):
        parser = Parser.create()
        self.assertEqual("text", str(parser.parse(["64214_0010_00700"] * 100)))

    def test3(self):
        parser = Parser.create()
        self.assertEqual("date/yyyyMMdd", str(parser.parse(
            ['20200918', '20200920', '20200923', '20200927', '20200928',
             '20201001', '20201006', '20201011', '20201016', '20201021',
             '20201023', '20201024', '20201027', '20201028', '20201102',
             '20201104', '20201108', '20201111', '20201113', '20201117',
             '20201120', '20201124'])))


if __name__ == '__main__':
    unittest.main()
