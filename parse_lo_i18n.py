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
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import collections

if len(sys.argv) != 2:
    raise Exception("First arg should be a path to i18npool/source/localedata/data directory of LibreOffice.")
else:
    source = sys.argv[1]

true_false_by_locale = {}
number_seps = collections.Counter()
datetime_seps = collections.Counter()
curr_codes = collections.Counter()
curr_symbols = collections.Counter()
names_by_datecode_by_locale = {}

for source in Path(source).glob("*.xml"):
    tree = ET.parse(source)
    root = tree.getroot()
    for separators in root.findall("./LC_MISC/ReservedWords"):
        true_false_by_locale[source.stem] = (
            separators.find("trueWord").text.casefold(),
            separators.find("falseWord").text.casefold())
    for separators in root.findall("./LC_CTYPE/Separators"):
        number_seps[separators.find("ThousandSeparator").text.casefold()] += 1
        number_seps[separators.find("DecimalSeparator").text.casefold()] += 1
        datetime_seps[separators.find("DateSeparator").text.casefold()] += 1
        datetime_seps[separators.find("TimeSeparator").text.casefold()] += 1

    for separators in root.findall("./LC_CURRENCY/Currency"):
        curr_symbols[separators.find("CurrencySymbol").text.casefold()] += 1
        curr_codes[separators.find("CurrencyID").text.casefold()] += 1

    name_by_datecode = names_by_datecode_by_locale.setdefault(source.stem, {})
    for day in root.findall("./LC_CALENDAR/Calendar/DaysOfWeek/Day"):
        name_by_datecode.setdefault("day", set()).add(
            day.find("DefaultFullName").text.casefold()),
        name_by_datecode.setdefault("dy", set()).add(
            day.find("DefaultAbbrvName").text.casefold())

    for month in root.findall("./LC_CALENDAR/Calendar/MonthsOfYear/Month"):
        name_by_datecode.setdefault("month", []).append(
            month.find("DefaultFullName").text.casefold()),
        name_by_datecode.setdefault("mon", []).append(
            month.find("DefaultAbbrvName").text.casefold())

print("""# coding: utf-8

# Data is retrieved from LibreOffice:
# https://github.com/LibreOffice/core/tree/master/i18npool/source/localedata/data
""")

print("TRUE_FALSE_BY_LOCALE_NAME = {")
for k, (t, f) in sorted(true_false_by_locale.items()):
    print(f"    {repr(k)}: ({repr(t)}, {repr(f)}),")
print("}")

for constant, counter in [("NUMBER_SEPARATORS", number_seps),
                          ("DATETIME_SEPARATORS", datetime_seps),
                          ("CURRENCY_SYMBOLS", curr_symbols),
                          ("CURRENCY_CODES", curr_codes),
                          ]:
    print()
    print(f"{constant} = {{")
    print(", ".join(repr(sep) for sep, _c in counter.most_common()))
    print("}")

print("PERCENTAGE_SIGNS = {\"%\"}")

print()
print("NAMES_BY_DATECODE_BY_LOCALE = {")
for locale, names_by_datecode in names_by_datecode_by_locale.items():
    print(f"    {repr(locale)}: {{")
    for datecode, names in names_by_datecode.items():
        names = ", ".join(repr(n) for n in names)
        print(f"        {repr(datecode)}: {{{names}}},")
    print("    },")
print("}")
