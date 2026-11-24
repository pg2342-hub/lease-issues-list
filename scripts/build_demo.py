"""Build the demo page (docs/index.html) from reports/results.json.

    python scripts/run_all.py && python scripts/build_demo.py

The page is a working tool: pick a lease, read each issue with the clause in context, accept,
reject or edit the requested change, and download the issues list as a Word file built in the
browser. Every number on the page comes from results.json.
"""

from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "lease-issues-list"
sys.path.insert(0, str(ROOT))

from leasereview import quotes as q  # noqa: E402

CONTEXT = 320  # characters of lease text shown on each side of a quote


def context(raw: str, quote: str) -> dict:
    """The clause around a quote, cut from the lease's own text (the quote alone if it cannot be placed)."""
    flat = " ".join(raw.translate(q._TRANSLATE).split())
    first = q.parts(quote)[0] if q.parts(quote) else ""
    i = flat.lower().find(first) if first else -1
    if i < 0:
        return {"before": "", "quote": quote, "after": ""}
    end = i + len(first)
    return {
        "before": ("..." if i > CONTEXT else "") + flat[max(0, i - CONTEXT) : i],
        "quote": flat[i:end],
        "after": flat[end : end + CONTEXT] + ("..." if end + CONTEXT < len(flat) else ""),
    }


def data() -> dict:
    res = json.loads((ROOT / "reports" / "results.json").read_text())
    leases = []
    for lease in res["edgar"]:
        raw = (ROOT / "leases" / "edgar" / f"{lease['id']}.txt").read_text(encoding="utf-8")
        items = []
        for it in lease["items"]:
            ctx = [context(raw, x["text"]) for x in it["quotes"]]
            items.append(
                {
                    "id": it["id"],
                    "topic": it["topic"],
                    "severity": it["severity"],
                    "kind": it["kind"],
                    "sections": it["sections"],
                    "quotes": [x["text"] for x in it["quotes"]],
                    "context": ctx,
                    "says": it["lease_says"],
                    "why": it["why"],
                    "standard": it["standard"],
                    "response": it["proposed_response"],
                    "reasons": it["reasons"],
                }
            )
        leases.append(
            {
                "id": lease["id"],
                "label": lease["label"],
                "url": lease["url"],
                "filed": lease["filed"],
                "words": lease["words"],
                "summary": lease["summary"],
                "meta": lease["meta"],
                "items": items,
            }
        )
    constructed = [
        {
            "id": c["id"],
            "right": c["score"]["right"],
            "total": c["score"]["total"],
            "critical": c["score"]["critical_misses"],
            "rows": c["score"]["rows"],
            "meta": c["meta"],
        }
        for c in res["constructed"]
    ]
    return {"playbook": res["playbook"], "leases": leases, "constructed": constructed}


def money(x: float) -> str:
    return f"${x:,.2f}"


def page(d: dict) -> str:
    leases = d["leases"]
    cons = d["constructed"]
    right = sum(c["right"] for c in cons)
    total = sum(c["total"] for c in cons)
    crit = sum(c["critical"] for c in cons)
    metas = [lease["meta"] for lease in leases if lease.get("meta")]
    cost = sum(m.get("cost_usd", 0) for m in metas) / max(1, len(metas))
    secs = sum(m.get("latency_s", 0) for m in metas) / max(1, len(metas))
    words = sum(lease["words"] for lease in leases) / max(1, len(leases))
    model = metas[0].get("model", "claude-opus-5-5") if metas else "claude-opus-5-5"
    issues_total = sum(lease["summary"]["issue"] for lease in leases)
    checks_total = sum(lease["summary"]["check"] for lease in leases)
    dropped = sum(lease["summary"].get("quotes_dropped", 0) for lease in leases)
    verified = sum(lease["summary"].get("quotes_verified", 0) for lease in leases)

    # signature visual: 15 positions x 4 leases coverage grid
    pos = d["playbook"]["positions"]
    grid_rows = []
    for p in pos:
        cells = []
        for lease in leases:
            it = next(i for i in lease["items"] if i["id"] == p["id"])
            label = {"issue": "Issue", "check": "Check", "consistent": "Consistent"}[it["kind"]]
            cells.append(
                f'<button type="button" class="gc {it["kind"]}" data-lease="{lease["id"]}" data-pos="{p["id"]}" '
                f'aria-label="{html.escape(p["topic"])}, {html.escape(lease["label"])}: {label}"></button>'
            )
        grid_rows.append(
            f'<div class="grow"><span class="gname">{html.escape(p["topic"])}'
            f'<i class="sev sev-{p["severity"]}">{p["severity"]}</i></span>{"".join(cells)}</div>'
        )
    grid_head = "".join(f'<span class="gh" title="{html.escape(x["label"])}">{n}</span>' for n, x in enumerate(leases, 1))

    con_rows = []
    for n, c in enumerate(cons, 1):
        planted = sum(r["expected"] == "departs" for r in c["rows"])
        cells = "".join(
            f'<span class="cell {"crit" if r["critical_miss"] else ("pass" if r["right"] else "fail")}" '
            f'title="{html.escape(r["id"])}: expected {r["expected"]}, got {r["got"]}"></span>'
            for r in c["rows"]
        )
        con_rows.append(
            f'<div class="vrow"><div class="vwho"><b>Test lease {n}</b><span>{planted} departures planted</span></div>'
            f'<div class="strip" role="group" aria-label="Test lease {n}: every position">{cells}</div>'
            f'<div class="vscore"><b>{c["right"]}</b><span>of {c["total"]} right<br>{c["critical"]} critical</span></div></div>'
        )

    lease_buttons = "".join(
        f'<button type="button" role="radio" aria-checked="{"true" if i == 0 else "false"}" data-lease="{lease["id"]}">'
        f"Lease {i + 1}</button>"
        for i, lease in enumerate(leases)
    )
    playbook_rows = "".join(
        f'<tr><td>{html.escape(p["topic"])}</td><td><i class="sev sev-{p["severity"]}">{p["severity"]}</i></td>'
        f'<td class="tx">{html.escape(p["standard"])}</td></tr>'
        for p in pos
    )
    source_links = "".join(
        f'<li><a href="{html.escape(lease["url"])}">Lease {i + 1}</a>: {html.escape(lease["label"])}, filed {lease["filed"]}</li>'
        for i, lease in enumerate(leases)
    )
    payload = json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
    tpl = (ROOT / "scripts" / "demo_template.html").read_text(encoding="utf-8")
    subs = {
        "{{LEASE_BUTTONS}}": lease_buttons,
        "{{GRID_HEAD}}": grid_head,
        "{{GRID_ROWS}}": "".join(grid_rows),
        "{{CON_ROWS}}": "".join(con_rows),
        "{{RIGHT}}": str(right),
        "{{TOTAL}}": str(total),
        "{{CRIT}}": str(crit),
        "{{COST}}": money(cost),
        "{{SECS}}": f"{secs:.0f}",
        "{{WORDS}}": f"{words:,.0f}",
        "{{MODEL}}": html.escape(model),
        "{{ISSUES_TOTAL}}": str(issues_total),
        "{{CHECKS_TOTAL}}": str(checks_total),
        "{{DROPPED}}": str(dropped),
        "{{VERIFIED}}": str(verified),
        "{{NLEASES}}": str(len(leases)),
        "{{PLAYBOOK_ROWS}}": playbook_rows,
        "{{SOURCES}}": source_links,
        "{{DATA}}": payload,
    }
    for k, v in subs.items():
        tpl = tpl.replace(k, v)
    return tpl


def main() -> int:
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page(data()), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "demo_chrome.py"), str(out), "--repo", REPO], check=True)
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
