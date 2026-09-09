"""Full research-agent orchestration for ERA Research v0.2.

The orchestrator composes literature priors, explicit hypotheses, ERA/FUTS
search, append-only research memory, clean-rerun verification, ablation, and
report generation. It never executes arbitrary code by itself; the caller owns
the evaluator/runtime and must enforce isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, Iterable, TypeVar

from ablation import run_ablations
from contracts import EvaluationContract, Evidence, Hypothesis, ResearchRun
from era_engine import EvaluationOutcome, flat_ucb_search
from reporting import build_markdown_report
from research_memory import ResearchMemory

T = TypeVar("T")


@dataclass(frozen=True)
class ResearchAgentConfig:
    c_puct: float = 1.0
    failure_score: float | None = None
    verification_repeats: int = 3

    def validate(self) -> None:
        if self.c_puct < 0:
            raise ValueError("c_puct must be >= 0")
        if self.verification_repeats < 1:
            raise ValueError("verification_repeats must be >= 1")


class ERAResearchAgent(Generic[T]):
    def __init__(
        self,
        *,
        contract: EvaluationContract,
        evaluate_fn: Callable[[T], float | EvaluationOutcome],
        generate_fn: Callable[[T, float, int, list[Evidence], list[Hypothesis]], T],
        literature_fn: Callable[[EvaluationContract], Iterable[Evidence]] | None = None,
        hypothesis_fn: Callable[[EvaluationContract, list[Evidence]], Iterable[Hypothesis]] | None = None,
        ablation_fn: Callable[[T, list[Hypothesis]], Iterable[tuple[str, T]]] | None = None,
        memory_path: str | Path | None = None,
        config: ResearchAgentConfig | None = None,
    ):
        contract.validate()
        self.contract = contract
        self.evaluate_fn = evaluate_fn
        self.generate_fn = generate_fn
        self.literature_fn = literature_fn
        self.hypothesis_fn = hypothesis_fn
        self.ablation_fn = ablation_fn
        self.config = config or ResearchAgentConfig()
        self.config.validate()
        self.memory = ResearchMemory(memory_path) if memory_path else None

    def _remember(self, event_type: str, payload) -> None:
        if self.memory is not None:
            self.memory.append(event_type, payload)

    def run(self, seed_candidate: T) -> tuple[ResearchRun[T], str]:
        # Phase 1: frame and freeze evaluator contract.
        self._remember("evaluation_contract", self.contract)

        # Phase 2: gather actionable priors. The host may implement this with web/deep research.
        priors = list(self.literature_fn(self.contract)) if self.literature_fn else []
        for item in priors:
            self._remember("evidence", item)

        # Phase 3: produce testable hypotheses before mutation/search.
        hypotheses = list(self.hypothesis_fn(self.contract, priors)) if self.hypothesis_fn else []
        for item in hypotheses:
            self._remember("hypothesis", item)

        # Phase 4: measure the baseline. Never accept an invented baseline score.
        seed_value = self.evaluate_fn(seed_candidate)
        if isinstance(seed_value, EvaluationOutcome):
            seed_score = float(seed_value.score)
            seed_metrics = dict(seed_value.metrics)
            seed_diagnostics = seed_value.diagnostics
        else:
            seed_score = float(seed_value)
            seed_metrics = {}
            seed_diagnostics = ""
        self._remember("baseline", {"candidate": seed_candidate, "score": seed_score, "metrics": seed_metrics, "diagnostics": seed_diagnostics})

        def generate_adapter(parent: T, score: float, iteration: int) -> T:
            return self.generate_fn(parent, score, iteration, priors, hypotheses)

        # Phase 5: ERA/FUTS empirical search.
        result = flat_ucb_search(
            initial_candidate=seed_candidate,
            initial_score=seed_score,
            generate_fn=generate_adapter,
            evaluate_fn=self.evaluate_fn,
            iterations=self.contract.iterations,
            direction=self.contract.metric.direction,
            c_puct=self.config.c_puct,
            failure_score=self.config.failure_score,
            target_score=self.contract.target_score,
            patience=self.contract.patience,
            initial_metrics=seed_metrics,
        )
        for row in result.ledger():
            self._remember("experiment", row)
        self._remember("search_stop", {"reason": result.stop_reason})

        # Phase 6: clean rerun verification of the selected winner.
        verification_scores = []
        for _ in range(self.config.verification_repeats):
            value = self.evaluate_fn(result.best_candidate)
            verification_scores.append(float(value.score if isinstance(value, EvaluationOutcome) else value))
        self._remember(
            "verification",
            {"candidate": result.best_candidate, "scores": verification_scores},
        )

        # Phase 7: targeted ablations proposed by the domain adapter.
        ablations = []
        if self.ablation_fn:
            variants = list(self.ablation_fn(result.best_candidate, hypotheses))
            ablations = [
                x.to_dict()
                for x in run_ablations(
                    best_candidate=result.best_candidate,
                    best_score=result.best_score,
                    variants=variants,
                    evaluate_fn=self.evaluate_fn,
                    direction=self.contract.metric.direction,
                    failure_score=self.config.failure_score,
                )
            ]
            for row in ablations:
                self._remember("ablation", row)

        run = ResearchRun(
            contract=self.contract,
            seed_candidate=seed_candidate,
            seed_score=seed_score,
            priors=priors,
            hypotheses=hypotheses,
            search_ledger=result.ledger(),
            best_candidate=result.best_candidate,
            best_score=result.best_score,
            verification_scores=verification_scores,
            ablations=ablations,
        )
        report = build_markdown_report(run)
        self._remember("report", {"markdown": report})
        return run, report
