import pytest

from bg.fetch import FetchError, Fetcher, Pacer, passage_url


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now
        self.slept = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class FakeResponse:
    def __init__(self, status_code, text="<html></html>"):
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": headers or {}, "timeout": timeout})
        return self.responses.pop(0)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def pacer(tmp_path, clock):
    return Pacer(tmp_path / "last_fetch", min_interval=15.0, clock=clock.time, sleep=clock.sleep)


def test_passage_url_carries_the_reference_and_version():
    url = passage_url("Romans 8:28-30", "ESV")

    assert url.startswith("https://www.biblegateway.com/passage/?")
    assert "search=Romans+8%3A28-30" in url
    assert "version=ESV" in url


def test_the_first_request_of_all_does_not_wait(pacer, clock):
    pacer.wait()

    assert clock.slept == []


def test_a_request_inside_the_crawl_delay_waits_out_the_remainder(pacer, clock):
    pacer.wait()
    pacer.mark()
    clock.now += 4.0

    pacer.wait()

    assert clock.slept == [pytest.approx(11.0)]


def test_a_request_after_the_crawl_delay_does_not_wait(pacer, clock):
    pacer.mark()
    clock.now += 20.0

    pacer.wait()

    assert clock.slept == []


def test_pacing_survives_a_restart(tmp_path, clock):
    state = tmp_path / "last_fetch"
    Pacer(state, min_interval=15.0, clock=clock.time, sleep=clock.sleep).mark()
    clock.now += 5.0

    Pacer(state, min_interval=15.0, clock=clock.time, sleep=clock.sleep).wait()

    assert clock.slept == [pytest.approx(10.0)]


def test_a_successful_request_returns_the_body(pacer):
    session = FakeSession([FakeResponse(200, "<html>Romans</html>")])
    fetcher = Fetcher(session=session, pacer=pacer, user_agent="bible-studies/0.1")

    assert fetcher.get("https://example.invalid/") == "<html>Romans</html>"


def test_the_request_identifies_itself(pacer):
    session = FakeSession([FakeResponse(200)])
    Fetcher(session=session, pacer=pacer, user_agent="bible-studies/0.1").get(
        "https://example.invalid/"
    )

    assert session.calls[0]["headers"]["User-Agent"] == "bible-studies/0.1"


def test_a_server_error_is_retried_until_it_succeeds(pacer, clock):
    session = FakeSession(
        [FakeResponse(503), FakeResponse(503), FakeResponse(200, "<html>ok</html>")]
    )
    fetcher = Fetcher(
        session=session, pacer=pacer, user_agent="ua", retries=3, backoff=2.0,
        sleep=clock.sleep,
    )

    assert fetcher.get("https://example.invalid/") == "<html>ok</html>"
    assert len(session.calls) == 3


def test_a_server_error_that_never_clears_is_reported(pacer, clock):
    session = FakeSession([FakeResponse(503), FakeResponse(503), FakeResponse(503)])
    fetcher = Fetcher(
        session=session, pacer=pacer, user_agent="ua", retries=3, backoff=2.0,
        sleep=clock.sleep,
    )

    with pytest.raises(FetchError) as excinfo:
        fetcher.get("https://example.invalid/")

    assert "503" in str(excinfo.value)


def test_a_client_error_is_not_retried(pacer, clock):
    session = FakeSession([FakeResponse(404)])
    fetcher = Fetcher(session=session, pacer=pacer, user_agent="ua", sleep=clock.sleep)

    with pytest.raises(FetchError):
        fetcher.get("https://example.invalid/")

    assert len(session.calls) == 1


def test_consecutive_requests_are_paced(pacer, clock):
    session = FakeSession([FakeResponse(200), FakeResponse(200)])
    fetcher = Fetcher(session=session, pacer=pacer, user_agent="ua", sleep=clock.sleep)

    fetcher.get("https://example.invalid/one")
    fetcher.get("https://example.invalid/two")

    assert clock.slept == [pytest.approx(15.0)]
