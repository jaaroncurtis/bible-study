import json

import pytest

from bg.__main__ import main
from bg.cache import Cache
from bg.client import BibleGateway


class StubFetcher:
    def __init__(self, html):
        self.html = html
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return self.html


@pytest.fixture
def gateway(tmp_path, fixture_html):
    return BibleGateway(
        cache=Cache(tmp_path),
        fetcher=StubFetcher(fixture_html("kjv-romans-8.html")),
        default_version="KJV",
    )


def test_fetch_prints_the_passage_as_json(gateway, capsys):
    code = main(["fetch", "Romans 8:28-30"], gateway=gateway)

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["reference"] == "Romans 8:28-30"
    assert [verse["num"] for verse in payload["verses"]] == [28, 29, 30]


def test_fetch_passes_the_requested_version_through(gateway, capsys):
    main(["fetch", "Romans 8:1", "--version", "ASV"], gateway=gateway)

    assert "version=ASV" in gateway.fetcher.urls[0]


def test_chapter_prints_the_whole_cached_chapter(gateway, capsys):
    code = main(["chapter", "Romans", "8"], gateway=gateway)

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["chapter"] == 8
    assert len(payload["verses"]) == 39


def test_an_unknown_book_reports_the_problem_and_fails(gateway, capsys):
    code = main(["fetch", "Romanz 8"], gateway=gateway)

    captured = capsys.readouterr()
    assert code != 0
    assert "Romans" in captured.err
    assert captured.out == ""


def test_a_reference_beyond_the_chapter_reports_the_problem(gateway, capsys):
    code = main(["fetch", "Romans 8:99"], gateway=gateway)

    assert code != 0
    assert "8" in capsys.readouterr().err


def test_cache_status_reports_what_is_stored(gateway, capsys):
    main(["fetch", "Romans 8:1"], gateway=gateway)
    capsys.readouterr()

    code = main(["cache-status"], gateway=gateway)

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["chapters"] == 1
    assert payload["versions"] == ["KJV"]


def test_refresh_is_passed_through(gateway, capsys):
    main(["fetch", "Romans 8:1"], gateway=gateway)
    main(["fetch", "Romans 8:1", "--refresh"], gateway=gateway)

    assert len(gateway.fetcher.urls) == 2
