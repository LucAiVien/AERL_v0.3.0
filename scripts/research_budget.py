"""Explicit autonomy/evaluation budget accounting for Automousera Research v0.3."""

from __future__ import annotations

from dataclasses import dataclass


class BudgetExhausted(RuntimeError):
    pass


@dataclass
class ResearchBudget:
    max_evaluations: int | None = None
    max_critic_rounds: int = 2
    evaluations_used: int = 0
    critic_rounds_used: int = 0

    def validate(self) -> None:
        if self.max_evaluations is not None and self.max_evaluations < 1:
            raise ValueError("max_evaluations must be >= 1")
        if self.max_critic_rounds < 0:
            raise ValueError("max_critic_rounds must be >= 0")

    @property
    def evaluations_remaining(self) -> int | None:
        if self.max_evaluations is None:
            return None
        return max(0, self.max_evaluations - self.evaluations_used)

    def consume_evaluation(self, n: int = 1) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        if self.max_evaluations is not None and self.evaluations_used + n > self.max_evaluations:
            raise BudgetExhausted("evaluation budget exhausted")
        self.evaluations_used += n

    def consume_critic_round(self) -> None:
        if self.critic_rounds_used >= self.max_critic_rounds:
            raise BudgetExhausted("critic-round budget exhausted")
        self.critic_rounds_used += 1

    def to_dict(self) -> dict[str, int | None]:
        return {
            "max_evaluations": self.max_evaluations,
            "evaluations_used": self.evaluations_used,
            "evaluations_remaining": self.evaluations_remaining,
            "max_critic_rounds": self.max_critic_rounds,
            "critic_rounds_used": self.critic_rounds_used,
        }
