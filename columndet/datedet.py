# coding:utf-8

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
from enum import Enum
from typing import (List, Optional, Sequence, Mapping, Collection, Iterable)

from columndet.field_description import (FieldDescription, DateDescription,
                                         DatetimeDescription)
# Types
from columndet.i18n import NAMES_BY_DATECODE_BY_LOCALE
from columndet.util import (LocaleType, ColumnInfos, OpCode, get_unique,
                            TokenRow)

DatePart = collections.namedtuple('DatePart', ['datecode', 'text', 'locale'])


class DateCode(Enum):
    YEAR_PART1 = 1
    YEAR_PART2 = 2

    YEAR = 100
    MONTH = 101
    DAY = 102
    HOURS = 103
    MINUTES = 104
    SECONDS = 105
    MILLISECONDS = 106
    TEXT = 107


class DateSniffer:
    """
    A sniffer. Try to find the date_format of a sized field: a date or a datetime.
    """

    def __init__(self, ymd_col_type_sniffer: "YMDColumnTypeSniffer",
                 hms_col_type_sniffer: "HMSColumnTypeSniffer",
                 token_rows: List[TokenRow], threshold: float):
        self._seen_datecodes = set()
        self._ymd_col_type_sniffer = ymd_col_type_sniffer
        self._hms_col_type_sniffer = hms_col_type_sniffer
        self._token_rows = token_rows
        self._threshold = threshold
        self._date_field_factory = DateFieldDescriptionFactory()

    def sniff(self) -> FieldDescription:
        tokens_cols = [ColumnInfos.create(ts, None, self._threshold) for ts
                       in zip(*self._token_rows)]
        ret_date_parts = []
        for tokens_col in tokens_cols:
            try:
                t = tokens_col.unique_token
            except ValueError:
                pass
            else:
                if t.opcode != OpCode.NUMBER:
                    if (t.opcode == OpCode.OPERATOR and (t.text == "+" or t.text == "-")
                            and self._ymd_known() and self._hms_known()):
                        ret_date_parts.append(
                            DatePart(DateCode.TEXT, "TZ", None))
                        break # TODO: could do better
                    else:
                        ret_date_parts.append(
                            DatePart(DateCode.TEXT, t.text, None))
                    continue

            date_part = None
            if self._ymd_known():
                if not (self._hms_known()
                        and DateCode.MILLISECONDS in self._seen_datecodes):
                    date_part = self._find_HMS(tokens_col)
            else:
                date_part = self._find_YMD(tokens_col)

            if date_part is None:
                date_part = DatePart(DateCode.TEXT,
                                     tokens_col.non_null_tokens.first_text, None)
            else:
                self._seen_datecodes.add(date_part.datecode)

            ret_date_parts.append(date_part)

        ret_date_parts = self._fix_types(ret_date_parts)
        counter = collections.Counter(
            t for t in ret_date_parts if t.datecode != DateCode.TEXT)
        if not counter:
            raise ValueError("Only text")
        if any(v > 1 for v in counter.values()):
            raise ValueError(str(counter))
        counter = collections.Counter(t.datecode for t in ret_date_parts if
                                      t.datecode not in (
                                          DateCode.TEXT, DateCode.DAY))
        if any(v > 1 for v in counter.values()):
            raise ValueError(str(counter))

        return self._date_field_factory.create(ret_date_parts)

    def _ymd_known(self):
        return ({DateCode.MONTH, DateCode.DAY} <= self._seen_datecodes
                and (DateCode.YEAR in self._seen_datecodes
                     or DateCode.YEAR_PART2 in self._seen_datecodes)
                )

    def _hms_known(self):
        return ({DateCode.HOURS, DateCode.MINUTES, DateCode.SECONDS}
                <= self._seen_datecodes)

    def _find_YMD(self, tokens_col: ColumnInfos) -> DatePart:
        try:
            date_part = self._ymd_col_type_sniffer.find_day_month_part(
                tokens_col)
        except ValueError:
            date_part = self._ymd_col_type_sniffer.find_yymd_col_part(
                tokens_col.texts)
        return date_part

    def _find_HMS(self, tokens_col: ColumnInfos) -> DatePart:
        try:
            date_part = self._hms_col_type_sniffer.find_hms(tokens_col)
        except ValueError:
            try:
                t = tokens_col.unique_token
            except ValueError:
                t = tokens_col.non_null_tokens[0]
            date_part = DatePart(DateCode.TEXT, t.text)
        return date_part

    def _fix_types(self, date_parts: List[DatePart]) -> List[DatePart]:
        return [DatePart(DateCode.YEAR, p.text)
                if p.datecode == DateCode.YEAR_PART2
                else p
                for p in date_parts]


class YMDColumnTypeSniffer:
    """
    A column sniffer. Takes a l
    """

    @staticmethod
    def create(threshold: float):
        return YMDColumnTypeSniffer(threshold, NAMES_BY_DATECODE_BY_LOCALE)

    def __init__(self, threshold: float, names_by_datecode_by_locale: Mapping[
        DateCode, Mapping[str, Mapping]]):
        self._threshold = threshold
        self._names_by_datecode_by_locale = names_by_datecode_by_locale

    def find_day_month_part(self, tokens_col: ColumnInfos) -> DatePart:
        """
        Find a literal day or a literal month.

        :param tokens_col: the tokens
        :return: a token representing the column
        :raise ValueError: if the columns is not a month.
        """
        if tokens_col.unique_opcode != OpCode.TEXT:
            raise ValueError()

        values = tokens_col.texts
        for locale, names_by_datecode in self._names_by_datecode_by_locale.items():
            for code, names in names_by_datecode.items():
                if values <= names:
                    datecode = self._get_datecode(code)
                    return DatePart(datecode, code, locale)
        raise ValueError

    def _get_datecode(self, code: str) -> DateCode:
        if code in {"mon", "month"}:
            datecode = DateCode.MONTH
        elif code in {"dy", "day"}:
            datecode = DateCode.DAY
        else:
            raise ValueError(f"Code: {code}")
        return datecode

    def find_ymd_col_part(self, values: Collection[str]) -> DatePart:
        size = min(len(v) for v in values)
        values = set(map(int, values))
        max_value = max(values)
        if 0 in values:
            return DatePart(DateCode.YEAR_PART2, 'y' * size, None)
        if len(values.symmetric_difference({18, 19, 20, 21})) <= 3:
            return DatePart(DateCode.YEAR_PART1, 'y' * size, None)
        if values <= {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}:
            return DatePart(DateCode.MONTH, 'MM', None)
        if max_value > 31:
            return DatePart(DateCode.YEAR_PART2, 'y' * size, None)
        if max_value > 12:
            return DatePart(DateCode.DAY, 'dd', None)

        raise ValueError

    def find_yymd_col_part(self, values: List[str]) -> DatePart:
        sizes = collections.Counter(len(v) for v in values)
        try:
            size = get_unique(sizes)
        except ValueError:  # day or month, but not year
            if max(sizes) == 2:
                min_value, max_value = self._get_min_max(values)
                return self._day_or_month(min_value, max_value)
        else:
            if size == 4:
                return DatePart(DateCode.YEAR, 'yyyy', None)
            elif size == 2:
                min_value, max_value = self._get_min_max(values)
                if min_value == 0 or max_value > 31:
                    return DatePart(DateCode.YEAR, 'yy', None)
                else:
                    return self._day_or_month(min_value, max_value)
        raise ValueError

    def _get_min_max(self, values):
        int_values = set(map(int, values))
        return min(int_values), max(int_values)

    def _day_or_month(self, m: int, M: int) -> DatePart:
        if 1 <= m <= M <= 12:
            return DatePart(DateCode.MONTH, 'MM', None)
        elif 12 < M <= 31:
            return DatePart(DateCode.DAY, 'dd', None)
        else:
            raise ValueError


class HMSColumnTypeSniffer:
    @staticmethod
    def create(threshold: float):
        return HMSColumnTypeSniffer(threshold)

    def __init__(self, threshold: float):
        self._threshold = threshold
        self._seen_datecodes = set()

    def find_hms(self, tokens_col: ColumnInfos) -> DatePart:
        assert tokens_col.unique_opcode == OpCode.NUMBER
        values = list(map(int, tokens_col.texts))
        min_v, max_v = min(values), max(values)
        t = None
        if DateCode.HOURS in self._seen_datecodes:
            if DateCode.MINUTES in self._seen_datecodes:
                if DateCode.SECONDS in self._seen_datecodes:
                    if 0 <= min_v and max_v < 1000:
                        t = DatePart(DateCode.MILLISECONDS, 'mmmm', None)
                elif 0 <= min_v and max_v < 60:
                    t = DatePart(DateCode.SECONDS, 'SS', None)
            elif 0 <= min_v and max_v < 60:
                t = DatePart(DateCode.MINUTES, 'MI', None)
        elif 0 <= min_v and max_v < 24:
            t = DatePart(DateCode.HOURS, 'HH', None)

        if t is None:
            raise ValueError("Time")
        else:
            self._seen_datecodes.add(t.datecode)
            return t


class DateFieldDescriptionFactory:
    def create(self, date_parts: Iterable[DatePart]) -> FieldDescription:
        locale = self._find_locale(date_parts)
        field_type = self._find_type(date_parts)
        text = self._find_text(date_parts)
        return field_type(text, locale)

    def _find_locale(self, date_parts: List[DatePart]) -> Optional[str]:
        for d in date_parts:
            if d.locale is not None:
                locale = d.locale
                break
        else:
            locale = None
        return locale

    def _find_type(self, date_parts: List[DatePart]) -> FieldDescription:
        field_type = DateDescription
        for d in date_parts:
            if d.datecode in {DateCode.HOURS, DateCode.MINUTES,
                              DateCode.SECONDS, DateCode.MILLISECONDS}:
                field_type = DatetimeDescription
        return field_type

    def _find_text(self, date_parts: List[DatePart]) -> str:
        return "".join(d.text.replace("/", "\\/") for d in date_parts)


class YMDBlockSniffer:
    """
    Sniff a simple column to find YYYYMMDD.
    Return the tokens or raise a ValueError.
    """

    def __init__(self, col_type_sniffer: YMDColumnTypeSniffer,
                 column: ColumnInfos):
        self._col_type_sniffer = col_type_sniffer
        self._column = column

    def sniff(self) -> List[DatePart]:
        size = self._column.unique_width
        if size == 8:
            return self._sniff8()
        elif size == 6:
            return self._sniff6()
        else:
            raise ValueError(f"Expected at least 6 digits, got {size}")

    def _sniff8(self) -> List[DatePart]:
        ds = self._column.texts
        twos = [[d[i:i + 2] for i in range(0, len(d), 2)] for d in ds]
        two_cols = map(set, zip(*twos))
        types = [self._col_type_sniffer.find_ymd_col_part(col) for col in
                 two_cols]
        return self._merge_types(types)

    def _sniff6(self) -> List[DatePart]:
        ds = self._column.texts
        twos = [[d[i:i + 2] for i in range(0, len(d), 2)] for d in ds]
        two_cols = list(map(set, zip(*twos)))
        types = [self._col_type_sniffer.find_ymd_col_part(col) for col in
                 two_cols]
        return self._merge_types(types)

    def _merge_types(self, ts: List[DatePart]) -> List[DatePart]:
        parts = []
        previous = None
        for t in ts:
            if t.datecode == DateCode.YEAR_PART1:
                pass
            elif (t.datecode == DateCode.YEAR_PART2 and previous is not None
                  and previous.datecode == DateCode.YEAR_PART1):
                parts.append(
                    DatePart(DateCode.YEAR, t.text + previous.text, None))
            elif t.datecode == DateCode.YEAR_PART2:
                parts.append(DatePart(DateCode.YEAR, t.text, None))
            else:
                parts.append(t)
            previous = t
        return parts


class HMSBlockSniffer:
    """
    Sniff a simple column to find HHMMSS.
    Return the tokens or raise a ValueError.
    """

    def __init__(self, column: ColumnInfos):
        self._column = column

    def sniff(self) -> List[DatePart]:
        size = self._column.unique_width
        if size == 6:
            return self._sniff6()
        else:
            raise ValueError("Expected at least 6 digits")

    def _sniff6(self) -> List[DatePart]:
        ds = self._column.texts
        hours, minutes, seconds = zip(
            *[[int(d[i:i + 2]) for i in range(0, len(d), 2)
               ] for d in ds])
        if (0 <= min(hours) and max(hours) < 24 and
                0 <= min(minutes) and max(minutes) < 60 and
                0 <= min(seconds) and max(seconds) < 60):
            return [DatePart(DateCode.HOURS, "HH", None),
                    DatePart(DateCode.MINUTES, "MI", None),
                    DatePart(DateCode.SECONDS, "SS", None)]
        else:
            raise ValueError("Bad minutes")
