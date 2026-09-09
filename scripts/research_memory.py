"""Append-only research memory for ERA Research v0.2.

This is experiment memory, not user-profile memory. It records provenance and
run events to JSONL so a later research pass can reuse verified findings without
silently rewriting history.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


class ResearchMemory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: Any) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type is required")
        if is_dataclass(payload):
            payload = asdict(payload)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def by_type(self, *event_types: str) -> list[dict[str, Any]]:
        wanted = set(event_types)
        return [r for r in self.read_all() if r.get("event_type") in wanted]
