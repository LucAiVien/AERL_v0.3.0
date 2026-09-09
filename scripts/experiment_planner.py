"""Research-plan construction for Automousera Research v0.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from contracts import EvaluationContract, Evidence, Hypothesis


@dataclass(frozen=True)
class PlannedExperiment:
    id: str
    hypothesis_id: str
    objective: str
    priority: int = 50
    rationale: str = ""

    def to_dict(self):
        return asdict(self)


def default_plan(
    contract: EvaluationContract,
    priors: list[Evidence],
    hypotheses: list[Hypothesis],
) -> list[PlannedExperiment]:
    """Create a hypothesis-driven experiment queue.

    The ERA search worker may still explore outside this queue, but every
    hypothesis gets at least one explicit experiment objective.
    """
    plan: list[PlannedExperiment] = []
    for i, hypothesis in enumerate(hypotheses, 1):
        plan.append(
            PlannedExperiment(
                id=f"E{i}",
                hypothesis_id=hypothesis.id,
                objective=f"Test: {hypothesis.statement}",
                priority=max(1, 100 - (i - 1) * 10),
                rationale=hypothesis.rationale,
            )
        )
    if not plan:
        plan.append(
            PlannedExperiment(
                id="E1",
                hypothesis_id="",
                objective=f"Improve {contract.metric.name} under the frozen evaluator",
                priority=50,
                rationale="Fallback plan because no explicit hypotheses were supplied.",
            )
        )
    return plan
