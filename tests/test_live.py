"""One end-to-end check against the real site.

Excluded from the default run (``-m 'not live'``). Run it with
``pytest -m live`` after changing the parser, to catch markup drift that
fixtures cannot see. It uses the KJV so the network round trip carries only
public-domain text.
"""

import pytest

from bg.cache import Cache
from bg.client import BibleGateway
from bg.fetch import Fetcher, Pacer


@pytest.mark.live
def test_a_real_reference_round_trips(tmp_path):
    import requests

    gateway = BibleGateway(
        cache=Cache(tmp_path),
        fetcher=Fetcher(
            session=requests.Session(), pacer=Pacer(tmp_path / ".last_fetch")
        ),
        default_version="KJV",
    )

    passage = gateway.passage("John 3:16")

    assert passage["reference"] == "John 3:16"
    assert passage["verses"][0]["text"].startswith("For God so loved the world")
    assert Cache(tmp_path).status()["chapters"] == 1
