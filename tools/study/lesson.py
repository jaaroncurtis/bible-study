"""Parse a lesson file into structured data.

The markdown is the authoring surface today, and the intention is that it
eventually becomes generated output with the JSON as the source. That only works
if the parse is deterministic, so the grammar below is enforced rather than
merely hoped for:

    # <Title>

    **<Reference>**

    ## Aim | Content | Cross-references | Reflection

    ### <optional subheading, opening a group within the section>

Sections must appear in that order, at most once each. Aim, Content and
Reflection are required; Cross-references is optional.
"""

import re

SECTION_ORDER = ["Aim", "Content", "Cross-references", "Reflection"]
REQUIRED_SECTIONS = ["Aim", "Content", "Reflection"]

# "- **Genesis 3:1-7** - the seizure itself." One note may cover several
# references ("**Exodus 33:18-19** and **Exodus 34:6-7** - Moses asks..."), so the
# references are a list and the note is shared.
_CROSSREF = re.compile(
    r"^(?P<refs>\*\*[^*]+\*\*(?:\s*(?:and|,)\s*\*\*[^*]+\*\*)*)"
    r"\s*[—-]\s*(?P<note>.+)$",
    re.S,
)


class LessonFormatError(ValueError):
    """The file does not follow the lesson grammar."""


def _blocks(lines):
    """Split a run of lines into paragraphs and bullet items."""
    paragraphs, items, buffer = [], [], []

    def flush():
        if buffer:
            paragraphs.append(" ".join(part.strip() for part in buffer).strip())
            buffer.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            flush()
            index += 1
            continue
        if line.startswith("- "):
            flush()
            item = [line[2:].strip()]
            index += 1
            # A bullet continues while its lines are indented.
            while index < len(lines) and lines[index].startswith("  ") and lines[index].strip():
                item.append(lines[index].strip())
                index += 1
            items.append(" ".join(item))
            continue
        buffer.append(line)
        index += 1

    flush()
    return paragraphs, items


def _group(heading, lines, section):
    paragraphs, items = _blocks(lines)
    if section == "Cross-references":
        parsed = []
        for item in items:
            match = _CROSSREF.match(item)
            if match is None:
                raise LessonFormatError(
                    f"cross-reference is not '**Reference** - note': {item!r}"
                )
            parsed.append(
                {
                    "references": re.findall(r"\*\*([^*]+)\*\*", match.group("refs")),
                    "note": match.group("note").strip(),
                }
            )
        items = parsed
    return {"heading": heading, "paragraphs": paragraphs, "items": items}


def parse_lesson(text):
    lines = text.splitlines()

    if not lines or not lines[0].startswith("# "):
        raise LessonFormatError("first line must be the lesson title, '# <Title>'")
    title = lines[0][2:].strip()

    body = lines[1:]
    reference = None
    for index, line in enumerate(body):
        if not line.strip():
            continue
        match = re.fullmatch(r"\*\*(.+)\*\*", line.strip())
        if match is None:
            raise LessonFormatError(
                "the reference must follow the title, wrapped in '**'"
            )
        reference = match.group(1).strip()
        body = body[index + 1 :]
        break
    if reference is None:
        raise LessonFormatError("no reference line found after the title")

    sections, seen = {}, []
    name = None
    heading = None
    buffer = []

    def close():
        if name is None:
            return
        group = _group(heading, buffer, name)
        if group["paragraphs"] or group["items"] or group["heading"]:
            sections.setdefault(name, []).append(group)
        buffer.clear()

    for line in body:
        if line.startswith("## "):
            close()
            name = line[3:].strip()
            heading = None
            if name not in SECTION_ORDER:
                raise LessonFormatError(
                    f"unknown section {name!r}; expected one of {SECTION_ORDER}"
                )
            if name in seen:
                raise LessonFormatError(f"section {name!r} appears more than once")
            seen.append(name)
            continue
        if line.startswith("### "):
            if name is None:
                raise LessonFormatError("a subheading appeared before any section")
            close()
            heading = line[4:].strip()
            continue
        if name is None and line.strip():
            raise LessonFormatError(f"text outside any section: {line.strip()!r}")
        buffer.append(line)
    close()

    ordered = [s for s in SECTION_ORDER if s in seen]
    if seen != ordered:
        raise LessonFormatError(
            f"sections are out of order: {seen}; expected {ordered}"
        )

    for required in REQUIRED_SECTIONS:
        if required not in sections:
            raise LessonFormatError(f"missing required section {required!r}")

    return {"title": title, "reference": reference, "sections": sections}
