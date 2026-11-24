"""Check that a quote really appears in the lease.

The model must quote the lease word for word. Typography differs between a filed HTML
exhibit and a model's output (curly quotes, dashes, non-breaking spaces, line breaks), so both
sides are normalized the same way before matching. A quote with an ellipsis is checked as
several parts that must appear in order.
"""

from __future__ import annotations

import re
import unicodedata

_TRANSLATE = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "‑": "-",
        " ": " ",
        "​": "",
        "﻿": "",
        "­": "",
    }
)
_ELLIPSIS = re.compile(r"\s*(?:\.\s*\.\s*\.|…)\s*")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_TRANSLATE)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def parts(quote: str) -> list[str]:
    return [p for p in (normalize(x) for x in _ELLIPSIS.split(quote)) if p]


def find(quote: str, lease_norm: str) -> int | None:
    """Position of the quote in the normalized lease, or None if any part is missing or out of order."""
    pieces = parts(quote)
    if not pieces:
        return None
    start = None
    at = 0
    for piece in pieces:
        i = lease_norm.find(piece, at)
        if i < 0:
            return None
        if start is None:
            start = i
        at = i + len(piece)
    return start


def word_count(quote: str) -> int:
    return len(normalize(quote).split())
