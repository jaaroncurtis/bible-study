import pytest

from bg.books import CANON
from bg.refs import (
    InvalidReferenceError,
    UnknownBookError,
    parse_reference,
    resolve_book,
)


def test_parses_book_chapter_and_single_verse():
    ref = parse_reference("Romans 8:28")

    assert ref.book == "Romans"
    assert ref.start_chapter == 8
    assert ref.start_verse == 28
    assert ref.end_chapter == 8
    assert ref.end_verse == 28


def test_parses_whole_chapter_with_no_verses():
    ref = parse_reference("Romans 8")

    assert ref.book == "Romans"
    assert ref.start_chapter == 8
    assert ref.end_chapter == 8
    assert ref.start_verse is None
    assert ref.end_verse is None


def test_parses_verse_range_within_one_chapter():
    ref = parse_reference("Romans 8:28-30")

    assert ref.start_chapter == 8
    assert ref.start_verse == 28
    assert ref.end_chapter == 8
    assert ref.end_verse == 30


def test_parses_range_spanning_two_chapters():
    ref = parse_reference("Romans 8:28-9:2")

    assert ref.start_chapter == 8
    assert ref.start_verse == 28
    assert ref.end_chapter == 9
    assert ref.end_verse == 2


def test_parses_chapter_range():
    ref = parse_reference("Romans 8-9")

    assert ref.start_chapter == 8
    assert ref.start_verse is None
    assert ref.end_chapter == 9
    assert ref.end_verse is None


def test_canonicalizes_a_book_abbreviation():
    assert parse_reference("Rom 8").book == "Romans"


def test_exposes_the_osis_code_for_the_book():
    assert parse_reference("Rom 8").osis == "Rom"


@pytest.mark.parametrize(
    "text", ["1 Cor 13", "1Cor 13", "I Corinthians 13", "1 Corinthians 13", "1 cor. 13"]
)
def test_numbered_book_variants_all_canonicalize_the_same(text):
    assert parse_reference(text).book == "1 Corinthians"


def test_distinguishes_john_from_first_john():
    assert parse_reference("John 3:16").book == "John"
    assert parse_reference("1 John 3:16").book == "1 John"


@pytest.mark.parametrize("text", ["Ps 23", "Psalm 23", "Psalms 23"])
def test_psalm_variants_canonicalize_to_psalms(text):
    assert parse_reference(text).book == "Psalms"


def test_unknown_book_raises_with_a_suggestion():
    with pytest.raises(UnknownBookError) as excinfo:
        parse_reference("Romanz 8")

    assert "Romans" in str(excinfo.value)


def test_text_with_no_chapter_is_rejected():
    with pytest.raises(InvalidReferenceError):
        parse_reference("not a reference")


def test_a_reference_inside_one_chapter_spans_that_chapter_only():
    assert parse_reference("Romans 8:28-30").chapters() == [8]


def test_a_cross_chapter_reference_spans_every_chapter_between():
    assert parse_reference("Romans 8:28-10:4").chapters() == [8, 9, 10]


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("rom 8", "Romans 8"),
        ("rom 8:28", "Romans 8:28"),
        ("rom 8:28-30", "Romans 8:28-30"),
        ("rom 8-9", "Romans 8-9"),
        ("rom 8:28-9:2", "Romans 8:28-9:2"),
        ("1cor 13", "1 Corinthians 13"),
    ],
)
def test_query_renders_the_canonical_reference(typed, expected):
    assert parse_reference(typed).query() == expected


def test_every_book_resolves_from_its_own_canonical_name_and_osis_code():
    for canonical, osis, _ in CANON:
        assert resolve_book(canonical) == (canonical, osis)
        assert resolve_book(osis) == (canonical, osis)
