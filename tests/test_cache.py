import json

import pytest

from bg.cache import Cache, to_document
from bg.parse import parse_chapter


@pytest.fixture
def cache(tmp_path):
    return Cache(tmp_path)


@pytest.fixture
def romans8(fixture_html):
    return parse_chapter(fixture_html("esv-romans-8-excerpt.html"), version="ESV")


@pytest.fixture
def document(romans8):
    return to_document(
        romans8,
        book="Romans",
        source_url="https://www.biblegateway.com/passage/?search=Romans+8&version=ESV",
    )


def test_a_chapter_is_stored_under_version_book_and_padded_chapter(cache, tmp_path):
    assert cache.path_for("ESV", "Romans", 8) == tmp_path / "ESV" / "Romans" / "008.json"


def test_chapter_numbers_pad_so_they_sort_in_reading_order(cache):
    names = [cache.path_for("ESV", "Psalms", n).name for n in (8, 99, 119, 150)]

    assert names == sorted(names)


def test_loading_a_chapter_that_was_never_cached_returns_none(cache):
    assert cache.load("ESV", "Romans", 8) is None


def test_a_saved_chapter_can_be_loaded_back_unchanged(cache, document):
    cache.save(document)

    assert cache.load("ESV", "Romans", 8) == document


def test_a_document_records_where_and_when_it_came_from(document):
    assert document["source_url"].endswith("version=ESV")
    assert document["fetched_at"].endswith("Z")
    assert document["schema"] == 1


def test_a_document_carries_the_translation_copyright(document):
    assert "Crossway" in document["copyright"]


def test_a_document_keeps_verses_headings_footnotes_and_crossrefs(document):
    first = document["verses"][0]

    assert first["num"] == 1
    assert first["text"].startswith("There is therefore now no condemnation")
    assert first["footnotes"][0]["marker"] == "a"
    assert document["headings"][0] == {"before_verse": 1, "text": "Life in the Spirit"}

    second = document["verses"][1]
    assert second["crossrefs"][0]["refs"][0] == "1 Corinthians 15:45"


def test_saved_json_is_readable_utf8(cache, document):
    path = cache.save(document)
    raw = path.read_text(encoding="utf-8")

    assert "\n" in raw, "should be indented rather than one long line"
    escape_prefix = chr(92) + "u"
    assert escape_prefix not in raw, "non-ascii belongs as characters"
    assert json.loads(raw) == document


def test_cache_status_counts_what_is_stored(cache, document):
    cache.save(document)

    status = cache.status()

    assert status["chapters"] == 1
    assert status["versions"] == ["ESV"]
