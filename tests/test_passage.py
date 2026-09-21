import pytest

from bg.passage import PassageRangeError, assemble
from bg.refs import parse_reference


def chapter_document(chapter, last_verse, headings=(), book="Romans"):
    return {
        "schema": 1,
        "version": "KJV",
        "book": book,
        "book_osis": "Rom",
        "chapter": chapter,
        "fetched_at": "2026-09-21T00:00:00Z",
        "source_url": f"https://example.invalid/{book}+{chapter}",
        "copyright": "King James Version - public domain.",
        "headings": [{"before_verse": v, "text": t} for v, t in headings],
        "verses": [
            {
                "num": number,
                "text": f"{book} {chapter}:{number} text.",
                "footnotes": [],
                "crossrefs": [],
            }
            for number in range(1, last_verse + 1)
        ],
    }


@pytest.fixture
def romans8():
    return [chapter_document(8, 39, headings=[(1, "Life in the Spirit"), (31, "Love")])]


@pytest.fixture
def romans8_and_9():
    return [chapter_document(8, 39), chapter_document(9, 33)]


def test_a_whole_chapter_reference_returns_every_verse(romans8):
    passage = assemble(parse_reference("Romans 8"), romans8)

    assert [verse["num"] for verse in passage["verses"]] == list(range(1, 40))


def test_a_single_verse_reference_returns_that_verse_alone(romans8):
    passage = assemble(parse_reference("Romans 8:28"), romans8)

    assert [verse["num"] for verse in passage["verses"]] == [28]


def test_a_verse_range_returns_only_that_range(romans8):
    passage = assemble(parse_reference("Romans 8:28-30"), romans8)

    assert [verse["num"] for verse in passage["verses"]] == [28, 29, 30]


def test_a_cross_chapter_range_runs_to_the_chapter_end_then_into_the_next(
    romans8_and_9,
):
    passage = assemble(parse_reference("Romans 8:38-9:2"), romans8_and_9)

    assert [(v["chapter"], v["num"]) for v in passage["verses"]] == [
        (8, 38),
        (8, 39),
        (9, 1),
        (9, 2),
    ]


def test_a_chapter_range_returns_both_chapters_whole(romans8_and_9):
    passage = assemble(parse_reference("Romans 8-9"), romans8_and_9)

    assert len(passage["verses"]) == 39 + 33


def test_every_verse_carries_its_chapter_so_a_span_stays_addressable(romans8):
    passage = assemble(parse_reference("Romans 8:28"), romans8)

    assert passage["verses"][0]["chapter"] == 8


def test_the_passage_echoes_the_canonical_reference_and_version(romans8):
    passage = assemble(parse_reference("rom 8:28-30"), romans8)

    assert passage["reference"] == "Romans 8:28-30"
    assert passage["version"] == "KJV"


def test_headings_inside_the_range_are_kept_and_others_dropped(romans8):
    passage = assemble(parse_reference("Romans 8:28-33"), romans8)

    assert passage["headings"] == [{"chapter": 8, "before_verse": 31, "text": "Love"}]


def test_the_passage_records_every_copyright_it_drew_on(romans8_and_9):
    passage = assemble(parse_reference("Romans 8-9"), romans8_and_9)

    assert passage["copyright"] == ["King James Version - public domain."]


def test_a_verse_beyond_the_end_of_the_chapter_is_rejected(romans8):
    with pytest.raises(PassageRangeError):
        assemble(parse_reference("Romans 8:40"), romans8)


def test_a_missing_chapter_document_is_rejected(romans8):
    with pytest.raises(PassageRangeError):
        assemble(parse_reference("Romans 8-9"), romans8)
