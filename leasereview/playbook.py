"""Load and check a firm's playbook: the standard positions a lease is read against."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

SEVERITIES = ("critical", "major", "minor")


@dataclass(frozen=True)
class Position:
    id: str
    topic: str
    severity: str
    standard: str
    departs_if: str
    response: str


@dataclass(frozen=True)
class Playbook:
    name: str
    side: str
    positions: tuple[Position, ...]

    def get(self, position_id: str) -> Position:
        for p in self.positions:
            if p.id == position_id:
                return p
        raise KeyError(position_id)

    @property
    def ids(self) -> list[str]:
        return [p.id for p in self.positions]

    def fingerprint(self) -> str:
        raw = json.dumps([p.__dict__ for p in self.positions], sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


def load(path: str | Path) -> Playbook:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    positions = []
    seen = set()
    for raw in data["positions"]:
        p = Position(**{k: " ".join(str(raw[k]).split()) for k in Position.__dataclass_fields__})
        if p.severity not in SEVERITIES:
            raise ValueError(f"{p.id}: severity must be one of {SEVERITIES}")
        if p.id in seen:
            raise ValueError(f"duplicate position id {p.id}")
        seen.add(p.id)
        positions.append(p)
    if not positions:
        raise ValueError("a playbook needs at least one position")
    return Playbook(name=data["name"], side=data.get("side", "landlord"), positions=tuple(positions))
