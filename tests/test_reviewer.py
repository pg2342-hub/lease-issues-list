import json
from types import SimpleNamespace

from leasereview import recorded
from leasereview.reviewer import SCHEMA, ClaudeReviewer, prompt


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        usage = SimpleNamespace(
            input_tokens=100_000, output_tokens=5_000, cache_creation_input_tokens=0, cache_read_input_tokens=0
        )
        return SimpleNamespace(
            stop_reason="end_turn",
            model="claude-opus-5-5",
            usage=usage,
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def test_prompt_lists_every_position_and_the_lease(playbook):
    text = prompt(playbook, "THE LEASE TEXT")
    assert all(pid in text for pid in playbook.ids)
    assert "<lease>\nTHE LEASE TEXT\n</lease>" in text


def test_call_uses_structured_output_and_reports_cost(playbook):
    payload = {"lease": {"landlord": "L", "tenant": "T", "premises": "P", "dated": "D"}, "positions": []}
    client = FakeClient(payload)
    review = ClaudeReviewer(client=client)(playbook, "lease")
    kw = client.calls[0]
    assert kw["output_config"]["format"] == {"type": "json_schema", "schema": SCHEMA}
    assert kw["model"] == "claude-opus-5-5"
    assert review["_meta"]["cost_usd"] == 0.5  # 100k in at $4/M + 5k out at $20/M
    assert review["lease"]["tenant"] == "T"


def test_record_then_replay_without_a_client(playbook, tmp_path):
    payload = {"lease": {"landlord": "", "tenant": "", "premises": "", "dated": ""}, "positions": []}
    tape = tmp_path / "t.jsonl"
    fp = {"model": "m", "effort": "e", "prompt": "v1"}
    live = recorded.recording(ClaudeReviewer(client=FakeClient(payload)), fp, tape)
    first = live(playbook, "lease A")
    again = recorded.replay(fp, tape)(playbook, "lease A")
    assert again == first
    import pytest

    with pytest.raises(LookupError):
        recorded.replay(fp, tape)(playbook, "lease B")
    with pytest.raises(LookupError):
        recorded.replay({**fp, "prompt": "v2"}, tape)(playbook, "lease A")
