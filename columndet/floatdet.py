# encoding: utf-8

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
import collections
from typing import List

from columndet import OpCode, FieldDescription
from columndet.field_description import FloatDescription, IntegerDescription
from columndet.util import (get_unique, get_some, TokenRow)


class FloatParser:
    def __init__(self, token_rows: List[TokenRow], threshold: float):
        self._token_rows = token_rows
        self._threshold = threshold
        self._errors = 0
        self._last_sep = collections.Counter()
        self._other_sep = collections.Counter()

    def sniff(self) -> FieldDescription:
        for row in self._token_rows:
            if len(row) == 1:
                continue
            self._sniff_row(row)
        if 1 - self._errors / len(self._token_rows) < self._threshold:
            pass  # raise ValueError(f"Errors: {self._errors} out of {len(self._token_rows)}")

        try:
            thousands_sep = get_unique(self._other_sep, self._threshold)
        except ValueError:
            thousands_sep = None

        dec_seps = get_some(self._last_sep, 2, self._threshold)
        if dec_seps:
            return FloatDescription(thousands_sep, dec_seps[0])
        elif thousands_sep is not None:
            return IntegerDescription(thousands_sep)
        else:
            return IntegerDescription()

    def _sniff_row(self, row: TokenRow):
        row = self._store_last_sep(row)
        self._store_other_sep(row)

    def _store_last_sep(self, row: TokenRow) -> TokenRow:
        # strip the last number
        assert len(row) >= 2
        if row.last_opcode == OpCode.NUMBER:
            row.pop()  # remove number
        assert row
        if (row.last_opcode == OpCode.ANY_NUMBER_SEPARATOR
                or row.last_opcode == OpCode.ANY_DATE_OR_NUMBER_SEPARATOR):
            self._last_sep[row.last_text] += 1  # store the value
            row.pop()  # remove value
        else:
            self._errors += 1

        return row

    def _store_other_sep(self, row: TokenRow):
        while row:
            # check for the size of numbers (groups of 3)
            if row.last_opcode != OpCode.NUMBER:
                self._errors += 1
                return
            elif row and len(row.last_text) != 3:
                self._errors += 1
                return
            elif len(row) <= 1:
                return
            row.pop()  # remove number

            if (row.last_opcode == OpCode.ANY_NUMBER_SEPARATOR
                    or row.last_opcode == OpCode.ANY_DATE_OR_NUMBER_SEPARATOR):
                self._other_sep[row.last_text] += 1
            elif row.last_opcode == OpCode.SPACE:
                self._other_sep[' '] += 1
            row.pop()  # remove value
