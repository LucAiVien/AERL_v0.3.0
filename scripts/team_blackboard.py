"""Append-only shared blackboard for Automousera multi-agent coordination.

This is run-scoped research state, not user-profile memory. Agents communicate
through explicit events/artifacts so failed attempts and reviewer objections are
preserved rather than overwritten.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TeamBlackboard:
    def __init__(self, path: str | Path, run_id: str = "run-1"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id

    def append(self, *, agent: str, event_type: str, payload: Any, artifact_id: str = "") -> dict[str, Any]:
        if not agent.strip() or not event_type.strip():
            raise ValueError("agent and event_type are required")
        if is_dataclass(payload):
            payload = asdict(payload)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "agent": agent,
            "event_type": event_type,
            "artifact_id": artifact_id,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def query(self, *, agent: str | None = None, event_type: str | None = None) -> list[dict[str, Any]]:
        rows = self.read_all()
        if agent is not None:
            rows = [r for r in rows if r.get("agent") == agent]
        if event_type is not None:
            rows = [r for r in rows if r.get("event_type") == event_type]
        return rows

    def checkpoint(self) -> dict[str, Any]:
        rows = self.read_all()
        return {
            "run_id": self.run_id,
            "event_count": len(rows),
            "last_event_type": rows[-1]["event_type"] if rows else None,
            "agents_seen": sorted({r["agent"] for r in rows}),
        }
