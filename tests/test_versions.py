import pytest

from bg.versions import find_version, parse_versions


@pytest.fixture
def versions(fixture_html):
    return parse_versions(fixture_html("bg-versions.html"))


def test_every_translation_on_the_page_is_listed(versions):
    assert len(versions) == 240


def test_a_translation_carries_its_code_name_and_language(versions):
    asv = next(v for v in versions if v["code"] == "ASV")

    assert asv["name"] == "American Standard Version"
    assert asv["language"] == "English"
    assert asv["language_code"] == "en"


def test_the_code_is_stripped_out_of_the_display_name(versions):
    coded = [version for version in versions if version["code"]]

    assert coded
    assert all(f"({v['code']})" not in v["name"] for v in coded)


def test_a_parenthesised_subtitle_is_not_mistaken_for_a_code(versions):
    # A code is a single token; "Pavithar Bible (New India Bible Version)"
    # is a subtitle, and that translation publishes no code.
    pavithar = next(v for v in versions if v["name"].startswith("Pavithar Bible"))

    assert pavithar["code"] is None
    assert pavithar["name"] == "Pavithar Bible (New India Bible Version)"


def test_translations_without_a_parenthesised_code_are_still_listed(versions):
    unnamed = [v for v in versions if v["code"] is None]

    assert unnamed, "some BibleGateway translations print no code"
    assert all(version["name"] for version in unnamed)


def test_audio_availability_is_recorded_per_translation(versions):
    # BibleGateway has no machine-readable audio index; the versions table is
    # the only place that says which translations have a recording.
    assert sum(1 for version in versions if version["audio"]) == 34


def test_a_version_can_be_looked_up_by_code_case_insensitively(versions):
    assert find_version(versions, "esv")["code"] == "ESV"
    assert find_version(versions, "ESV")["name"] == "English Standard Version"


def test_looking_up_an_unknown_code_returns_nothing(versions):
    assert find_version(versions, "NOPE") is None
