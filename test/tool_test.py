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
import io
import unittest

from columndet.tool import csv_det


class ToolTest(unittest.TestCase):
    def test_tool1(self):
        self.maxDiff = None
        meta_csv_data = csv_det("fixtures/csv/synthese-fra.csv")
        self.assertEqual(
            ['date/yyyy-MM-dd',
             'integer',
             'integer',
             'integer',
             'integer',
             'integer',
             'integer',
             'integer',
             'integer',
             'text',
             'text'],
            meta_csv_data.field_descriptions)
        out = io.StringIO()
        meta_csv_data.write(out)

        self.assertEqual("""domain,key,value
file,encoding,ascii
csv,double_quote,false
data,col/0/type,date/yyyy-MM-dd
data,col/1/type,integer
data,col/2/type,integer
data,col/3/type,integer
data,col/4/type,integer
data,col/5/type,integer
data,col/6/type,integer
data,col/7/type,integer
data,col/8/type,integer
""".replace("\n", "\r\n"), out.getvalue())

    def test_tool2(self):
        self.maxDiff = None
        meta_csv_data = csv_det("fixtures/csv/20201001-bal-216402149.csv")
        self.assertEqual(
            ['text',
             'text',
             'text',
             'integer',
             'text',
             'text',
             'text',
             'float//.',
             'float//.',
             'float//.',
             'float//.',
             'text',
             'date/yyyy-MM-dd',
             'text',
             'text',
             'text'],
            meta_csv_data.field_descriptions)
        out = io.StringIO()
        meta_csv_data.write(out)

        self.assertEqual("""domain,key,value
file,encoding,UTF-8-SIG
csv,delimiter,;
csv,double_quote,false
data,col/3/type,integer
data,col/7/type,float//.
data,col/8/type,float//.
data,col/9/type,float//.
data,col/10/type,float//.
data,col/12/type,date/yyyy-MM-dd
""".replace("\n", "\r\n"), out.getvalue())


if __name__ == '__main__':
    unittest.main()
