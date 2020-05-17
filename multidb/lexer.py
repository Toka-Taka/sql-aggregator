import logging

from . import _logger
from . import token as tk

# noinspection PyTypeChecker
logger = logging.getLogger('lexer')  # type: _logger.ParserLogger


class Position:
    END_CHAR = '\000'

    def __init__(self, text, n=None, idx=None, row=None, col=None):
        self._text = text
        self.n = n or len(text)
        self.idx = idx or 0
        self.row = row or 1
        self.col = col or 1

    @property
    def text(self):
        return self._text[self.idx:]

    @property
    def char(self):
        return self._text[self.idx] if self.idx < self.n else self.END_CHAR

    def next(self):
        if self.char == '\n':
            self.row += 1
            self.col = 1
        else:
            self.col += 1
        self.idx = self.idx + 1 if self.idx < self.n else self.idx

    def nextn(self, n):
        assert n > 0
        for _ in range(n):
            self.next()

    @property
    def isspace(self):
        return self.char.isspace()

    @property
    def is_end(self):
        return self.idx == self.n

    def skip_space(self):
        while self.isspace:
            self.next()

    def __sub__(self, other):
        return self._text[other.idx:self.idx]

    def __copy__(self):
        return Position(self._text, self.n, self.idx, self.row, self.col)

    def copy(self):
        return self.__copy__()

    def __str__(self):
        return '<{}:{}>'.format(self.row, self.col)


class Interval:
    def __init__(self):
        self._start = None
        self._end = None

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value: Position):
        self._start = value.copy()

    @start.deleter
    def start(self):
        self._start = None

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value: Position):
        self._end = value.copy()

    @end.deleter
    def end(self):
        self._end = None

    def __str__(self):
        assert self._start and self._end
        return self.end - self.start

    def __repr__(self):
        assert self._start and self._end
        return '[{}-{}]'.format(self._start, self._end)


class Lexer:
    TOKENS = [
        tk.IntToken,
        tk.FloatToken,
        tk.StringToken,
        tk.DateToken,
        tk.DatetimeToken,
        tk.IdentifierToken,
        tk.KeywordToken,
        tk.SymbolToken
    ]

    def __init__(self, program):
        self.program = program
        self.pos = Position(program)

        self.interval = None
        self.last_interval = None
        logger.set_lexer(self)

    def get_matches(self):
        start = self.pos.copy()
        return start, sorted((
            (t, t.match(start))
            for t in self.TOKENS
        ), key=lambda x: x[1][0], reverse=True)

    def __parse(self):
        self.pos.skip_space()
        while not self.pos.is_end:
            self.last_interval, self.interval = self.interval, Interval()

            self.interval.start, matches = self.get_matches()
            max_size = matches[0][1][0]

            if not max_size:
                while not self.pos.isspace and not self.pos.is_end:
                    self.pos.next()
                self.interval.end = self.pos.copy()
                logger.current_token.error('Wrong sequences: %s', str(self.interval))
            else:
                self.pos.nextn(max_size)
                self.interval.end = self.pos.copy()
                tokens = tuple(
                    t(match, self.interval)
                    for t, (size, match) in matches
                    if size == max_size
                )
                yield tokens

            self.pos.skip_space()