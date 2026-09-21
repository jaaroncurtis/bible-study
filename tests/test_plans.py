import pytest

from bg.plans import parse_plans


@pytest.fixture
def plans(fixture_html):
    return parse_plans(fixture_html("bg-reading-plans.html"))


def test_every_plan_on_the_page_is_listed(plans):
    assert len(plans) == 18


def test_a_plan_carries_its_id_name_and_description(plans):
    chronological = next(plan for plan in plans if plan["id"] == "chronological")

    assert chronological["name"] == "Chronological"
    assert "chronological" in chronological["description"].lower()


def test_a_plan_carries_an_absolute_url(plans):
    plan = next(plan for plan in plans if plan["id"] == "old-new-testament")

    assert plan["url"] == (
        "https://www.biblegateway.com/reading-plans/old-new-testament/next"
    )


def test_plans_are_listed_in_page_order(plans):
    assert plans[0]["id"] == "old-new-testament"
