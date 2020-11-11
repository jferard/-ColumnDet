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

from typing import Optional


class FieldDescription:
    @staticmethod
    def _none_to_empty(value):
        return "" if value is None else value


class BooleanDescription(FieldDescription):
    def __init__(self, true_word: str, false_word: str):
        self._true_word = true_word
        self._false_word = false_word

    def __str__(self):
        return f"boolean/{self._true_word}/{self._false_word}"


class CurrencyDescription(FieldDescription):
    def __init__(self, pre: bool, currency: Optional[str],
                 float_description: "FloatDescription"):
        self._pre = pre
        self._currency = currency
        self._float_description = float_description

    def __str__(self):
        pre = "pre" if self._pre else "post"
        return f"currency/{pre}/{self._none_to_empty(self._currency)}/{self._float_description}"


class DateDescription(FieldDescription):
    def __init__(self, format: str, locale_name: Optional[str]):
        self._format = format
        self._locale_name = locale_name

    def __str__(self):
        if self._locale_name is None:
            return f"date/{self._format}"
        else:
            return f"date/{self._format}/{self._locale_name}"


class DatetimeDescription(FieldDescription):
    def __init__(self, format: str, locale_name: Optional[str]):
        self._format = format
        self._locale_name = locale_name

    def __str__(self):
        if self._locale_name is None:
            return f"datetime/{self._format}"
        else:
            return f"datetime/{self._format}/{self._locale_name}"


class FloatDescription(FieldDescription):
    def __init__(self, thousand_sep: Optional[str], decimal_sep: str):
        self._thousand_sep = thousand_sep
        self._decimal_sep = decimal_sep

    def __str__(self):
        return f"float/{self._none_to_empty(self._thousand_sep)}/{self._decimal_sep}"


class IntegerDescription(FieldDescription):
    def __init__(self, thousand_sep: Optional[str] = None):
        self._thousand_sep = thousand_sep

    def __str__(self):
        if self._thousand_sep is None:
            return f"integer"
        else:
            return f"integer/{self._none_to_empty(self._thousand_sep)}"


class PercentageDescription(FieldDescription):
    def __init__(self, pre: bool, sign: Optional[str],
                 float_description: FieldDescription):
        self._pre = pre
        self._sign = sign
        self._float_description = float_description

    def __str__(self):
        pre = "pre" if self._pre else "post"
        return f"percentage/{pre}/{self._none_to_empty(self._sign)}/{self._float_description}"


class TextDescription(FieldDescription):
    def __str__(self):
        return "text"


TextDescription.INSTANCE = TextDescription()
