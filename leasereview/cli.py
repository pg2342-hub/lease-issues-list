"""Review a lease from the command line and write the Word issues list.

lease-review leases/constructed/constructed-1.txt --out issues.docx          # replays a recorded review
LEASE_LIVE=1 ANTHROPIC_API_KEY=... lease-review my_lease.txt --out issues.docx   # a live Claude review
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import docx_out, guardrails, pipeline
from .fetch import html_to_text
from .playbook import load


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lease-review", description=__doc__.splitlines()[0])
    ap.add_argument("lease", help="the lease as .txt, .html or .docx")
    ap.add_argument("--playbook", default=str(pipeline.PLAYBOOK))
    ap.add_argument("--out", default="issues.docx")
    args = ap.parse_args(argv)

    path = Path(args.lease)
    if path.suffix.lower() in (".html", ".htm"):
        text = html_to_text(path.read_text(encoding="utf-8", errors="replace"))
    elif path.suffix.lower() == ".docx":
        from docx import Document

        text = "\n".join(p.text for p in Document(str(path)).paragraphs)
    else:
        text = path.read_text(encoding="utf-8")

    playbook = load(args.playbook)
    try:
        result = pipeline.run(path.stem, text, pipeline.reviewer(), playbook)
    except LookupError as e:
        print(f"{e}\nSet LEASE_LIVE=1 and ANTHROPIC_API_KEY to review a new lease.", file=sys.stderr)
        return 2
    docx_out.write(result.items, path.name, playbook.name, args.out)
    s = guardrails.summary(result.items)
    counts = f"{s['issue']} issues ({s['critical_issues']} critical), {s['check']} to check, {s['consistent']} consistent"
    print(f"{counts} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
