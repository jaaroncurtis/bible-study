"""Retrieving pages from BibleGateway.

BibleGateway's robots.txt allows /passage/ and /quicksearch/ but asks for a
15 second crawl delay. The Pacer honours it across process boundaries by
keeping the last request time on disk, so a run of short commands cannot
sidestep the delay simply by starting a new process each time. Cache hits never
reach the Pacer, so working through an already-cached book stays instant.
"""

import time
from urllib.parse import urlencode

BASE_URL = "https://www.biblegateway.com"
PASSAGE_URL = f"{BASE_URL}/passage/"
SEARCH_URL = f"{BASE_URL}/quicksearch/"
CRAWL_DELAY_SECONDS = 15.0
USER_AGENT = "bible-studies/0.1 (personal Bible study tool; one reader, cached locally)"

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class FetchError(RuntimeError):
    """BibleGateway did not return a usable page."""


def passage_url(query, version):
    return f"{PASSAGE_URL}?{urlencode({'search': query, 'version': version})}"


def search_url(query, version):
    return f"{SEARCH_URL}?{urlencode({'quicksearch': query, 'version': version})}"


class Pacer:
    """Keeps BibleGateway's crawl delay between requests, across runs."""

    def __init__(self, state_path, min_interval=CRAWL_DELAY_SECONDS, clock=None, sleep=None):
        self.state_path = state_path
        self.min_interval = min_interval
        self._clock = clock or time.time
        self._sleep = sleep or time.sleep

    def _last_request(self):
        try:
            return float(self.state_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def wait(self):
        """Block until the crawl delay since the last request has elapsed."""
        last = self._last_request()
        if last is None:
            return 0.0
        remaining = self.min_interval - (self._clock() - last)
        if remaining <= 0:
            return 0.0
        self._sleep(remaining)
        return remaining

    def mark(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(f"{self._clock()}", encoding="utf-8")


class Fetcher:
    def __init__(
        self,
        session,
        pacer,
        user_agent=USER_AGENT,
        retries=3,
        backoff=2.0,
        timeout=30,
        sleep=None,
    ):
        self.session = session
        self.pacer = pacer
        self.user_agent = user_agent
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout
        self._sleep = sleep or time.sleep

    def get(self, url):
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.retries):
            self.pacer.wait()
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            self.pacer.mark()

            if 200 <= response.status_code < 300:
                return response.text

            if response.status_code not in _RETRY_STATUSES:
                raise FetchError(f"{url} returned {response.status_code}")

            if attempt == self.retries - 1:
                raise FetchError(
                    f"{url} returned {response.status_code} "
                    f"after {self.retries} attempts"
                )
            self._sleep(self.backoff * (2**attempt))

        raise FetchError(f"{url} could not be retrieved")
