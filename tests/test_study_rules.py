"""The study rules from CLAUDE.md, enforced.

"The study" is exactly the set of files study.json references. Meta-study files
such as outline.md are working documents and are deliberately out of scope.
"""

import json
import pathlib
import re

import pytest

from bg.refs import ReferenceError, parse_reference
from study.lesson import parse_lesson

STUDIES = pathlib.Path("studies")


def _studies():
    return sorted(STUDIES.glob("*/study.json"))


def _load(study_json):
    return json.loads(study_json.read_text(encoding="utf-8"))


def _study_files(study_json):
    """Every file the study consists of, tagged by kind."""
    root = study_json.parent
    data = _load(study_json)
    files = [("overview", root / data["overview"])]
    for section in data["sections"]:
        base = root / "sections" / section["dir"]
        files.append(("overview", base / section["overview"]))
        if section.get("teacher"):
            files.append(("teacher", base / section["teacher"]))
        for lesson in section["lessons"]:
            files.append(("lesson", base / lesson["file"]))
            if lesson.get("teacher"):
                files.append(("teacher", base / lesson["teacher"]))
    return files


ALL = [(s, kind, path) for s in _studies() for kind, path in _study_files(s)]
LEARNER = [(s, k, p) for s, k, p in ALL if k != "teacher"]


def _id(item):
    study, kind, path = item
    return f"{study.parent.name}/{path.relative_to(study.parent).as_posix()}"


def test_there_is_at_least_one_study_to_check():
    assert _studies()


# --- structure and identity -------------------------------------------------


@pytest.mark.parametrize("item", ALL, ids=_id)
def test_every_referenced_file_exists(item):
    assert item[2].exists()


@pytest.mark.parametrize("study_json", _studies(), ids=lambda p: p.parent.name)
def test_no_file_on_disk_is_orphaned_from_the_study(study_json):
    referenced = {path.resolve() for _, path in _study_files(study_json)}
    on_disk = {p.resolve() for p in (study_json.parent / "sections").rglob("*.md")}

    assert on_disk - referenced == set()


@pytest.mark.parametrize("study_json", _studies(), ids=lambda p: p.parent.name)
def test_ids_are_unique_and_below_the_counter(study_json):
    data = _load(study_json)
    ids = [l["id"] for s in data["sections"] for l in s["lessons"]]

    assert len(ids) == len(set(ids))
    assert max(ids) < data["nextId"]


@pytest.mark.parametrize("study_json", _studies(), ids=lambda p: p.parent.name)
def test_sequence_on_disk_is_contiguous_and_matches_the_json(study_json):
    data = _load(study_json)
    for n, section in enumerate(data["sections"], start=1):
        assert section["dir"] == f"{n:02d}-{section['key']}"
        for m, lesson in enumerate(section["lessons"], start=1):
            assert lesson["file"] == f"{m:02d}-{lesson['key']}.md"


@pytest.mark.parametrize("study_json", _studies(), ids=lambda p: p.parent.name)
def test_lesson_links_resolve_and_the_index_matches_the_prose(study_json):
    data = _load(study_json)
    root = study_json.parent
    ids = {l["id"] for s in data["sections"] for l in s["lessons"]}
    for section in data["sections"]:
        for lesson in section["lessons"]:
            prose = (root / "sections" / section["dir"] / lesson["file"]).read_text(
                encoding="utf-8"
            )
            found = sorted({int(n) for n in re.findall(r"\(lesson:(\d+)\)", prose)})
            assert set(found) <= ids, f"{lesson['file']} links to a missing lesson"
            assert lesson["links"] == found, f"{lesson['file']} links index is stale"


@pytest.mark.parametrize("item", LEARNER, ids=_id)
def test_no_bare_lesson_numbers_in_prose(item):
    # Links go by id; a literal "Lesson 23" would silently rot on renumber.
    assert not re.search(r"\bLesson \d+\b", item[2].read_text(encoding="utf-8"))


# --- content rules ----------------------------------------------------------


@pytest.mark.parametrize("item", ALL, ids=_id)
def test_the_study_never_mentions_the_notes(item):
    text = item[2].read_text(encoding="utf-8")
    pattern = re.compile(
        r"notes/|context note|context document|"
        r"\b(saving-faith|royal-prerogative|trajectory|translation|doulos) note\b",
        re.I,
    )
    assert not pattern.search(text)


GROUP = re.compile(
    r"\bthe room\b|\bout loud\b|\bcongregation\b|\blet people\b|\bthe class\b|"
    r"\bthe group\b|\bin front of\b|\bTeach (it|them|this)\b",
    re.I,
)


@pytest.mark.parametrize("item", LEARNER, ids=_id)
def test_learner_files_never_assume_a_room(item):
    lines = item[2].read_text(encoding="utf-8").splitlines()
    bad = [l for l in lines if GROUP.search(l)]
    assert not bad


@pytest.mark.parametrize("item", ALL, ids=_id)
def test_no_blockquoted_scripture(item):
    # Blockquotes are how verse text would arrive in bulk. Section guardrails that
    # are the author's own prose are allowed; nothing that reads like a verse.
    for line in item[2].read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            assert not re.search(r"\b\d+:\d+\s", line[:12])


@pytest.mark.parametrize("item", ALL, ids=_id)
def test_quoted_phrases_stay_short(item):
    # Short phrases in the author's prose are citation; anything long enough to be a
    # verse is not.
    for phrase in re.findall(r'"([^"\n]{2,})"', item[2].read_text(encoding="utf-8")):
        assert len(phrase.split()) <= 14, phrase


@pytest.mark.parametrize("item", ALL, ids=_id)
def test_no_stray_characters(item):
    text = item[2].read_text(encoding="utf-8")
    odd = {c for c in text if 0x2E80 <= ord(c) <= 0x9FFF or 0xAC00 <= ord(c) <= 0xD7AF}
    assert not odd, f"CJK characters: {odd}"


@pytest.mark.parametrize("item", LEARNER, ids=_id)
def test_learner_files_keep_election_relational(item):
    # The decretal frame, and the lapsarian debate it feeds, live in teacher notes.
    text = item[2].read_text(encoding="utf-8").lower()

    assert "lapsarian" not in text
    assert "decree" not in text


# --- references -------------------------------------------------------------


@pytest.mark.parametrize("item", [i for i in ALL if i[1] == "lesson"], ids=_id)
def test_every_cross_reference_parses(item):
    lesson = parse_lesson(item[2].read_text(encoding="utf-8"))
    for group in lesson["sections"].get("Cross-references", []):
        for entry in group["items"]:
            for reference in entry["references"]:
                try:
                    parse_reference(reference)
                except ReferenceError as error:
                    pytest.fail(f"{reference!r}: {error}")


# --- repository-wide --------------------------------------------------------


def test_the_repository_is_not_creative_commons_licensed():
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
        path = pathlib.Path(name)
        if path.exists():
            assert "creative commons" not in path.read_text(encoding="utf-8").lower()


def test_no_journal_data_is_committed():
    suspicious = [
        p
        for p in pathlib.Path(".").rglob("*")
        if ".git" not in p.parts
        and ".venv" not in p.parts
        and re.search(r"journal", p.name, re.I)
        and p.suffix in {".json", ".md", ".txt", ".db", ".sqlite"}
    ]
    assert not suspicious


def test_source_files_are_ascii():
    for path in pathlib.Path("tools").rglob("*.py"):
        assert all(b < 128 for b in path.read_bytes()), path
