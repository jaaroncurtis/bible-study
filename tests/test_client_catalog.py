import pytest

from bg.cache import Cache
from bg.client import BibleGateway


class RecordingFetcher:
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
def gateway(tmp_path, fixture_html):
    return BibleGateway(
        cache=Cache(tmp_path),
        fetcher=RecordingFetcher(
            {
                "/versions/": fixture_html("bg-versions.html"),
                "/quicksearch/": fixture_html("bg-quicksearch-faith.html"),
                "/reading-plans/": fixture_html("bg-reading-plans.html"),
            }
        ),
        default_version="KJV",
    )


def test_the_translation_catalogue_is_fetched_and_parsed(gateway):
    versions = gateway.versions()

    assert len(versions) == 240
    assert any(version["code"] == "ESV" for version in versions)


def test_the_translation_catalogue_is_fetched_only_once(gateway):
    gateway.versions()
    gateway.versions()

    assert len(gateway.fetcher.urls) == 1


def test_refreshing_refetches_the_translation_catalogue(gateway):
    gateway.versions()
    gateway.versions(refresh=True)

    assert len(gateway.fetcher.urls) == 2


def test_a_search_returns_parsed_results(gateway):
    found = gateway.search("faith")

    assert found["version"] == "KJV"
    assert found["total"] == 336
    assert len(found["results"]) == 25


def test_the_same_search_is_not_run_twice(gateway):
    gateway.search("faith")
    gateway.search("faith")

    assert len(gateway.fetcher.urls) == 1


def test_a_search_on_a_later_page_is_cached_separately(gateway):
    gateway.search("faith")
    gateway.search("faith", start=26)

    assert len(gateway.fetcher.urls) == 2


def test_a_later_page_is_requested_with_its_offset(gateway):
    gateway.search("faith", start=26)

    assert "startnumber=26" in gateway.fetcher.urls[0]


def test_reading_plans_are_fetched_and_parsed(gateway):
    plans = gateway.reading_plans()

    assert len(plans) == 18
    assert plans[0]["id"] == "old-new-testament"


def test_reading_plans_are_fetched_only_once(gateway):
    gateway.reading_plans()
    gateway.reading_plans()

    assert len(gateway.fetcher.urls) == 1


def test_catalogue_documents_do_not_count_as_cached_chapters(gateway):
    gateway.versions()
    gateway.search("faith")
    gateway.reading_plans()

    assert gateway.cache.status()["chapters"] == 0
