"""Record each live review once, then replay it with no API key.

CI and the demo page use recorded reviews, so they are free and repeatable; the record
workflow (.github/workflows/record.yml) refreshes them with real Claude calls. A recording is
keyed by the lease text, the playbook and the reviewer's model, effort and prompt version, so a
change to any of them needs a fresh recording instead of silently reusing an old one.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .playbook import Playbook

ROOT = Path(__file__).resolve().parent.parent / "recordings"
TAPE = ROOT / "reviews.jsonl"


def key(playbook: Playbook, lease_text: str, fingerprint: dict) -> str:
    raw = json.dumps(
        {"lease": hashlib.sha256(lease_text.encode()).hexdigest(), "playbook": playbook.fingerprint(), "reviewer": fingerprint},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load(path: Path) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["key"]] = row["value"]
    return rows


def recording(reviewer: Callable[[Playbook, str], dict], fingerprint: dict, path: Path = TAPE) -> Callable[[Playbook, str], dict]:
    def call(playbook: Playbook, lease_text: str) -> dict:
        review = reviewer(playbook, lease_text)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps({"key": key(playbook, lease_text, fingerprint), "value": review}, sort_keys=True) + "\n")
        return review

    return call


def replay(fingerprint: dict, path: Path = TAPE) -> Callable[[Playbook, str], dict]:
    rows = _load(path)

    def call(playbook: Playbook, lease_text: str) -> dict:
        k = key(playbook, lease_text, fingerprint)
        if k not in rows:
            raise LookupError(f"no recorded review for this lease, playbook and reviewer ({k}); run the record workflow")
        return rows[k]

    return call
