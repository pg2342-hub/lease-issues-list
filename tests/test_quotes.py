from leasereview import quotes as q

LEASE = q.normalize(
    "Tenant shall not assign this Lease\nwithout the prior written consent of Landlord’s agent — in each instance."
)


def test_exact_quote_across_line_break_and_typography():
    assert (
        q.find("Tenant shall not assign this Lease without the prior written consent of Landlord's agent - in each", LEASE) == 0
    )


def test_ellipsis_parts_must_appear_in_order():
    assert q.find("Tenant shall not assign ... in each instance", LEASE) is not None
    assert q.find("in each instance ... Tenant shall not assign", LEASE) is None


def test_paraphrase_is_rejected():
    assert q.find("Tenant may not assign this Lease without consent", LEASE) is None


def test_empty_quote_is_rejected():
    assert q.find("  ...  ", LEASE) is None


def test_case_insensitive():
    assert q.find("TENANT SHALL NOT ASSIGN", LEASE) == 0
