"""Command line entry point.

Every command prints JSON on stdout. That is deliberate: this is the first pass
of the notes pipeline, whose job is to get scripture into a structured form the
consolidation pass can read directly. Rendering belongs to a later pass.
"""

import argparse
import json
import pathlib
import sys

from bg.cache import Cache
from bg.client import DEFAULT_VERSION, BibleGateway
from bg.fetch import FetchError, Fetcher, Pacer
from bg.parse import PassageNotFoundError
from bg.passage import PassageRangeError
from bg.refs import ReferenceError, resolve_book
from bg.versions import filter_versions

REPORTED_ERRORS = (ReferenceError, PassageRangeError, PassageNotFoundError, FetchError)


def default_cache_root():
    """The repo's cache directory: tools/bg/__main__.py -> tools -> repo root."""
    return pathlib.Path(__file__).resolve().parents[2] / "cache"


def build_gateway(default_version=DEFAULT_VERSION):
    import requests

    root = default_cache_root()
    return BibleGateway(
        cache=Cache(root),
        fetcher=Fetcher(
            session=requests.Session(),
            pacer=Pacer(root / ".last_fetch"),
        ),
        default_version=default_version,
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bg",
        description="Fetch and cache scripture from BibleGateway as structured JSON.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser("fetch", help="print the verses of a reference")
    fetch.add_argument("reference", help='e.g. "Romans 8:28-30"')
    fetch.add_argument("--version", default=None, help="translation code, e.g. ESV")
    fetch.add_argument(
        "--refresh", action="store_true", help="refetch even if already cached"
    )

    chapter = commands.add_parser("chapter", help="print a whole chapter")
    chapter.add_argument("book")
    chapter.add_argument("chapter", type=int)
    chapter.add_argument("--version", default=None)
    chapter.add_argument("--refresh", action="store_true")

    versions = commands.add_parser("versions", help="list translations")
    versions.add_argument(
        "--filter", dest="text", default=None, help="match against name or code"
    )
    versions.add_argument("--language", default=None, help="language code, e.g. en")
    versions.add_argument(
        "--audio", action="store_true", help="only translations with a recording"
    )
    versions.add_argument("--refresh", action="store_true")

    search = commands.add_parser("search", help="keyword search across a translation")
    search.add_argument("query")
    search.add_argument("--version", default=None)
    search.add_argument(
        "--start", type=int, default=None, help="1-based offset of a later page"
    )
    search.add_argument("--refresh", action="store_true")

    plans = commands.add_parser("reading-plans", help="list reading plans")
    plans.add_argument("--refresh", action="store_true")

    commands.add_parser("cache-status", help="summarise what is cached")

    return parser


def main(argv=None, gateway=None):
    args = build_parser().parse_args(argv)
    gateway = gateway if gateway is not None else build_gateway()

    try:
        if args.command == "fetch":
            payload = gateway.passage(
                args.reference, version=args.version, refresh=args.refresh
            )
        elif args.command == "chapter":
            book, _ = resolve_book(args.book)
            payload = gateway.chapter(
                book, args.chapter, version=args.version, refresh=args.refresh
            )
        elif args.command == "versions":
            payload = filter_versions(
                gateway.versions(refresh=args.refresh),
                text=args.text,
                language=args.language,
                audio_only=args.audio,
            )
        elif args.command == "search":
            payload = gateway.search(
                args.query,
                version=args.version,
                start=args.start,
                refresh=args.refresh,
            )
        elif args.command == "reading-plans":
            payload = gateway.reading_plans(refresh=args.refresh)
        else:
            payload = gateway.cache.status()
    except REPORTED_ERRORS as error:
        print(str(error), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
