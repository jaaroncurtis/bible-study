import pytest

from bg.parse import PassageNotFoundError, parse_chapter


@pytest.fixture
def romans8(fixture_html):
    """Romans 8:1-3 ESV.

    Trimmed to an excerpt: it is the only fixture carrying section headings,
    footnotes and cross-references, none of which BibleGateway supplies for a
    public-domain translation.
    """
    return parse_chapter(fixture_html("esv-romans-8-excerpt.html"), version="ESV")


@pytest.fixture
def romans8_kjv(fixture_html):
    """Romans 8 KJV in full - no headings, footnotes or cross-references."""
    return parse_chapter(fixture_html("kjv-romans-8.html"), version="KJV")


def test_identifies_the_book_and_chapter_from_the_markup(romans8):
    assert romans8.book_code == "Rom"
    assert romans8.chapter == 8


def test_verse_text_drops_verse_numbers_and_marker_glyphs(romans8):
    first = romans8.verses[0]

    assert first.text == (
        "There is therefore now no condemnation for those who are in Christ Jesus."
    )


def test_a_verse_carrying_markers_keeps_only_its_words(romans8):
    second = next(v for v in romans8.verses if v.num == 2)

    assert second.text.startswith("For the law of the Spirit of life has set you free")
    assert "(" not in second.text
    assert "[" not in second.text


def test_headings_are_attached_to_the_verse_they_introduce(romans8):
    assert romans8.headings[0].text == "Life in the Spirit"
    assert romans8.headings[0].before_verse == 1


def test_footnotes_are_attached_to_the_verse_that_cites_them(romans8):
    first = romans8.verses[0]

    assert [f.marker for f in first.footnotes] == ["a"]
    assert first.footnotes[0].text == (
        "Some manuscripts add who walk not according to the flesh "
        "(but according to the Spirit)"
    )


def test_cross_references_are_attached_to_their_verse(romans8):
    second = next(v for v in romans8.verses if v.num == 2)

    assert [c.marker for c in second.crossrefs] == ["A", "B"]


def test_cross_reference_targets_are_expanded_to_unambiguous_references(romans8):
    second = next(v for v in romans8.verses if v.num == 2)

    assert second.crossrefs[0].refs == ["1 Corinthians 15:45", "2 Corinthians 3:6"]
    # BibleGateway prints a compact form whose later parts are unusable alone
    # ("7:4"); keep it for display, but never as the addressable reference.
    assert second.crossrefs[1].refs == [
        "Romans 8:12",
        "Romans 6:14",
        "Romans 6:18",
        "Romans 7:4",
    ]


def test_cross_reference_keeps_the_display_form_biblegateway_prints(romans8):
    second = next(v for v in romans8.verses if v.num == 2)

    assert second.crossrefs[0].display == "1 Cor. 15:45; 2 Cor. 3:6"


def test_captures_the_translation_copyright_notice(romans8):
    assert "Crossway" in romans8.copyright


def test_parses_a_full_chapter(romans8_kjv):
    assert [verse.num for verse in romans8_kjv.verses] == list(range(1, 40))
    assert romans8_kjv.verses[27].text.startswith("And we know that all things work")


def test_a_translation_without_study_apparatus_parses_cleanly(romans8_kjv):
    assert romans8_kjv.headings == []
    assert all(not verse.footnotes for verse in romans8_kjv.verses)
    assert all(not verse.crossrefs for verse in romans8_kjv.verses)
    assert all(verse.text for verse in romans8_kjv.verses)


def test_a_page_with_no_passage_is_rejected(fixture_html):
    with pytest.raises(PassageNotFoundError):
        parse_chapter(fixture_html("esv-no-results.html"), version="ESV")
