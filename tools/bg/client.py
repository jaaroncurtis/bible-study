"""Ties fetching, parsing, caching and slicing together.

A chapter is always requested whole, however narrow the reference: BibleGateway
returns the whole chapter regardless, so asking for it by name means one cached
file serves every later reference into it.
"""

from bg.cache import to_document
from bg.fetch import PLANS_URL, VERSIONS_URL, passage_url, search_url
from bg.parse import parse_chapter
from bg.passage import assemble
from bg.plans import parse_plans
from bg.refs import parse_reference
from bg.search import parse_search
from bg.versions import parse_versions

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

    def _catalogue(self, url, parse, key, refresh):
        """Fetch a site-wide listing, or return the cached copy.

        These change rarely, so they are cached without expiry and refreshed
        only on request.
        """
        if not refresh:
            cached = self.cache.load_json("catalog", key)
            if cached is not None:
                return cached["items"]

        items = parse(self.fetcher.get(url))
        self.cache.save_json({"source_url": url, "items": items}, "catalog", key)
        return items

    def versions(self, refresh=False):
        """Every translation BibleGateway publishes, with audio availability."""
        return self._catalogue(VERSIONS_URL, parse_versions, "versions", refresh)

    def reading_plans(self, refresh=False):
        return self._catalogue(PLANS_URL, parse_plans, "reading-plans", refresh)

    def search(self, query, version=None, start=None, refresh=False):
        """One page of keyword search results, 25 hits at a time."""
        version = version or self.default_version
        key = f"{query} {start or 1}"

        if not refresh:
            cached = self.cache.load_json("search", version, key)
            if cached is not None:
                return cached

        url = search_url(query, version, start=start)
        found = parse_search(self.fetcher.get(url), query=query, version=version)
        found["source_url"] = url
        self.cache.save_json(found, "search", version, key)
        return found
