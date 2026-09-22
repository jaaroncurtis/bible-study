import pathlib

import pytest

from study.lesson import LessonFormatError, parse_lesson

MINIMAL = """# The Fall

**Romans 1:21b-32**

## Aim

Trace what the seizure did to us.

## Content

- The declaration of war.
- The new master.

## Reflection

- Where am I still defining righteousness for myself?
"""


def test_reads_the_title_and_reference():
    lesson = parse_lesson(MINIMAL)

    assert lesson["title"] == "The Fall"
    assert lesson["reference"] == "Romans 1:21b-32"


def test_sections_are_keyed_by_name():
    lesson = parse_lesson(MINIMAL)

    assert list(lesson["sections"]) == ["Aim", "Content", "Reflection"]


def test_bullets_are_parsed_as_items():
    lesson = parse_lesson(MINIMAL)
    content = lesson["sections"]["Content"][0]

    assert content["heading"] is None
    assert content["items"] == ["The declaration of war.", "The new master."]


def test_prose_is_parsed_as_paragraphs():
    lesson = parse_lesson(MINIMAL)

    assert lesson["sections"]["Aim"][0]["paragraphs"] == [
        "Trace what the seizure did to us."
    ]


def test_a_subheading_opens_a_new_group():
    text = MINIMAL.replace(
        "## Reflection\n\n- Where am I",
        "## Reflection\n\n### On the fall\n\n- Where am I",
    )

    groups = parse_lesson(text)["sections"]["Reflection"]

    assert [g["heading"] for g in groups] == ["On the fall"]


def test_cross_references_split_into_reference_and_note():
    text = MINIMAL.replace(
        "## Reflection",
        "## Cross-references\n\n"
        "- **Genesis 3:1-7** — the seizure itself.\n\n"
        "## Reflection",
    )

    items = parse_lesson(text)["sections"]["Cross-references"][0]["items"]

    assert items == [
        {"references": ["Genesis 3:1-7"], "note": "the seizure itself."}
    ]


def test_one_note_may_cover_several_references():
    text = MINIMAL.replace(
        "## Reflection",
        "## Cross-references\n\n"
        "- **Exodus 33:18-19** and **Exodus 34:6-7** — show me your glory.\n\n"
        "## Reflection",
    )

    items = parse_lesson(text)["sections"]["Cross-references"][0]["items"]

    assert items == [
        {
            "references": ["Exodus 33:18-19", "Exodus 34:6-7"],
            "note": "show me your glory.",
        }
    ]


def test_a_missing_title_is_rejected():
    with pytest.raises(LessonFormatError, match="title"):
        parse_lesson(MINIMAL.replace("# The Fall\n", "", 1))


def test_a_missing_reference_is_rejected():
    with pytest.raises(LessonFormatError, match="reference"):
        parse_lesson(MINIMAL.replace("**Romans 1:21b-32**\n", "", 1))


def test_an_unknown_section_is_rejected():
    with pytest.raises(LessonFormatError, match="Discussion"):
        parse_lesson(MINIMAL.replace("## Reflection", "## Discussion"))


def test_sections_out_of_order_are_rejected():
    text = MINIMAL.replace("## Aim", "## TEMP").replace("## Content", "## Aim")
    text = text.replace("## TEMP", "## Content")

    with pytest.raises(LessonFormatError, match="order"):
        parse_lesson(text)


def test_a_repeated_section_is_rejected():
    with pytest.raises(LessonFormatError, match="more than once"):
        parse_lesson(MINIMAL + "\n## Content\n\n- again\n")


def test_a_required_section_missing_is_rejected():
    text = MINIMAL.split("## Reflection")[0]

    with pytest.raises(LessonFormatError, match="Reflection"):
        parse_lesson(text)


def test_cross_references_are_optional():
    assert "Cross-references" not in parse_lesson(MINIMAL)["sections"]


LESSONS = sorted(
    p
    for p in pathlib.Path("studies/romans/sections").rglob("*.md")
    if p.name != "overview.md"
)


def test_the_study_actually_has_lessons_to_check():
    assert len(LESSONS) == 42


@pytest.mark.parametrize("path", LESSONS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_lesson_in_the_study_parses(path):
    lesson = parse_lesson(path.read_text(encoding="utf-8"))

    assert lesson["title"]
    assert lesson["reference"].startswith("Romans ")
    assert set(lesson["sections"]) <= {"Aim", "Content", "Cross-references", "Reflection"}
