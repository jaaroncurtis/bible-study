"""Whitespace handling shared by every page parser."""

import re


def clean(text):
    """Collapse runs of whitespace, including the non-breaking spaces
    BibleGateway puts after verse numbers, into single spaces."""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
