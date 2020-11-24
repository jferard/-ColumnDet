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
import typing
from pathlib import Path
from typing import Union, Tuple, Optional

import chardet
import csv

from columndet.parser import Parser


class MetaCSVData:
    def __init__(self, path: Path, encoding: str, dialect: csv.Dialect,
                 header: Tuple[str], field_descriptions: Tuple[str]):
        self.path = path
        self.encoding = encoding
        self.dialect = dialect
        self.header = header
        self.field_descriptions = list(field_descriptions)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.field_descriptions[key] = value
        else:
            try:
                i = self.header.index(key)
            except ValueError:
                pass
            else:
                self.field_descriptions[i] = value

    def write(self, path: Optional[
        Union[str, Path, typing.TextIO, typing.BinaryIO]] = None, minimal=True):
        if isinstance(path, io.TextIOBase):
            self._write(path, minimal)
        elif isinstance(path, (io.RawIOBase, io.BufferedIOBase)):
            self._write(io.TextIOWrapper(path, encoding="utf-8", newline="\r\n"
                                         ), minimal)
        else:
            if path is None:
                path = self.path.with_suffix(".mcsv")
            elif isinstance(path, str):
                path = Path(path)

            with path.open("w", newline="\r\n") as dest:
                self._write(dest, minimal)

    def _write(self, dest, minimal):
        writer = csv.writer(dest)
        writer.writerow(["domain", "key", "value"])
        if not minimal or self.encoding.casefold() != "utf-8":
            writer.writerow(["file", "encoding", self.encoding])
        if not minimal or self.dialect.lineterminator != "\r\n":
            writer.writerow(
                ["file", "line_terminator", self.dialect.lineterminator])
        if not minimal or self.dialect.delimiter != ",":
            writer.writerow(["csv", "delimiter", self.dialect.delimiter])
        if not minimal or not self.dialect.doublequote:
            writer.writerow(["csv", "double_quote", str(
                bool(self.dialect.skipinitialspace)).lower()])
        if not minimal or self.dialect.escapechar:
            writer.writerow(["csv", "escape_char", self.dialect.escapechar])
        if not minimal or self.dialect.quotechar != '"':
            writer.writerow(["csv", "quote_char", self.dialect.quotechar])
        if not minimal or self.dialect.skipinitialspace:
            writer.writerow(["csv", "skip_initial_space", str(
                bool(self.dialect.skipinitialspace)).lower()])
        for i, value in enumerate(self.field_descriptions):
            if not minimal or value != "text":
                writer.writerow(["data", f"col/{i}/type", value])


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
                           tuple(str(parser.parse(col)) for col in cols))
