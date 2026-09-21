"""Storage for fetched chapters.

The chapter is both the fetch unit and the cache unit: BibleGateway returns a
whole chapter however narrow the reference, so caching per chapter makes any
later verse range a local slice. Files are plain indented JSON so a cached
chapter can be read, diffed and consumed by the note-building passes directly.
"""

import json
import pathlib
from dataclasses import asdict
from datetime import datetime, timezone

SCHEMA = 1


def to_document(chapter, book, source_url, fetched_at=None):
    """Build the cacheable document for a parsed chapter.

    ``book`` is the canonical name ("1 Corinthians") rather than the code in the
    markup ("1Cor"), because it names the directory a human will browse.
    """
    moment = fetched_at or datetime.now(timezone.utc)
    return {
        "schema": SCHEMA,
        "version": chapter.version,
        "book": book,
        "book_osis": chapter.book_code,
        "chapter": chapter.chapter,
        "fetched_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": source_url,
        "copyright": chapter.copyright,
        "headings": [asdict(heading) for heading in chapter.headings],
        "verses": [asdict(verse) for verse in chapter.verses],
    }


class Cache:
    def __init__(self, root):
        self.root = pathlib.Path(root)

    def path_for(self, version, book, chapter):
        # Zero-padded to three so Psalm 8, 99 and 150 sort in reading order.
        return self.root / version / book / f"{chapter:03d}.json"

    def load(self, version, book, chapter):
        path = self.path_for(version, book, chapter)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, document):
        path = self.path_for(document["version"], document["book"], document["chapter"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path

    def chapter_files(self):
        return sorted(self.root.glob("*/*/*.json"))

    def status(self):
        files = self.chapter_files()
        return {
            "chapters": len(files),
            "versions": sorted({path.parent.parent.name for path in files}),
        }
