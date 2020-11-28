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
from typing import Set

from mcsv.meta_csv_data import FieldDescription, BooleanDescription
from columndet.i18n import TRUE_FALSE_BY_LOCALE_NAME
from columndet.util import get_some


class BooleanSniffer:
    def __init__(self, texts: Set[str], threshold: float):
        self._texts = texts
        self._threshold = threshold

    def sniff(self) -> FieldDescription:
        counter = collections.Counter(self._texts)
        t_f = get_some(counter, 2, self._threshold)
        if t_f:
            # can't create the reverse dict because of UTF-8
            for locale_name, locale_t_f in TRUE_FALSE_BY_LOCALE_NAME.items():
                if set(t_f) <= set(locale_t_f):
                    return BooleanDescription(*locale_t_f)

            raise ValueError()
        else:
            raise ValueError("Empty int_values")  # should not happen
