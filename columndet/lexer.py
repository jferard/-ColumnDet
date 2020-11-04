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
from typing import Sequence

from columndet.i18n import CURRENCY_SYMBOLS, CURRENCY_CODES, \
    DATETIME_SEPARATORS, \
    NUMBER_SEPARATORS, PERCENTAGE_SIGNS
from columndet.util import (Token, OpCode)


class Lexer:
    def lex(self, text: str) -> Sequence[Token]:
        text = text.strip()
        if not text:
            return []

        tokens = []
        c = text[0]
        cur = c
        was_opcode = self._get_opcode(c)

        for c in text[1:]:
            is_opcode = self._get_opcode(c)
            if is_opcode == was_opcode or (
                    was_opcode == OpCode.TEXT and c in {"."}):
                cur += c
            else:
                token = self._create_token(was_opcode, cur)
                if token is not None:
                    tokens.append(token)
                cur = c
            was_opcode = is_opcode

        token = self._create_token(was_opcode, cur)
        if token is not None:
            tokens.append(token)
        return tokens

    def _get_opcode(self, c: str) -> OpCode:
        if c.isdigit():
            opcode = OpCode.NUMBER
        elif c.isspace():
            opcode = OpCode.SPACE
        else:
            opcode = OpCode.TEXT
        return opcode

    def _create_token(self, opcode: OpCode, text: str) -> Token:
        if opcode in {OpCode.NUMBER, OpCode.SPACE}:
            pass
        elif text in DATETIME_SEPARATORS & NUMBER_SEPARATORS:
            opcode = OpCode.ANY_DATE_OR_NUMBER_SEPARATOR
        elif text in DATETIME_SEPARATORS:
            opcode = OpCode.ANY_DATE_SEPARATOR
        elif text in NUMBER_SEPARATORS:
            opcode = OpCode.ANY_NUMBER_SEPARATOR
        elif text in PERCENTAGE_SIGNS:
            opcode = OpCode.ANY_PERCENTAGE_SIGN
        elif text in CURRENCY_SYMBOLS or text in CURRENCY_CODES:
            opcode = OpCode.ANY_CURRENCY_SIGN
        else:
            opcode = OpCode.TEXT
        return Token(opcode, text)
