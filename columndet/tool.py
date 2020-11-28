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
#
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
import io
from pathlib import Path
from typing import Union

import chardet
import csv

from mcsv.meta_csv_data import MetaCSVData
from columndet.parser import Parser


def csv_det(path: Union[str, Path], chunk_size=1024 * 1024,
            threshold: float = 0.95,
            prefer_dot_as_decimal_separator: bool = True
            ) -> MetaCSVData:
    """
    Detect a csv format.

    :param path:
    :param chunk_size:
    :param threshold:
    :param prefer_dot_as_decimal_separator:
    :return:
    """
    if isinstance(path, str):
        path = Path(path)

    with path.open("rb") as source:
        data = source.read(chunk_size)
        encoding = chardet.detect(data)["encoding"]
        data_str = data.decode(encoding, errors='ignore')
        dialect = csv.Sniffer().sniff(data_str)

        reader = csv.reader(io.StringIO(data_str), dialect)
        header = next(reader)
        parser = Parser.create(threshold=threshold,
                               prefer_dot_as_decimal_separator=
                               prefer_dot_as_decimal_separator)
        cols = list(zip(*reader))
        return MetaCSVData(path, encoding, dialect(), header,
                           tuple(parser.parse(col) for col in cols))
