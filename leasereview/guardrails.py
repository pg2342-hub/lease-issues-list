"""Turn the model's review into an issues list a lawyer can trust.

Rules, not the model, decide what each line of the issues list is:
- every quote is matched against the lease text; a quote that is not in the lease is dropped
  and never shown as the lease's words;
- a "departs" or "consistent" call with no verified quote becomes a check item for the lawyer;
- a low-confidence call becomes a check item;
- a position the lease does not address becomes a check item (silence can cost a landlord as
  much as a bad clause);
- a position the model skipped or answered twice becomes a check item;
- nothing is ever dropped: every playbook position ends up as an issue, a check or consistent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import quotes as q
from .playbook import Playbook

KINDS = ("issue", "check", "consistent")
SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}
KIND_ORDER = {"issue": 0, "check": 1, "consistent": 2}


@dataclass
class Quote:
    text: str
    verified: bool
    at: int | None = None


@dataclass
class Item:
    id: str
    topic: str
    severity: str
    kind: str
    model_status: str
    sections: list[str]
    quotes: list[Quote]
    lease_says: str
    why: str
    proposed_response: str
    standard: str
    reasons: list[str] = field(default_factory=list)
    dropped_quotes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def apply(playbook: Playbook, review: dict, lease_text: str) -> list[Item]:
    lease_norm = q.normalize(lease_text)
    answers: dict[str, list[dict]] = {}
    for row in review.get("positions", []):
        answers.setdefault(row.get("id", ""), []).append(row)

    items: list[Item] = []
    for p in playbook.positions:
        rows = answers.get(p.id, [])
        if len(rows) != 1:
            reason = "The review did not answer this position." if not rows else "The review answered this position twice."
            items.append(Item(p.id, p.topic, p.severity, "check", "missing", [], [], "", "", "", p.standard, [reason]))
            continue
        row = rows[0]
        status = row["status"]
        checked = []
        for text in row.get("quotes", []):
            at = q.find(text, lease_norm)
            checked.append(Quote(text=text, verified=at is not None, at=at))
        verified = [c for c in checked if c.verified]
        reasons = []
        dropped = len(checked) - len(verified)
        if dropped:
            reasons.append(f"{dropped} quote(s) could not be found word for word in the lease and were removed.")

        if status == "not_found":
            kind = "check"
            reasons.append("The lease does not appear to address this. Confirm, and add the standard clause if it is missing.")
        elif not verified:
            kind = "check"
            reasons.append("No quote could be verified against the lease, so this call needs a lawyer's read.")
        elif row.get("confidence") == "low":
            kind = "check"
            reasons.append("The review marked this call as low confidence.")
        else:
            kind = "issue" if status == "departs" else "consistent"

        items.append(
            Item(
                id=p.id,
                topic=p.topic,
                severity=p.severity,
                kind=kind,
                model_status=status,
                sections=list(dict.fromkeys(row.get("sections", []))),
                quotes=verified,
                lease_says=row.get("lease_says", ""),
                why=row.get("why", ""),
                proposed_response=row.get("proposed_response", "") if status == "departs" else "",
                standard=p.standard,
                reasons=reasons,
                dropped_quotes=dropped,
            )
        )
    items.sort(key=lambda i: (KIND_ORDER[i.kind], SEVERITY_ORDER[i.severity]))
    return items


def summary(items: list[Item]) -> dict:
    out = {k: sum(1 for i in items if i.kind == k) for k in KINDS}
    out["critical_issues"] = sum(1 for i in items if i.kind == "issue" and i.severity == "critical")
    out["quotes_verified"] = sum(len(i.quotes) for i in items)
    out["quotes_dropped"] = sum(i.dropped_quotes for i in items)
    return out
