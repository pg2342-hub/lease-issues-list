from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from leasereview import pipeline  # noqa: E402
from leasereview.playbook import load  # noqa: E402


@pytest.fixture(scope="session")
def playbook():
    return load(pipeline.PLAYBOOK)


def oracle_review(playbook, lease_text: str, expected: dict[str, str]) -> dict:
    """A scripted reviewer that knows the answer key: quotes the real clause for each position."""
    import make_constructed as mc

    rows = []
    for p in playbook.positions:
        status = expected[p.id]
        quotes, sections = [], []
        if status != "not_found":
            clause = (mc.STANDARD if status == "consistent" else mc.DEPARTS)[p.id]
            first = clause.split(". ")[0]
            quotes = [first]
            m = re.search(r"(\d+)\.1 " + re.escape(clause[:40]), lease_text)
            sections = [f"Section {m.group(1)}.1"] if m else []
        rows.append(
            {
                "id": p.id,
                "status": status,
                "sections": sections,
                "quotes": quotes,
                "lease_says": "scripted",
                "why": "scripted",
                "proposed_response": p.response if status == "departs" else "",
                "confidence": "high",
            }
        )
    return {"lease": {"landlord": "", "tenant": "", "premises": "", "dated": ""}, "positions": rows}
