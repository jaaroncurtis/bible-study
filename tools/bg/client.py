"""Ties fetching, parsing, caching and slicing together.

A chapter is always requested whole, however narrow the reference: BibleGateway
returns the whole chapter regardless, so asking for it by name means one cached
file serves every later reference into it.
"""

from bg.cache import to_document
from bg.fetch import passage_url
from bg.parse import parse_chapter
from bg.passage import assemble
from bg.refs import parse_reference

DEFAULT_VERSION = "ESV"


class BibleGateway:
    def __init__(self, cache, fetcher, default_version=DEFAULT_VERSION):
        self.cache = cache
        self.fetcher = fetcher
        self.default_version = default_version

    def chapter(self, book, chapter, version=None, refresh=False):
        """Return one chapter's document, fetching it only if it is not cached."""
        version = version or self.default_version

        if not refresh:
            cached = self.cache.load(version, book, chapter)
            if cached is not None:
                return cached

        url = passage_url(f"{book} {chapter}", version)
        document = to_document(
            parse_chapter(self.fetcher.get(url), version=version),
            book=book,
            source_url=url,
        )
        self.cache.save(document)
        return document

    def passage(self, reference_text, version=None, refresh=False):
        """Return the verses of a reference, fetching whatever is not cached."""
        reference = parse_reference(reference_text)
        version = version or self.default_version

        documents = [
            self.chapter(reference.book, number, version=version, refresh=refresh)
            for number in reference.chapters()
        ]
        return assemble(reference, documents)
