"""Ablation utilities for ERA Research v0.2."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Generic, Iterable, TypeVar

from era_engine import EvaluationOutcome

T = TypeVar("T")


@dataclass(frozen=True)
class AblationResult(Generic[T]):
    label: str
    candidate: T
    score: float
    delta_from_best: float
    status: str = "ok"

    def to_dict(self) -> dict:
        return asdict(self)


def run_ablations(
    *,
    best_candidate: T,
    best_score: float,
    variants: Iterable[tuple[str, T]],
    evaluate_fn: Callable[[T], float | EvaluationOutcome],
    direction: str,
    failure_score: float | None = None,
) -> list[AblationResult[T]]:
    results: list[AblationResult[T]] = []
    for label, candidate in variants:
        status = "ok"
        try:
            value = evaluate_fn(candidate)
            score = float(value.score if isinstance(value, EvaluationOutcome) else value)
        except Exception:
            if failure_score is None:
                raise
            score = float(failure_score)
            status = "failed"
        if direction == "maximize":
            delta = score - best_score
        elif direction == "minimize":
            delta = best_score - score
        else:
            raise ValueError("direction must be maximize or minimize")
        results.append(AblationResult(label, candidate, score, delta, status))
    return results
