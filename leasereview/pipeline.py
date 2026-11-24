"""Run one lease through the reviewer and the guardrails, and score constructed leases."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import guardrails, recorded
from .playbook import Playbook
from .playbook import load as load_playbook

ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK = ROOT / "playbooks" / "landlord_office_ny.yml"
CONSTRUCTED = ROOT / "leases" / "constructed"

Reviewer = Callable[[Playbook, str], dict]


@dataclass
class Result:
    lease_id: str
    review: dict
    items: list[guardrails.Item]

    @property
    def meta(self) -> dict:
        return self.review.get("_meta", {})


def reviewer(live: bool | None = None) -> Reviewer:
    """The live Claude reviewer (recording every reply) or a replay of the recording."""
    from .reviewer import EFFORT, MODEL, PROMPT_VERSION, ClaudeReviewer

    fingerprint = {"model": MODEL, "effort": EFFORT, "prompt": PROMPT_VERSION}
    live = os.environ.get("LEASE_LIVE") == "1" if live is None else live
    if live:
        return recorded.recording(ClaudeReviewer(), fingerprint)
    return recorded.replay(fingerprint)


def run(lease_id: str, lease_text: str, review_fn: Reviewer, playbook: Playbook | None = None) -> Result:
    playbook = playbook or load_playbook(PLAYBOOK)
    review = review_fn(playbook, lease_text)
    return Result(lease_id, review, guardrails.apply(playbook, review, lease_text))


def answer_key() -> dict[str, dict[str, str]]:
    return yaml.safe_load((CONSTRUCTED / "answers.yml").read_text())


def score(result: Result, expected: dict[str, str], playbook: Playbook) -> dict:
    """Compare the final issues list with the answer key of a constructed lease.

    A position counts as right when the final kind matches: departs -> issue, consistent ->
    consistent, not_found -> check. A miss is critical when a departure from a critical position
    reaches the lawyer as consistent, which is the one error that would let a bad clause through.
    """
    want_kind = {"departs": "issue", "consistent": "consistent", "not_found": "check"}
    rows = []
    for item in result.items:
        want = expected[item.id]
        right = item.kind == want_kind[want]
        critical = want == "departs" and item.kind == "consistent" and playbook.get(item.id).severity == "critical"
        rows.append({"id": item.id, "expected": want, "got": item.kind, "right": right, "critical_miss": critical})
    return {
        "lease": result.lease_id,
        "right": sum(r["right"] for r in rows),
        "total": len(rows),
        "critical_misses": sum(r["critical_miss"] for r in rows),
        "missed_departures": sum(1 for r in rows if r["expected"] == "departs" and r["got"] == "consistent"),
        "rows": rows,
    }
