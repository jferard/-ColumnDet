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
from enum import Enum
from typing import TypeVar, Optional, Tuple, Callable, Mapping, Sequence, \
    Counter, Sized, Iterable, Iterator

T = TypeVar('T')
LocaleType = Optional[Tuple[str, str]]


def get_unique(counter: Counter[T], threshold: float = 0.99) -> T:
    """
    :param counter: a counter
    :param threshold: a _threshold
    :return: the unique value in the counter, or raise a ValueError
    """
    value_and_count, = counter.most_common(1)
    if value_and_count[1] > threshold * sum(counter.values()):
        return value_and_count[0]
    else:
        raise ValueError()


def get_some(counter: Counter[T], n: int, threshold: float = 0.99) -> Tuple[T]:
    """
    :param counter: a counter
    :param n: the number of int_values
    :param threshold: a _threshold
    :return: the `n` or less int_values in the counter, or raise a ValueError
    """
    if not counter:
        values = tuple()
    elif len(counter) <= n:
        values, _ = zip(*counter.most_common())
    else:
        values, counts = zip(*counter.most_common(n))
        if sum(counts) <= threshold * sum(counter.values()):
            raise ValueError()

    return values


class OpCode(Enum):
    NUMBER = 1
    SPACE = 2
    TEXT = 3
    PUNCTUATION = 4
    OPERATOR = 5


Token = collections.namedtuple('Token', ['opcode', 'text'])


class TokenRow(Iterable[Token], Sized):
    def __init__(self, tokens: Sequence[Token]):
        self._tokens = tokens

    def __len__(self):
        return len(self._tokens)

    def __iter__(self) -> Iterator[Token]:
        return iter(self._tokens)

    @property
    def first_opcode(self) -> OpCode:
        return self._tokens[0].opcode

    @property
    def first_text(self) -> str:
        return self._tokens[0].text

    @property
    def last_opcode(self) -> OpCode:
        return self._tokens[-1].opcode

    @property
    def last_text(self) -> str:
        return self._tokens[-1].text

    @property
    def only(self) -> Token:
        assert len(self._tokens) == 1
        return self._tokens[0]

    def lstrip(self, func: Callable[[Token], bool]) -> "TokenRow":
        i = 0
        while i < len(self._tokens) and func(self._tokens[i]):
            i += 1
        return TokenRow(self._tokens[i:])

    def rstrip(self, func: Callable[[Token], bool]) -> "TokenRow":
        i = len(self._tokens)
        while i > 0 and func(self._tokens[i - 1]):
            i -= 1
        return TokenRow(self._tokens[:i])

    def pop(self) -> Token:
        ret = self._tokens[-1]
        self._tokens = self._tokens[:-1]
        return ret

    def shift(self) -> Token:
        ret = self._tokens[0]
        self._tokens = self._tokens[1:]
        return ret

    def first(self) -> Token:
        return self._tokens[0]

    def last(self) -> Token:
        return self._tokens[-1]


class ColumnInfos:
    """
    Infos about a column.
    """

    @staticmethod
    def create(tokens: TokenRow,
               is_null: Optional[Callable[[Token], bool]] = None,
               threshold: float = 1.0) -> "ColumnInfos":
        """

        :param tokens: the tokens of the column
        :param is_null: a function that returns True if the token is null
        :param threshold: the _threshold
        :return: column infos
        """
        if is_null is None:
            non_null_tokens = [t for t in tokens if
                               t.opcode != OpCode.SPACE]
        else:
            non_null_tokens = [t for t in tokens if is_null(t.opcode)]
        return ColumnInfos(tokens, TokenRow(non_null_tokens), threshold)

    def __init__(self, tokens: TokenRow,
                 non_null_tokens: TokenRow,
                 threshold: float):
        self._tokens = tokens
        self._non_null_tokens = non_null_tokens
        self._threshold = threshold

    def stats(self) -> Mapping[Token, float]:
        counter = collections.Counter(self._tokens)
        return {k: v / len(self._tokens) for k, v in
                counter.items()}

    @property
    def non_null_tokens(self):
        return self._non_null_tokens

    @property
    def opcodes(self) -> Mapping[OpCode, int]:
        return collections.Counter([t.opcode for t in self._non_null_tokens])

    @property
    def unique_width(self) -> int:
        return self._unique(lambda t: len(t.text))

    @property
    def unique_token(self):
        return self._unique(lambda t: t)

    @property
    def unique_opcode(self):
        return self._unique(lambda t: t.opcode)

    @property
    def texts(self):
        return set([t.text.casefold() for t in self._tokens])

    def _unique(self, func: Callable[[Token], T]) -> T:
        if self._non_null_tokens:
            tokens = self.non_null_tokens
        else:
            tokens = self._tokens
        counter = collections.Counter(func(t) for t in tokens)
        return get_unique(counter, self._threshold)

    def split_at(self, n) -> Tuple["ColumnInfos", "ColumnInfos"]:
        tokens = [Token(t.opcode, t.text[:n]) for t in self._tokens]
        non_null_tokens = [Token(t.opcode, t.text[:n]) for t in
                           self._non_null_tokens]
        first = ColumnInfos(TokenRow(tokens), TokenRow(non_null_tokens),
                            self._threshold)

        tokens = [Token(t.opcode, t.text[n:]) for t in self._tokens]
        non_null_tokens = [Token(t.opcode, t.text[n:]) for t in
                           self._non_null_tokens]
        second = ColumnInfos(TokenRow(tokens), TokenRow(non_null_tokens),
                             self._threshold)
        return first, second


class LocalesWrapper:
    def __init__(self, locale_names: Optional[Sequence[LocaleType]]):
        self._locale_names = locale_names

    def match(self, locale_name):
        pass
