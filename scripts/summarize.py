"""Print a Markdown summary of reports/results.json (used for the record workflow's job summary)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    res = json.loads((ROOT / "reports" / "results.json").read_text())
    print("## Filed leases\n")
    print("| Lease | Issues | Critical | Checks | Consistent | Quotes removed | Cost | Seconds |")
    print("|---|---|---|---|---|---|---|---|")
    for lease in res["edgar"]:
        s, m = lease["summary"], lease.get("meta", {})
        print(
            f"| {lease['label']} | {s['issue']} | {s['critical_issues']} | {s['check']} | {s['consistent']} | "
            f"{s.get('quotes_dropped', 0)} | ${m.get('cost_usd', 0):.2f} | {m.get('latency_s', 0):.0f} |"
        )
    right = sum(c["score"]["right"] for c in res["constructed"])
    total = sum(c["score"]["total"] for c in res["constructed"])
    crit = sum(c["score"]["critical_misses"] for c in res["constructed"])
    print(f"\n## Constructed leases\n\n{right} of {total} positions right, {crit} critical misses.")


if __name__ == "__main__":
    main()
