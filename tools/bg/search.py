"""Parse BibleGateway's keyword search results.

Results come 25 to a page. The page reports the full hit count and, when there
is more, the offset of the next page; paging is left to the caller because each
further page is another network request under the crawl delay.
"""

import copy
import re

from bs4 import BeautifulSoup

from bg.text import clean

_TOTAL = re.compile(r"([\d,]+)\s+Bible results", re.IGNORECASE)
_START_NUMBER = re.compile(r"startnumber=(\d+)")


def parse_search(html, query, version):
    soup = BeautifulSoup(html, "lxml")

    total = None
    showing = soup.select_one(".showing-results")
    if showing is not None:
        match = _TOTAL.search(showing.get_text(" "))
        if match:
            total = int(match.group(1).replace(",", ""))

    results = []
    # Only the verse list counts. BibleGateway also promotes a chapter-level
    # card above it, which is a suggestion rather than a numbered hit.
    for item in soup.select("div.search-result-list li.bible-item"):
        title = item.select_one("a.bible-item-title")
        body = item.select_one("div.bible-item-text")
        if title is None or body is None:
            continue

        snippet = copy.copy(body)
        for extras in snippet.select(".bible-item-extras"):
            extras.decompose()

        results.append(
            {
                "reference": clean(title.get_text()),
                "osis": item.get("data-osis"),
                "text": clean(snippet.get_text()),
            }
        )

    next_start = None
    pager = soup.select_one("a[href*='startnumber']")
    if pager is not None:
        match = _START_NUMBER.search(pager.get("href") or "")
        if match:
            next_start = int(match.group(1))

    return {
        "query": query,
        "version": version,
        "total": total,
        "results": results,
        "next_start": next_start,
    }
