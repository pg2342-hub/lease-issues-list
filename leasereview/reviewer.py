"""The judgment step: Claude reads the whole lease against the playbook, one call per lease.

For each standard position the model says whether the lease departs from it, matches it, or is
silent, quotes the lease word for word with the section number, and drafts the response a
landlord-side lawyer would send back. It never decides what reaches the issues list on its own:
guardrails.py checks every quote against the lease text and sends anything it cannot verify to
the lawyer as a check item.
"""

from __future__ import annotations

import json
import time
from typing import Any

from .playbook import Playbook

MODEL = "claude-opus-5-5"
EFFORT = "medium"
PROMPT_VERSION = "v2"
ATTEMPTS = 2  # a reply that skips positions is asked again once; anything still missing becomes a check
# USD per million tokens (input, output), first-party list prices.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-opus-4-8": (5.00, 25.00), "claude-sonnet-5-5": (2.00, 10.00)}

SYSTEM = """You are a careful real estate associate at a landlord-side law firm in New York.
You read a commercial lease against the firm's playbook of standard positions and prepare the
first draft of the issues list a partner will review before anything goes back to the other side.

Rules:
- Read the whole lease, including riders, exhibits and amendments that are part of the text.
- For every playbook position, decide one status:
  "departs": the lease gives the tenant more than the firm's standard position, as described
  under "departs if".
  "consistent": the lease says what the standard position says, or gives the landlord more.
  "not_found": the lease does not address the point. Do not guess from silence.
- Quote the lease word for word, copying the exact characters of the clause, 1 to 3 quotes per
  position, each under 80 words. Never paraphrase inside a quote. If you must skip words inside a
  quote, use "..." and keep each part exact. Give no quotes for "not_found".
- Give the section or article number where each quote sits, as the lease numbers it.
- Text replaced by asterisks or brackets was redacted from the public filing. Say so if it
  matters, and never guess what it said.
- "lease_says" is one plain sentence on what the lease does on this point.
- "why" is one or two sentences on how it differs from the standard position (or why it is
  consistent). No legal citations.
- "proposed_response" is what the firm would ask for, written as an instruction to the other
  side's counsel, for "departs" only. Leave it empty otherwise.
- "confidence" is low when the lease is ambiguous, redacted on the point, or spreads it across
  several sections you could not reconcile.
You are drafting for a lawyer, not giving legal advice to a client. Be exact and brief."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["lease", "positions"],
    "properties": {
        "lease": {
            "type": "object",
            "additionalProperties": False,
            "required": ["landlord", "tenant", "premises", "dated"],
            "properties": {
                "landlord": {"type": "string"},
                "tenant": {"type": "string"},
                "premises": {"type": "string"},
                "dated": {"type": "string"},
            },
        },
        "positions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "status", "sections", "quotes", "lease_says", "why", "proposed_response", "confidence"],
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["departs", "consistent", "not_found"]},
                    "sections": {"type": "array", "items": {"type": "string"}},
                    "quotes": {"type": "array", "items": {"type": "string"}},
                    "lease_says": {"type": "string"},
                    "why": {"type": "string"},
                    "proposed_response": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
            },
        },
    },
}


def prompt(playbook: Playbook, lease_text: str) -> str:
    book = [
        {"id": p.id, "topic": p.topic, "standard": p.standard, "departs_if": p.departs_if, "usual_response": p.response}
        for p in playbook.positions
    ]
    return (
        f"Playbook: {playbook.name} (we act for the {playbook.side}).\n"
        f"<playbook>\n{json.dumps(book, indent=1)}\n</playbook>\n\n"
        f"Answer every one of these position ids exactly once: {', '.join(playbook.ids)}.\n\n"
        f"<lease>\n{lease_text}\n</lease>"
    )


class ClaudeReviewer:
    def __init__(self, client: Any = None, model: str = MODEL, effort: str = EFFORT) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.model = model
        self.effort = effort

    def fingerprint(self) -> dict:
        return {"model": self.model, "effort": self.effort, "prompt": PROMPT_VERSION}

    def __call__(self, playbook: Playbook, lease_text: str) -> dict:
        """Review once; if the reply leaves out any position, ask again (at most ATTEMPTS calls)."""
        wanted = {p.id for p in playbook.positions}
        cost = latency = 0.0
        tokens_in = tokens_out = attempts = 0
        while attempts < ATTEMPTS:
            attempts += 1
            review, response, seconds = self._once(playbook, lease_text)
            cost += self.cost(response)
            latency += seconds
            tokens_in += response.usage.input_tokens
            tokens_out += response.usage.output_tokens
            if wanted <= {p.get("id") for p in review.get("positions", [])}:
                break
        review["_meta"] = {
            "model": getattr(response, "model", self.model),
            "cost_usd": round(cost, 4),
            "latency_s": round(latency, 2),
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "attempts": attempts,
        }
        return review

    def _once(self, playbook: Playbook, lease_text: str) -> tuple[dict, Any, float]:
        start = time.perf_counter()
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": SCHEMA}},
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt(playbook, lease_text)}],
        )
        latency = time.perf_counter() - start
        if response.stop_reason == "refusal":
            raise RuntimeError("the model declined this lease")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("the review was cut off at max_tokens")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text), response, latency

    def cost(self, response: Any) -> float:
        price = PRICES.get(getattr(response, "model", self.model)) or PRICES.get(self.model, (0.0, 0.0))
        usage = response.usage
        tokens_in = (usage.input_tokens or 0) + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
        tokens_in += 0.1 * (getattr(usage, "cache_read_input_tokens", 0) or 0)
        return round((tokens_in * price[0] + (usage.output_tokens or 0) * price[1]) / 1_000_000, 4)
