"""Multi-agent protocol primitives for Automousera Research v0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AgentRole = Literal[
    "orchestrator",
    "literature-scout",
    "hypothesis-scientist",
    "experiment-planner",
    "era-search-worker",
    "critic-reviewer",
    "statistical-verifier",
    "ablation-analyst",
    "reporter",
]
ReviewVerdict = Literal["accept", "revise", "reject"]


@dataclass(frozen=True)
class AgentTask:
    id: str
    assigned_to: AgentRole
    objective: str
    requested_outputs: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 50

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("task id is required")
        if not self.objective.strip():
            raise ValueError("task objective is required")
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentArtifact:
    id: str
    task_id: str
    agent: AgentRole
    kind: str
    content: Any
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id.strip() or not self.task_id.strip():
            raise ValueError("artifact id and task_id are required")
        if not self.kind.strip():
            raise ValueError("artifact kind is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewDecision:
    verdict: ReviewVerdict
    rationale: str
    concerns: tuple[str, ...] = ()
    requested_experiments: tuple[str, ...] = ()
    confidence: float = 0.5

    def validate(self) -> None:
        if self.verdict not in ("accept", "revise", "reject"):
            raise ValueError("invalid review verdict")
        if not self.rationale.strip():
            raise ValueError("review rationale is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.verdict == "revise" and not self.requested_experiments:
            raise ValueError("revise verdict requires at least one requested experiment")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
