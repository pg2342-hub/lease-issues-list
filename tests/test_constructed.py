import make_constructed as mc
import yaml

from leasereview import guardrails, pipeline
from tests.conftest import oracle_review


def test_files_match_the_generator():
    key = yaml.safe_load((pipeline.CONSTRUCTED / "answers.yml").read_text())
    assert len(key) == 6
    for seed in range(6):
        text, answers = mc.build(seed)
        lid = f"constructed-{seed + 1}"
        assert (pipeline.CONSTRUCTED / f"{lid}.txt").read_text() == text
        assert key[lid] == answers


def test_every_status_is_represented():
    key = pipeline.answer_key()
    statuses = [s for a in key.values() for s in a.values()]
    for s in ("departs", "consistent", "not_found"):
        assert statuses.count(s) >= 5


def test_clause_variants_cover_the_playbook(playbook):
    assert set(mc.STANDARD) == set(mc.DEPARTS) == set(playbook.ids) == set(mc.TITLES)


def test_a_perfect_reviewer_scores_90_of_90(playbook):
    key = pipeline.answer_key()
    total = 0
    for lid, expected in key.items():
        text = (pipeline.CONSTRUCTED / f"{lid}.txt").read_text()
        result = pipeline.run(lid, text, lambda pb, t, e=expected: oracle_review(pb, t, e), playbook)
        s = pipeline.score(result, expected, playbook)
        assert s["critical_misses"] == 0
        total += s["right"]
        assert guardrails.summary(result.items)["quotes_dropped"] == 0
    assert total == 90


def test_a_reviewer_that_calls_everything_consistent_has_critical_misses(playbook):
    key = pipeline.answer_key()
    misses = 0
    for lid, expected in key.items():
        text = (pipeline.CONSTRUCTED / f"{lid}.txt").read_text()
        lazy = {k: ("consistent" if v == "departs" else v) for k, v in expected.items()}
        lazy_review = oracle_review(playbook, text, expected)
        for r in lazy_review["positions"]:
            r["status"] = lazy[r["id"]]
        result = pipeline.run(lid, text, lambda pb, t, rv=lazy_review: rv, playbook)
        misses += pipeline.score(result, expected, playbook)["critical_misses"]
    assert misses > 0
