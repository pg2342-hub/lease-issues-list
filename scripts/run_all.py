"""Review every lease (4 filed EDGAR leases and 6 constructed ones) and write the results.

    python scripts/run_all.py                        # replays the recorded Claude reviews, no key needed
    LEASE_LIVE=1 ANTHROPIC_API_KEY=... python scripts/run_all.py   # live reviews, recorded to recordings/

Writes reports/results.json (everything the demo page shows) and one Word issues list per
lease to docs/issues/<lease>.docx.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from leasereview import docx_out, guardrails, pipeline  # noqa: E402
from leasereview.fetch import fetch_all, leases  # noqa: E402
from leasereview.playbook import load  # noqa: E402
from leasereview.quotes import normalize  # noqa: E402


def main() -> int:
    playbook = load(pipeline.PLAYBOOK)
    review_fn = pipeline.reviewer()
    fetch_all()
    out: dict = {
        "playbook": {
            "name": playbook.name,
            "positions": [p.__dict__ for p in playbook.positions],
        },
        "edgar": [],
        "constructed": [],
    }
    issues_dir = ROOT / "docs" / "issues"
    for lease in leases():
        text = (ROOT / "leases" / "edgar" / f"{lease['id']}.txt").read_text(encoding="utf-8")
        result = pipeline.run(lease["id"], text, review_fn, playbook)
        docx_out.write(result.items, lease["label"], playbook.name, issues_dir / f"{lease['id']}.docx")
        out["edgar"].append(
            {
                **lease,
                "words": len(normalize(text).split()),
                "parties": result.review.get("lease", {}),
                "meta": result.meta,
                "summary": guardrails.summary(result.items),
                "items": [i.to_dict() for i in result.items],
            }
        )
        print(f"{lease['id']}: {guardrails.summary(result.items)}")

    key = pipeline.answer_key()
    for lid in sorted(key):
        text = (pipeline.CONSTRUCTED / f"{lid}.txt").read_text(encoding="utf-8")
        result = pipeline.run(lid, text, review_fn, playbook)
        s = pipeline.score(result, key[lid], playbook)
        out["constructed"].append({"id": lid, "meta": result.meta, "score": s, "summary": guardrails.summary(result.items)})
        print(f"{lid}: {s['right']}/{s['total']} right, {s['critical_misses']} critical misses")

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "results.json").write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
