"""Assemble a reference's verses from cached chapter documents.

Slicing happens here rather than at fetch time: a chapter is cached whole, so
every range within it -- and every range spanning several of them -- is a local
read. A verse keeps its chapter once it leaves its document, so a cross-chapter
span stays addressable in the note that quotes it.
"""


class PassageRangeError(ValueError):
    """The reference asks for verses the cached chapters do not hold."""


def assemble(reference, documents):
    by_chapter = {document["chapter"]: document for document in documents}

    verses = []
    headings = []
    copyrights = []
    version = None

    for chapter in reference.chapters():
        document = by_chapter.get(chapter)
        if document is None:
            raise PassageRangeError(
                f"no cached chapter for {reference.book} {chapter}"
            )

        numbers = [verse["num"] for verse in document["verses"]]
        if not numbers:
            raise PassageRangeError(f"{reference.book} {chapter} holds no verses")

        # A span only bounds the chapter it starts in and the one it ends in;
        # chapters in between are taken whole.
        starts_here = chapter == reference.start_chapter
        ends_here = chapter == reference.end_chapter
        first = reference.start_verse if starts_here and reference.start_verse else numbers[0]
        last = reference.end_verse if ends_here and reference.end_verse else numbers[-1]

        selected = [verse for verse in document["verses"] if first <= verse["num"] <= last]
        if not selected:
            raise PassageRangeError(
                f"{reference.book} {chapter} has verses "
                f"{numbers[0]}-{numbers[-1]}, not {first}-{last}"
            )

        version = version or document["version"]
        verses.extend({"chapter": chapter, **verse} for verse in selected)
        headings.extend(
            {"chapter": chapter, **heading}
            for heading in document["headings"]
            if first <= heading["before_verse"] <= last
        )

        notice = document.get("copyright")
        if notice and notice not in copyrights:
            copyrights.append(notice)

    return {
        "reference": reference.query(),
        "book": reference.book,
        "version": version,
        "verses": verses,
        "headings": headings,
        "copyright": copyrights,
    }
