"""Turn a BibleGateway passage page into structured chapter data.

BibleGateway wraps every verse in one or more ``span.text`` elements whose
class carries the address -- ``Rom-8-1`` is Romans chapter 8 verse 1. Footnote
and cross-reference markers sit *inside* those spans, so a marker's verse is
known from its container and never has to be recovered by parsing the
reference text printed beside the note.
"""

import copy
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


class PassageNotFoundError(ValueError):
    """The page carries no passage -- a bad reference, or a search-results page."""


@dataclass(frozen=True)
class Footnote:
    marker: str
    text: str


@dataclass(frozen=True)
class CrossRef:
    marker: str
    refs: list
    display: str


@dataclass
class Verse:
    num: int
    text: str
    footnotes: list = field(default_factory=list)
    crossrefs: list = field(default_factory=list)


@dataclass(frozen=True)
class Heading:
    before_verse: int
    text: str


@dataclass
class Chapter:
    version: str
    book_code: str
    chapter: int
    verses: list
    headings: list
    copyright: str


# "Rom-8-1", "1Cor-13-4" -- book code may itself contain digits, so split from
# the right.
_VERSE_CLASS = re.compile(r"^(?P<book>.+)-(?P<chapter>\d+)-(?P<verse>\d+)$")

_HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5"]
_NON_TEXT = ["sup.versenum", "span.chapternum", "sup.footnote", "sup.crossreference"]


def _clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _verse_address(element):
    """Return (book_code, chapter, verse) if this element is a verse span."""
    for name in element.get("class") or []:
        match = _VERSE_CLASS.match(name)
        if match:
            return (
                match.group("book"),
                int(match.group("chapter")),
                int(match.group("verse")),
            )
    return None


def _words_of(span):
    """The span's own words: no verse number, no heading, no marker glyphs."""
    clone = copy.copy(span)
    for selector in _NON_TEXT + _HEADING_TAGS:
        for unwanted in clone.select(selector):
            unwanted.decompose()
    return _clean(clone.get_text())


def _footnote_bodies(soup):
    bodies = {}
    for item in soup.select("div.footnotes li"):
        body = item.select_one("span.footnote-text")
        if body is None:
            body = copy.copy(item)
            first_link = body.find("a")
            if first_link is not None:
                first_link.decompose()
        bodies[item.get("id")] = _clean(body.get_text())
    return bodies


def _crossref_bodies(soup):
    """Map each cross-reference id to its expanded targets and printed form.

    The printed form abbreviates against the running context -- "ver. 12; See
    ch. 6:14, 18; 7:4" -- so its later parts cannot stand alone. The link's
    ``data-bibleref`` carries the same set fully expanded, which is what a note
    can actually resolve, so that is the addressable value.
    """
    bodies = {}
    for item in soup.select("div.crossrefs li"):
        links = item.select("a.crossref-link")
        display = _clean("; ".join(link.get_text() for link in links))

        refs = []
        for link in links:
            expanded = link.get("data-bibleref") or ""
            refs.extend(_clean(part) for part in expanded.split(",") if _clean(part))

        if not refs:
            refs = [_clean(part) for part in display.split(";") if _clean(part)]

        bodies[item.get("id")] = (refs, display)
    return bodies


def _markers_in(span, attribute):
    """Yield (note id, marker letter) for each marker sup inside this span."""
    for sup in span.select(f"sup[{attribute}]"):
        if sup.find_parent(_HEADING_TAGS) is not None:
            continue
        note_id = (sup.get(attribute) or "").lstrip("#")
        marker = _clean(sup.get_text()).strip("[]() ")
        if note_id:
            yield note_id, marker


def parse_chapter(html, version):
    """Parse one chapter's passage page into a Chapter."""
    soup = BeautifulSoup(html, "lxml")

    content = soup.select_one("div.passage-content")
    if content is None:
        raise PassageNotFoundError("page contains no passage content")

    footnote_bodies = _footnote_bodies(soup)
    crossref_bodies = _crossref_bodies(soup)

    verses = {}
    order = []
    book_code = None
    chapter_number = None

    for span in content.select("span.text"):
        address = _verse_address(span)
        if address is None or span.find_parent(_HEADING_TAGS) is not None:
            continue
        book_code, chapter_number, number = address

        words = _words_of(span)
        if number not in verses:
            verses[number] = Verse(num=number, text="")
            order.append(number)
        verse = verses[number]
        verse.text = _clean(f"{verse.text} {words}")

        for note_id, marker in _markers_in(span, "data-fn"):
            verse.footnotes.append(
                Footnote(marker=marker, text=footnote_bodies.get(note_id, ""))
            )
        for note_id, marker in _markers_in(span, "data-cr"):
            refs, display = crossref_bodies.get(note_id, ([], ""))
            verse.crossrefs.append(
                CrossRef(marker=marker, refs=refs, display=display)
            )

    if not order:
        raise PassageNotFoundError("page contains no verses")

    headings = []
    for element in content.find_all(_HEADING_TAGS):
        text = _clean(element.get_text())
        if not text:
            continue
        before = _following_verse_number(element)
        if before is not None:
            headings.append(Heading(before_verse=before, text=text))

    notice = soup.select_one("div.publisher-info-bottom") or soup.select_one(
        "div.copyright-table"
    )

    return Chapter(
        version=version,
        book_code=book_code,
        chapter=chapter_number,
        verses=[verses[number] for number in sorted(order)],
        headings=headings,
        copyright=_clean(notice.get_text()) if notice else "",
    )


def _following_verse_number(element):
    """Which verse does this heading introduce?"""
    enclosing = element.find_parent(attrs={"class": "text"})
    if enclosing is not None:
        address = _verse_address(enclosing)
        if address:
            return address[2]

    for later in element.find_all_next("span", class_="text"):
        address = _verse_address(later)
        if address:
            return address[2]
    return None
