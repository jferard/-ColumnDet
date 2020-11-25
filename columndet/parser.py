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
from typing import (Optional, List, Collection, Counter, Callable)

from columndet import (ColumnInfos, OpCode, YMDBlockSniffer, HMSBlockSniffer,
                       FieldDescription, DateSniffer)
from columndet.booldet import BooleanSniffer
from columndet.datedet import (YMDColumnTypeSniffer, HMSColumnTypeSniffer,
                               DateFieldDescriptionFactory)
from columndet.field_description import (CurrencyDescription,
                                         PercentageDescription,
                                         BooleanDescription, TextDescription,
                                         IntegerDescription, DateDescription,
                                         DatetimeDescription)
from columndet.floatdet import FloatParser
from columndet.i18n import DECIMAL_SEPARATORS, PERCENTAGE_SIGNS, \
    CURRENCY_SYMBOLS, CURRENCY_CODES
from columndet.lexer import (Lexer)
from columndet.util import (get_unique, get_some, TokenRow, Token)


class RowsInfos:
    @staticmethod
    def create(non_empty_token_rows: List[TokenRow], threshold: float):
        sizes = collections.Counter([len(row) for row in non_empty_token_rows])
        return RowsInfos(non_empty_token_rows, sizes, threshold)

    def __init__(self, non_empty_token_rows: List[TokenRow],
                 sizes: Counter[int],
                 threshold: float):
        self._non_empty_token_rows = non_empty_token_rows
        self.sizes = sizes
        self._threshold = threshold

    def get_unique_size(self) -> int:
        """
        :return: the size
        :raise ValueError: if this unique size does not exist.
        """
        return get_unique(self.sizes, self._threshold)

    def first_matches(self, func: Callable[[Token], bool]) -> bool:
        count = sum(1 for tr in self._non_empty_token_rows if func(tr.first()))
        return count > self._threshold * len(self._non_empty_token_rows)

    def last_matches(self, func: Callable[[Token], bool]) -> bool:
        count = sum(1 for tr in self._non_empty_token_rows if func(tr.last()))
        return count > self._threshold * len(self._non_empty_token_rows)


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
            try:
                return self._parse_unsized(rows_infos, non_empty_token_rows)
            except ValueError:
                return TextDescription.INSTANCE
        else:
            try:
                return self._parse_sized(unique_size, non_empty_token_rows)
            except ValueError:
                try:
                    return self._parse_unsized(rows_infos, non_empty_token_rows)
                except ValueError:
                    return TextDescription.INSTANCE

    def _parse_sized(self, row_size: int,
                     non_empty_token_rows: Collection[TokenRow]
                     ) -> FieldDescription:
        # col bet: bool, date, datetime *are* sized
        # (currency, integer, float, _text, percentage *may be* sized)
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
        """
        Return the field description of this one token-column.
        Does not raise any exception because we can always decide the type.

        :return: the field description
        """
        rows = [tr.only for tr in self._token_rows]
        tokens_col = ColumnInfos.create(TokenRow(rows), None, self._threshold)
        opcode = tokens_col.unique_opcode
        if opcode == OpCode.NUMBER:
            try:
                description = self._sniff_dateblock_or_bool_01(tokens_col)
            except ValueError:
                try:
                    tokens_col.unique_width
                except ValueError:
                    description = IntegerDescription.INSTANCE
                else:
                    if any(t[0] == "0" and len(t) > 1 for t in
                           tokens_col.texts):
                        description = TextDescription.INSTANCE
                    else:
                        description = IntegerDescription.INSTANCE
        elif opcode == OpCode.TEXT:
            try:
                description = self._sniff_bool_literal(tokens_col)
            except ValueError:
                description = TextDescription.INSTANCE
        else:
            description = TextDescription.INSTANCE
        return description

    def _sniff_dateblock_or_bool_01(self,
                                    first: ColumnInfos) -> FieldDescription:
        width = first.unique_width
        if width == 1:
            if first.texts <= {"0", "1"}:
                return BooleanDescription("1", "0")
        elif width == 6 or width == 8:
            return DateDescription(
                YMDBlockSniffer(self._ymd_col_type_sniffer,
                                first).sniff(), None)
        elif width == 12 or width == 14:
            date, time = first.split_at(-6)
            sniff1 = YMDBlockSniffer(self._ymd_col_type_sniffer,
                                     date).sniff()
            sniff2 = HMSBlockSniffer(time).sniff()
            return DatetimeDescription(sniff1 + sniff2, None)

        raise ValueError()

    def _sniff_bool_literal(self, col: ColumnInfos) -> FieldDescription:
        texts = col.texts
        return BooleanSniffer(texts, self._threshold).sniff()


class UnsizedColumnSniffer:
    """
    A sniffer. Try to find the date_format of an unsized sized field:
     currency, a float, an integer, a percentage or some text.
    """

    def __init__(self, rows_infos: RowsInfos,
                 token_rows: List[TokenRow], threshold: float,
                 prefer_dot_as_decimal_separator: bool = True):
        self._rows_infos = rows_infos
        self._token_rows = token_rows
        self._threshold = threshold
        self._prefer_dot_as_decimal_separator = prefer_dot_as_decimal_separator

    def sniff(self) -> FieldDescription:
        if self._rows_infos.last_matches(lambda t: (
                t.opcode == OpCode.NUMBER or t.text in DECIMAL_SEPARATORS)):
            if self._rows_infos.first_matches(
                    lambda t: t.opcode == OpCode.NUMBER or t.text in {"-",
                                                                      "+"}):
                return self._try_float_or_integer()
            elif self._rows_infos.first_matches(
                    lambda t: t.text in PERCENTAGE_SIGNS):
                return self._try_pre_percentage()
            elif self._rows_infos.first_matches(lambda t: (
                    t.text in CURRENCY_SYMBOLS or t.text in CURRENCY_CODES)):
                return self._try_pre_currency()
            else:
                return TextDescription.INSTANCE
        elif self._rows_infos.last_matches(
                lambda t: t.text in PERCENTAGE_SIGNS):
            return self._try_post_percentage()
        elif self._rows_infos.last_matches(lambda t: (
                t.text in CURRENCY_SYMBOLS or t.text in CURRENCY_CODES)):
            return self._try_post_currency()
        else:
            return TextDescription.INSTANCE

    def _try_float_or_integer(self) -> FieldDescription:
        return FloatParser(self._token_rows, self._threshold,
                           self._prefer_dot_as_decimal_separator).sniff()

    def _try_pre_percentage(self):
        sign = self._get_pre()
        rows = [row.lstrip(
            lambda t: (t.opcode == OpCode.SPACE or t.text in PERCENTAGE_SIGNS))
            for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()
        return PercentageDescription(True, sign, float_description)

    def _try_pre_currency(self):
        currency = self._get_pre()
        rows = [row.lstrip(lambda t: (
                t.opcode == OpCode.SPACE or t.text in CURRENCY_SYMBOLS or t.text in CURRENCY_CODES))
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
        rows = [row.rstrip(
            lambda t: (t.opcode == OpCode.SPACE or t.text in PERCENTAGE_SIGNS))
            for row in self._token_rows]
        float_description = FloatParser(rows, self._threshold,
                                        self._prefer_dot_as_decimal_separator).sniff()
        return PercentageDescription(False, sign, float_description)

    def _try_post_currency(self):
        currency = self._get_post()
        rows = [row.rstrip(lambda t: (
                t.opcode == OpCode.SPACE or t.text in CURRENCY_SYMBOLS or t.text in CURRENCY_CODES))
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
