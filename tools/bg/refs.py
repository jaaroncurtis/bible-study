"""Parsing and canonicalization of Bible references."""

import difflib
import re
from dataclasses import dataclass

from bg.books import CANON


class ReferenceError(ValueError):
    """Base class for anything wrong with a reference string."""


class InvalidReferenceError(ReferenceError):
    """The text is not shaped like a reference at all."""


class UnknownBookError(ReferenceError):
    """The book part of the reference does not name a book of the canon."""


@dataclass(frozen=True)
class Reference:
    book: str
    osis: str
    start_chapter: int
    start_verse: int | None
    end_chapter: int
    end_verse: int | None

    def chapters(self):
        """Every chapter this reference touches - the unit of fetching and caching."""
        return list(range(self.start_chapter, self.end_chapter + 1))

    def query(self):
        """Render the canonical reference string, as BibleGateway expects it."""
        text = f"{self.book} {self.start_chapter}"
        if self.start_verse is not None:
            text += f":{self.start_verse}"

        if (self.end_chapter, self.end_verse) == (self.start_chapter, self.start_verse):
            return text
        if self.end_chapter == self.start_chapter:
            return f"{text}-{self.end_verse}"
        if self.end_verse is None:
            return f"{text}-{self.end_chapter}"
        return f"{text}-{self.end_chapter}:{self.end_verse}"


# Book, start chapter, optional start verse, and an optional end that is either
# a full "chapter:verse" or a bare number whose meaning depends on whether a
# start verse was given ("Rom 8-9" is chapters, "Rom 8:28-30" is verses).
_REFERENCE = re.compile(
    r"""^\s*
    (?P<book>.+?)
    \s+
    (?P<start_chapter>\d+)
    (?::(?P<start_verse>\d+))?
    (?:\s*[-\u2013\u2014]\s*
        (?:
            (?P<end_chapter>\d+):(?P<end_verse>\d+)
          | (?P<end_number>\d+)
        )
    )?
    \s*$""",
    re.VERBOSE,
)

_ORDINAL_PREFIXES = [
    (re.compile(r"^(?:iii|third|3rd)\b\s*"), "3 "),
    (re.compile(r"^(?:ii|second|2nd)\b\s*"), "2 "),
    (re.compile(r"^(?:i|first|1st)\b\s*"), "1 "),
]


def normalize_book(text):
    """Fold the many ways a book gets typed into one lookup key.

    "1 Cor.", "I Corinthians", "1cor" and "1 CORINTHIANS" all become "1 cor".
    """
    key = text.strip().lower().replace(".", "")
    key = re.sub(r"\s+", " ", key)
    for pattern, replacement in _ORDINAL_PREFIXES:
        if pattern.match(key):
            key = pattern.sub(replacement, key)
            break
    key = re.sub(r"^(\d)\s*", r"\1 ", key)
    return key.strip()


def _build_alias_index():
    index = {}
    for canonical, osis, aliases in CANON:
        keys = {normalize_book(canonical), normalize_book(osis)}
        keys.update(normalize_book(alias) for alias in aliases)
        for key in keys:
            if key in index and index[key][0] != canonical:
                raise RuntimeError(
                    f"alias {key!r} maps to both {index[key][0]} and {canonical}"
                )
            index[key] = (canonical, osis)
    return index


_ALIASES = _build_alias_index()


def resolve_book(text):
    """Return (canonical name, OSIS code) for a book however it was typed."""
    key = normalize_book(text)
    if key in _ALIASES:
        return _ALIASES[key]

    close = difflib.get_close_matches(key, _ALIASES, n=3, cutoff=0.6)
    suggestions = []
    for match in close:
        canonical = _ALIASES[match][0]
        if canonical not in suggestions:
            suggestions.append(canonical)

    message = f"Unknown book {text!r}"
    if suggestions:
        message += f". Did you mean {' or '.join(suggestions)}?"
    raise UnknownBookError(message)


def parse_reference(text):
    """Parse a human reference such as "Rom 8:28-30" into a Reference."""
    match = _REFERENCE.match(text)
    if match is None:
        raise InvalidReferenceError(
            f"{text!r} is not a reference; expected something like 'Romans 8:28-30'"
        )

    book, osis = resolve_book(match.group("book"))
    start_chapter = int(match.group("start_chapter"))
    start_verse = int(match.group("start_verse")) if match.group("start_verse") else None

    if match.group("end_chapter"):
        end_chapter = int(match.group("end_chapter"))
        end_verse = int(match.group("end_verse"))
    elif match.group("end_number"):
        end_number = int(match.group("end_number"))
        if start_verse is None:
            end_chapter, end_verse = end_number, None
        else:
            end_chapter, end_verse = start_chapter, end_number
    else:
        end_chapter, end_verse = start_chapter, start_verse

    return Reference(book, osis, start_chapter, start_verse, end_chapter, end_verse)
