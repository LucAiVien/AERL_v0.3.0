"""Small statistical verification helpers for ERA Research v0.2.

Uses standard-library statistics only. The confidence interval is a normal
approximation suitable as a lightweight diagnostic, not a replacement for a
problem-specific statistical analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import sqrt
from statistics import mean, stdev
from typing import Iterable


@dataclass(frozen=True)
class ScoreSummary:
    n: int
    mean: float
    std: float
    ci95_low: float
    ci95_high: float
    minimum: float
    maximum: float

    def to_dict(self) -> dict:
        return asdict(self)


def summarize_scores(scores: Iterable[float]) -> ScoreSummary:
    values = [float(x) for x in scores]
    if not values:
        raise ValueError("at least one score is required")
    mu = mean(values)
    sd = stdev(values) if len(values) > 1 else 0.0
    margin = 1.96 * sd / sqrt(len(values)) if len(values) > 1 else 0.0
    return ScoreSummary(
        n=len(values),
        mean=mu,
        std=sd,
        ci95_low=mu - margin,
        ci95_high=mu + margin,
        minimum=min(values),
        maximum=max(values),
    )


def directional_improvement(baseline: float, candidate: float, direction: str) -> float:
    if direction == "maximize":
        return float(candidate) - float(baseline)
    if direction == "minimize":
        return float(baseline) - float(candidate)
    raise ValueError("direction must be maximize or minimize")
