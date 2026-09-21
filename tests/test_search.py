import pytest

from bg.search import parse_search


@pytest.fixture
def results(fixture_html):
    return parse_search(
        fixture_html("bg-quicksearch-faith.html"), query="faith", version="KJV"
    )


def test_the_search_echoes_its_query_and_version(results):
    assert results["query"] == "faith"
    assert results["version"] == "KJV"


def test_the_total_number_of_hits_is_reported(results):
    assert results["total"] == 336


def test_one_page_of_results_is_returned(results):
    assert len(results["results"]) == 25


def test_a_result_carries_its_reference_and_snippet(results):
    first = results["results"][0]

    assert first["reference"] == "Numbers 12:7"
    assert first["text"] == (
        "My servant Moses is not so, who is faithful in all mine house."
    )


def test_a_result_carries_the_machine_readable_osis_address(results):
    assert results["results"][0]["osis"] == "Num.12.7"


def test_the_in_context_and_full_chapter_links_are_not_part_of_the_snippet(results):
    assert all("In Context" not in hit["text"] for hit in results["results"])
    assert all("Full Chapter" not in hit["text"] for hit in results["results"])


def test_the_next_page_offset_is_reported_so_paging_is_possible(results):
    assert results["next_start"] == 26


def test_a_suggested_result_is_not_counted_as_a_verse_hit(results):
    # BibleGateway prepends a promoted chapter-level card (an <article>) above
    # the verse list; it is not one of the numbered results.
    assert all(hit["reference"] != "Hebrews 11" for hit in results["results"])
