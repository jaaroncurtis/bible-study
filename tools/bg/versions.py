"""Parse BibleGateway's translation catalogue.

The versions table is the only structured statement on the site of which
translations exist and which have a recording: /resources/audio/ is a marketing
page about devotionals, not an index. Audio is therefore recorded here as a
property of a translation rather than as a catalogue of its own.
"""

import copy
import re

from bs4 import BeautifulSoup

from bg.text import clean

# "American Standard Version (ASV)" -> name, code. A code is always a single
# token (ASV, KJ21, ERV-AR), so a parenthesised phrase is a subtitle instead:
# "Pavithar Bible (New India Bible Version)" has no code at all.
_NAMED_CODE = re.compile(r"^(?P<name>.+?)\s*\((?P<code>[^()\s]+)\)\s*$")

# "English (EN) 64" -> "English"
_LANGUAGE_SUFFIX = re.compile(r"\s*\([A-Za-z-]+\)\s*\d*\s*$")


def _language_name(cell):
    display = cell.select_one("span.language-display") or cell
    clone = copy.copy(display)
    for svg in clone.select("svg"):
        svg.decompose()
    return _LANGUAGE_SUFFIX.sub("", clean(clone.get_text(" "))).strip()


def parse_versions(html):
    soup = BeautifulSoup(html, "lxml")

    languages = {}
    for row in soup.select("tr.language-row"):
        cell = row.select_one("td.language-cell")
        code = row.get("data-language")
        if cell is None or not code or code in languages:
            continue
        name = _language_name(cell)
        if name:
            languages[code] = name

    versions = []
    for cell in soup.select("td.translation-name"):
        row = cell.find_parent("tr")
        label = clean(cell.get_text(" "))
        match = _NAMED_CODE.match(label)
        language_code = row.get("data-language") if row is not None else None
        has_audio = (
            row is not None
            and row.select_one("td.translation-types a[href*='audio']") is not None
        )

        versions.append(
            {
                "code": match.group("code") if match else None,
                "name": match.group("name") if match else label,
                "language": languages.get(language_code),
                "language_code": language_code,
                "audio": has_audio,
            }
        )
    return versions


def filter_versions(versions, text=None, language=None, audio_only=False):
    """Narrow the catalogue. `text` matches either the name or the code."""
    selected = list(versions)

    if text:
        needle = text.casefold()
        selected = [
            version
            for version in selected
            if needle in (version["name"] or "").casefold()
            or needle in (version["code"] or "").casefold()
        ]
    if language:
        wanted = language.casefold()
        selected = [
            version
            for version in selected
            if (version["language_code"] or "").casefold() == wanted
        ]
    if audio_only:
        selected = [version for version in selected if version["audio"]]

    return selected


def find_version(versions, code):
    """Look a translation up by its code, however it was capitalised."""
    wanted = str(code).strip().casefold()
    for version in versions:
        if version["code"] and version["code"].casefold() == wanted:
            return version
    return None
