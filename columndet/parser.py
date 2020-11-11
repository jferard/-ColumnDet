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
import collections
from typing import (Optional, List, Collection, Counter)

from columndet import (ColumnInfos, OpCode, YMDBlockSniffer, HMSBlockSniffer,
                       FieldDescription, DateSniffer)
from columndet.booldet import BooleanSniffer
from columndet.datedet import (YMDColumnTypeSniffer, HMSColumnTypeSniffer,
                               DateFieldDescriptionFactory)
from columndet.field_description import (CurrencyDescription,
                                         PercentageDescription,
                                         BooleanDescription, TextDescription)
from columndet.floatdet import FloatParser
from columndet.lexer import (Lexer)
from columndet.util import (get_unique, get_some, TokenRow)


class RowsInfos:
    @staticmethod
    def create(non_empty_token_rows: List[TokenRow], threshold: float):
        sizes = collections.Counter([len(row) for row in non_empty_token_rows])
        first_opcodes = collections.Counter(
            [row.first_opcode for row in non_empty_token_rows])
        last_opcodes = collections.Counter(
            [row.last_opcode for row in non_empty_token_rows])
        return RowsInfos(sizes, first_opcodes, last_opcodes, threshold)

    def __init__(self, sizes: Counter[int],
                 first_opcodes: Counter[OpCode],
                 last_opcodes: Counter[OpCode], threshold: float):
        self.sizes = sizes
        self.first_opcodes = first_opcodes
        self.last_opcodes = last_opcodes
        self._threshold = threshold

    def get_unique_size(self) -> int:
        """
        :return: the size
        :raise ValueError: if this unique size does not exist.
        """
        return get_unique(self.sizes, self._threshold)

    def get_unique_last_opcode(self):
        return get_unique(self.last_opcodes, self._threshold)

    def get_two_uniques_last_opcodes(self):
        return get_some(self.last_opcodes, 2, self._threshold)

    def get_unique_first_opcode(self):
        return get_unique(self.first_opcodes, self._threshold)


class Parser:
    """
    The parser
    """

    @staticmethod
    def create(lexer: Optional[Lexer] = None, threshold: float = 0.95,
               prefer_dot_as_decimal_separator: bool = True):
        if lexer is None:
            lexer = Lexer()
        ymd_col_type_sniffer = YMDColumnTypeSniffer.create(threshold)
        hms_col_type_sniffer = HMSColumnTypeSniffer.create(threshold)
        return Parser(lexer, threshold, ymd_col_type_sniffer,
                      hms_col_type_sniffer, prefer_dot_as_decimal_separator)

    def __init__(self, lexer: Lexer, threshold: float,
                 ymd_col_type_sniffer: YMDColumnTypeSniffer,
                 hms_col_type_sniffer: HMSColumnTypeSniffer,
                 prefer_dot_as_decimal_separator: bool = True):
        self._lexer = lexer
        self._threshold = threshold
        self._ymd_col_type_sniffer = ymd_col_type_sniffer
        self._hms_col_type_sniffer = hms_col_type_sniffer
        self._prefer_dot_as_decimal_separator = prefer_dot_as_decimal_separator

    def parse(self, texts: List[str]) -> FieldDescription:
        token_rows = [self._lexer.lex(text.strip()) for text in texts]
        non_empty_token_rows = [TokenRow(r) for r in token_rows if r]
        if not non_empty_token_rows:
            return TextDescription.INSTANCE

        rows_infos = RowsInfos.create(non_empty_token_rows, self._threshold)
        try:
            unique_size = rows_infos.get_unique_size()
        except ValueError:
            return self._parse_unsized(rows_infos, non_empty_token_rows)
        else:
            try:
                return self._parse_sized(unique_size, non_empty_token_rows)
            except ValueError:
                return self._parse_unsized(rows_infos, non_empty_token_rows)

    def _parse_sized(self, row_size: int,
                     non_empty_token_rows: Collection[TokenRow]
                     ) -> FieldDescription:
        # col bet: bool, date, datetime *are* sized
        # (_currency, integer, float, _text, percentage *may be* sized)
        valid_token_rows = [r for r in non_empty_token_rows if
                            len(r) == row_size]
        if not valid_token_rows:
            raise ValueError(f"Too few valid tokens")

        if row_size == 1:
            return OneColumnSniffer(self._ymd_col_type_sniffer,
                                    self._hms_col_type_sniffer,
                                    valid_token_rows,
                                    self._threshold).sniff()
        else:
            return DateSniffer(self._ymd_col_type_sniffer,
                               self._hms_col_type_sniffer,
                               valid_token_rows,
                               self._threshold).sniff()

    def _parse_unsized(self, rows_infos: RowsInfos,
                       non_empty_token_rows: List[TokenRow]
                       ) -> FieldDescription:
        return UnsizedColumnSniffer(rows_infos, non_empty_token_rows,
                                    self._threshold,
                                    self._prefer_dot_as_decimal_separator).sniff()


class OneColumnSniffer:
    """
    A sniffer. Try to find the date_format of a one token field: a date, datetime or
    a boolean
    """

    def __init__(self, ymd_col_type_sniffer: YMDColumnTypeSniffer,
                 hms_col_type_sniffer: HMSColumnTypeSniffer,
                 token_rows: List[TokenRow], threshold: float):
        self._ymd_col_type_sniffer = ymd_col_type_sniffer
        self._hms_col_type_sniffer = hms_col_type_sniffer
        self._token_rows = token_rows
        self._threshold = threshold
        self._date_field_factory = DateFieldDescriptionFactory()

    def sniff(self) -> FieldDescription:
        rows = [tr.only for tr in self._token_rows]
        tokens_col = ColumnInfos.create(TokenRow(rows), None, self._threshold)
        opcode = tokens_col.unique_opcode
        if opcode == OpCode.NUMBER:
            out_tokens = self._sniff_dateblock_or_bool_01(tokens_col)
        elif opcode == OpCode.TEXT:
            out_tokens = self._sniff_bool_literal(tokens_col)
        else:
            raise ValueError()
        return out_tokens

    def _sniff_dateblock_or_bool_01(self,
                                    first: ColumnInfos) -> FieldDescription:
        width = first.unique_width
        if width == 1:
            if first.texts <= {"0", "1"}:
                return BooleanDescription("1", "0")
        elif width == 6 or width == 8:
            return self._date_field_factory.create(
                YMDBlockSniffer(self._ymd_col_type_sniffer,
                                first).sniff())
        elif width == 12 or width == 14:
            date, time = first.split_at(-6)
            sniff1 = YMDBlockSniffer(self._ymd_col_type_sniffer,
                                     date).sniff()
            sniff2 = HMSBlockSniffer(time).sniff()
            return self._date_field_factory.create(sniff1 + sniff2)

        raise ValueError()

    def _sniff_bool_literal(self, col: ColumnInfos) -> FieldDescription:
        texts = col.texts
        return BooleanSniffer(texts, self._threshold).sniff()


class UnsizedColumnSniffer:
    """
    A sniffer. Try to find the date_format of a sized field: a _currency, a float,
    an integer, a percentage or some _text.
    """

    def __init__(self, rows_infos: RowsInfos,
                 token_rows: List[TokenRow], threshold: float,
                 prefer_dot_as_decimal_separator: bool = True):
        self._rows_infos = rows_infos
        self._token_rows = token_rows
        self._threshold = threshold
        self._prefer_dot_as_decimal_separator = prefer_dot_as_decimal_separator

    def sniff(self) -> FieldDescription:
        try:
            first_opcode = self._rows_infos.get_unique_first_opcode()
        except ValueError:
            return TextDescription.INSTANCE
        else:
            try:
                last_opcode = self._rows_infos.get_unique_last_opcode()
            except ValueError:
                try:
                    last_opcodes = self._rows_infos.get_two_uniques_last_opcodes()
                except ValueError:
                    return TextDescription.INSTANCE
                else:
                    return self._sniff_one_first_two_last(first_opcode,
                                                          last_opcodes)
            else:
                return self._sniff_one_first_one_last(first_opcode, last_opcode)

    def _sniff_one_first_one_last(self, first_opcode: OpCode,
                                  last_opcode: OpCode) -> FieldDescription:
        if last_opcode == OpCode.NUMBER:
            if first_opcode == OpCode.NUMBER:
                return self._try_float_or_integer()
            elif first_opcode == OpCode.ANY_PERCENTAGE_SIGN:
                return self._try_pre_percentage()
            elif first_opcode == OpCode.ANY_CURRENCY_SIGN:
                return self._try_pre_currency()
            else:
                return TextDescription.INSTANCE
        elif last_opcode == OpCode.ANY_PERCENTAGE_SIGN:
            return self._try_post_percentage()
        elif last_opcode == OpCode.ANY_CURRENCY_SIGN:
            return self._try_post_currency()
        else:
            return TextDescription.INSTANCE

    def _sniff_one_first_two_last(self, first_opcode: OpCode,
                                  last_opcodes: Collection[OpCode]
                                  ) -> FieldDescription:
        if (set(last_opcodes) <= {
            OpCode.NUMBER,
            OpCode.ANY_NUMBER_SEPARATOR,
            OpCode.ANY_DATE_OR_NUMBER_SEPARATOR
        }):
            if first_opcode == OpCode.NUMBER:
                return self._try_float_or_integer()  # just try float?
            elif first_opcode == OpCode.ANY_PERCENTAGE_SIGN:
                return self._try_pre_percentage()
            elif first_opcode == OpCode.ANY_CURRENCY_SIGN:
                return self._try_pre_currency()
            else:
                return TextDescription.INSTANCE
        else:
            return TextDescription.INSTANCE

    def _try_float_or_integer(self) -> FieldDescription:
        return FloatParser(self._token_rows, self._threshold,
                           self._prefer_dot_as_decimal_separator).sniff()

    def _try_pre_percentage(self):
        sign = self._get_pre()
        rows = [row.lstrip(OpCode.ANY_PERCENTAGE_SIGN, OpCode.SPACE)
                for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()
        return PercentageDescription(True, sign, float_description)

    def _try_pre_currency(self):
        currency = self._get_pre()
        rows = [row.lstrip(OpCode.ANY_CURRENCY_SIGN, OpCode.SPACE)
                for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()

        return CurrencyDescription(True, currency, float_description)

    def _get_pre(self):
        values = collections.Counter(
            row.first_text for row in self._token_rows)
        try:
            value = get_unique(values)
        except ValueError:
            value = None
        return value

    def _try_post_percentage(self):
        sign = self._get_post()
        rows = [row.rstrip(OpCode.ANY_PERCENTAGE_SIGN, OpCode.SPACE)
                for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()
        return PercentageDescription(False, sign, float_description)

    def _try_post_currency(self):
        currency = self._get_post()
        rows = [row.rstrip(OpCode.ANY_CURRENCY_SIGN, OpCode.SPACE)
                for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()

        return CurrencyDescription(False, currency, float_description)

    def _get_post(self):
        values = collections.Counter(
            row.last_text for row in self._token_rows)
        try:
            value = get_unique(values)
        except ValueError:
            value = None
        return value
