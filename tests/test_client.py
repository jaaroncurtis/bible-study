import pytest

from bg.cache import Cache
from bg.client import BibleGateway


class RecordingFetcher:
    """Serves fixture HTML and records every URL it was asked for."""

    def __init__(self, pages):
        self.pages = pages
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        for marker, html in self.pages.items():
            if marker in url:
                return html
        raise AssertionError(f"unexpected fetch: {url}")


@pytest.fixture
def pages(fixture_html):
    romans8 = fixture_html("kjv-romans-8.html")
    # Romans 9 stands in as Romans 8's markup with the verse addresses rewritten.
    # The span class is exactly what the parser reads to place a verse, so this
    # exercises the real parsing path rather than a hand-built document.
    romans9 = romans8.replace("Rom-8-", "Rom-9-")
    return {"Romans+8": romans8, "Romans+9": romans9}


@pytest.fixture
def gateway(tmp_path, pages):
    return BibleGateway(
        cache=Cache(tmp_path),
        fetcher=RecordingFetcher(pages),
        default_version="KJV",
    )


def test_a_reference_is_fetched_parsed_and_returned(gateway):
    passage = gateway.passage("Romans 8:28-30")

    assert passage["reference"] == "Romans 8:28-30"
    assert [verse["num"] for verse in passage["verses"]] == [28, 29, 30]
    assert passage["verses"][0]["text"].startswith("And we know that all things work")


def test_the_whole_chapter_is_cached_even_for_a_narrow_reference(gateway, tmp_path):
    gateway.passage("Romans 8:28")

    cached = Cache(tmp_path).load("KJV", "Romans", 8)
    assert len(cached["verses"]) == 39


def test_a_second_reference_in_a_cached_chapter_does_not_refetch(gateway):
    gateway.passage("Romans 8:28-30")
    gateway.passage("Romans 8:1")

    assert len(gateway.fetcher.urls) == 1


def test_a_span_fetches_each_chapter_it_needs_once(gateway):
    gateway.passage("Romans 8:38-9:2")

    assert len(gateway.fetcher.urls) == 2


def test_refresh_refetches_a_chapter_already_cached(gateway):
    gateway.passage("Romans 8:1")
    gateway.passage("Romans 8:1", refresh=True)

    assert len(gateway.fetcher.urls) == 2


def test_the_requested_version_overrides_the_default(gateway):
    gateway.passage("Romans 8:1", version="ASV")

    assert "version=ASV" in gateway.fetcher.urls[0]


def test_a_chapter_is_requested_whole_never_as_the_narrow_reference(gateway):
    gateway.passage("Romans 8:28-30")

    assert "search=Romans+8&" in gateway.fetcher.urls[0]


def test_an_unknown_book_fails_before_any_request_is_made(gateway):
    from bg.refs import UnknownBookError

    with pytest.raises(UnknownBookError):
        gateway.passage("Romanz 8")

    assert gateway.fetcher.urls == []
