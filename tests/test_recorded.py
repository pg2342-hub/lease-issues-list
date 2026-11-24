"""Grade the recorded live Claude run. Skipped until the record workflow has run once."""

import pytest

from leasereview import pipeline, recorded

pytestmark = pytest.mark.skipif(not recorded.TAPE.exists(), reason="no recorded live run yet")


def test_replay_needs_no_key_and_meets_the_bar(playbook, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LEASE_LIVE", raising=False)
    review_fn = pipeline.reviewer()
    right = total = critical = 0
    for lid, expected in pipeline.answer_key().items():
        text = (pipeline.CONSTRUCTED / f"{lid}.txt").read_text()
        s = pipeline.score(pipeline.run(lid, text, review_fn, playbook), expected, playbook)
        right += s["right"]
        total += s["total"]
        critical += s["critical_misses"]
    assert critical == 0, "a departure from a critical position reached the lawyer as consistent"
    assert right >= 84, f"{right} of {total} positions right on the constructed leases"
