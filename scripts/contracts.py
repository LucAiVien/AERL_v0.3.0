"""Declarative contracts and run records for Automousera Research v0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Generic, Literal, TypeVar

T = TypeVar("T")
Direction = Literal["maximize", "minimize"]
EvidenceKind = Literal["literature", "measured", "hypothesis", "diagnostic"]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    direction: Direction
    description: str = ""

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name is required")
        if self.direction not in ("maximize", "minimize"):
            raise ValueError("metric direction must be maximize or minimize")


@dataclass(frozen=True)
class EvaluationContract:
    problem: str
    candidate_interface: str
    metric: MetricSpec
    inputs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    evaluator_id: str = "frozen-evaluator"
    iterations: int = 10
    execution_timeout_seconds: int | None = None
    target_score: float | None = None
    patience: int | None = None
    validation_protocol: str = ""
    final_test_visibility: str = "hidden-from-candidates"

    def validate(self) -> None:
        if not self.problem.strip():
            raise ValueError("problem is required")
        if not self.candidate_interface.strip():
            raise ValueError("candidate_interface is required")
        self.metric.validate()
        if self.iterations < 0:
            raise ValueError("iterations must be >= 0")
        if self.execution_timeout_seconds is not None and self.execution_timeout_seconds <= 0:
            raise ValueError("execution timeout must be positive")
        if self.patience is not None and self.patience <= 0:
            raise ValueError("patience must be positive")
        if not self.evaluator_id.strip():
            raise ValueError("evaluator_id is required so results can be traced")
        if not self.final_test_visibility.strip():
            raise ValueError("final_test_visibility is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evidence:
    kind: EvidenceKind
    claim: str
    source: str = ""
    confidence: str = ""


@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    rationale: str
    expected_effect: str = ""
    risk: str = ""
    falsification_test: str = ""


@dataclass
class ResearchRun(Generic[T]):
    contract: EvaluationContract
    seed_candidate: T
    seed_score: float
    priors: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    search_ledger: list[dict[str, Any]] = field(default_factory=list)
    best_candidate: T | None = None
    best_score: float | None = None
    verification_scores: list[float] = field(default_factory=list)
    ablations: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def improvement(self) -> float | None:
        if self.best_score is None:
            return None
        if self.contract.metric.direction == "maximize":
            return self.best_score - self.seed_score
        return self.seed_score - self.best_score


@dataclass
class AutonomousResearchRun(ResearchRun[T]):
    plan: list[dict[str, Any]] = field(default_factory=list)
    review_history: list[dict[str, Any]] = field(default_factory=list)
    agent_trace: list[dict[str, Any]] = field(default_factory=list)
    final_status: str = "in_progress"
    stop_reason: str = ""
    budget: dict[str, Any] = field(default_factory=dict)
    accepted_by_critic: bool = False
