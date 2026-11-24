from leasereview import guardrails

LEASE = """ARTICLE 5. ASSIGNMENT
5.1 Tenant may assign this Lease with the consent of Landlord, which consent shall not be unreasonably withheld.
ARTICLE 6. USE
6.1 Tenant shall use the Premises solely for general, executive and administrative offices.
"""


def row(pid, status, quotes=(), confidence="high"):
    return {
        "id": pid,
        "status": status,
        "sections": ["5.1"],
        "quotes": list(quotes),
        "lease_says": "x",
        "why": "y",
        "proposed_response": "fix it",
        "confidence": confidence,
    }


def review(rows):
    return {"lease": {}, "positions": rows}


def by_id(items):
    return {i.id: i for i in items}


def test_every_position_lands_in_exactly_one_kind(playbook):
    items = guardrails.apply(playbook, review([]), LEASE)
    assert len(items) == 15
    assert all(i.kind == "check" for i in items)
    assert all("did not answer" in i.reasons[0] for i in items)


def test_verified_departure_is_an_issue(playbook):
    r = review([row("assignment", "departs", ["consent shall not be unreasonably withheld"])])
    item = by_id(guardrails.apply(playbook, r, LEASE))["assignment"]
    assert item.kind == "issue"
    assert item.quotes[0].verified
    assert item.proposed_response == "fix it"


def test_invented_quote_is_dropped_and_sent_to_check(playbook):
    r = review([row("assignment", "departs", ["Landlord waives its recapture right"])])
    item = by_id(guardrails.apply(playbook, r, LEASE))["assignment"]
    assert item.kind == "check"
    assert item.quotes == []
    assert item.dropped_quotes == 1


def test_one_bad_quote_among_good_ones_is_removed(playbook):
    r = review([row("assignment", "departs", ["consent shall not be unreasonably withheld", "no recapture whatsoever"])])
    item = by_id(guardrails.apply(playbook, r, LEASE))["assignment"]
    assert item.kind == "issue"
    assert [x.text for x in item.quotes] == ["consent shall not be unreasonably withheld"]
    assert "removed" in item.reasons[0]


def test_consistent_without_quote_is_not_trusted(playbook):
    r = review([row("use", "consistent", [])])
    assert by_id(guardrails.apply(playbook, r, LEASE))["use"].kind == "check"


def test_low_confidence_goes_to_check(playbook):
    r = review([row("use", "consistent", ["solely for general, executive and administrative offices"], confidence="low")])
    assert by_id(guardrails.apply(playbook, r, LEASE))["use"].kind == "check"


def test_silence_goes_to_check(playbook):
    r = review([row("holdover", "not_found")])
    item = by_id(guardrails.apply(playbook, r, LEASE))["holdover"]
    assert item.kind == "check"
    assert item.proposed_response == ""


def test_duplicate_answer_goes_to_check(playbook):
    q = ["solely for general, executive and administrative offices"]
    r = review([row("use", "consistent", q), row("use", "departs", q)])
    assert by_id(guardrails.apply(playbook, r, LEASE))["use"].kind == "check"


def test_unknown_position_ids_are_ignored(playbook):
    r = review([row("rent_abatement", "departs", ["consent shall not be unreasonably withheld"])])
    assert len(guardrails.apply(playbook, r, LEASE)) == 15


def test_order_is_issues_then_checks_then_consistent_by_severity(playbook):
    r = review(
        [
            row("use", "consistent", ["solely for general, executive and administrative offices"]),
            row("assignment", "departs", ["consent shall not be unreasonably withheld"]),
        ]
    )
    items = guardrails.apply(playbook, r, LEASE)
    assert items[0].id == "assignment" and items[-1].id == "use"
    s = guardrails.summary(items)
    assert s == {"issue": 1, "check": 13, "consistent": 1, "critical_issues": 1, "quotes_verified": 2, "quotes_dropped": 0}
