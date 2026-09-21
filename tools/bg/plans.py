"""Parse BibleGateway's reading plan catalogue."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bg.fetch import BASE_URL
from bg.text import clean


def parse_plans(html):
    soup = BeautifulSoup(html, "lxml")

    plans = []
    for item in soup.select("div.plan-item"):
        link = item.select_one(".plan-title a")
        if link is None:
            continue
        description = item.select_one(".plan-desc")

        plans.append(
            {
                "id": item.get("data-plan_id"),
                "name": clean(link.get_text()),
                "url": urljoin(f"{BASE_URL}/", link.get("href") or ""),
                "description": clean(description.get_text()) if description else "",
            }
        )
    return plans
