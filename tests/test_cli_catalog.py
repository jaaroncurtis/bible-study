import json

import pytest

from bg.__main__ import main
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


def run(args, gateway, capsys):
    code = main(args, gateway=gateway)
    captured = capsys.readouterr()
    return code, captured


def test_versions_lists_every_translation(gateway, capsys):
    code, captured = run(["versions"], gateway, capsys)

    assert code == 0
    assert len(json.loads(captured.out)) == 240


def test_versions_can_be_narrowed_by_text(gateway, capsys):
    _, captured = run(["versions", "--filter", "english standard"], gateway, capsys)

    listed = json.loads(captured.out)
    assert [version["code"] for version in listed] == ["ESV", "ESVUK"]


def test_the_filter_matches_the_code_as_well_as_the_name(gateway, capsys):
    _, captured = run(["versions", "--filter", "KJ21"], gateway, capsys)

    assert [version["code"] for version in json.loads(captured.out)] == ["KJ21"]


def test_versions_can_be_narrowed_to_one_language(gateway, capsys):
    _, captured = run(["versions", "--language", "en"], gateway, capsys)

    listed = json.loads(captured.out)
    assert listed
    assert all(version["language_code"] == "en" for version in listed)


def test_versions_can_be_narrowed_to_those_with_audio(gateway, capsys):
    _, captured = run(["versions", "--audio"], gateway, capsys)

    listed = json.loads(captured.out)
    assert len(listed) == 34
    assert all(version["audio"] for version in listed)


def test_search_prints_results_as_json(gateway, capsys):
    code, captured = run(["search", "faith"], gateway, capsys)

    payload = json.loads(captured.out)
    assert code == 0
    assert payload["total"] == 336
    assert payload["results"][0]["reference"] == "Numbers 12:7"


def test_search_accepts_a_page_offset(gateway, capsys):
    run(["search", "faith", "--start", "26"], gateway, capsys)

    assert "startnumber=26" in gateway.fetcher.urls[0]


def test_reading_plans_are_listed(gateway, capsys):
    code, captured = run(["reading-plans"], gateway, capsys)

    listed = json.loads(captured.out)
    assert code == 0
    assert len(listed) == 18
    assert listed[0]["name"] == "Old/New Testament"
