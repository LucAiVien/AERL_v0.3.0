"""Multi-agent autonomous-scientist orchestrator for Automousera Research v0.3.

The host injects actual literature/model/evaluator capabilities. This module
coordinates explicit agent roles, keeps a shared blackboard, runs ERA/FUTS,
invokes an independent critic loop, verifies the accepted winner, performs
ablations, and renders a research report. It never treats arbitrary local code
execution as a secure sandbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, Iterable, TypeVar

from ablation import run_ablations
from agent_protocol import AgentTask, ReviewDecision
from contracts import AutonomousResearchRun, EvaluationContract, Evidence, Hypothesis
from era_engine import CandidateProposal, EvaluationOutcome, flat_ucb_search
from experiment_planner import PlannedExperiment, default_plan
from reporting import build_autonomous_markdown_report
from research_budget import BudgetExhausted, ResearchBudget
from team_blackboard import TeamBlackboard

T = TypeVar("T")


@dataclass(frozen=True)
class AutomouseraConfig:
    c_puct: float = 1.0
    failure_score: float | None = None
    verification_repeats: int = 3
    max_critic_rounds: int = 2
    max_total_evaluations: int | None = None
    require_critic_acceptance: bool = True

    def validate(self) -> None:
        if self.c_puct < 0:
            raise ValueError("c_puct must be >= 0")
        if self.verification_repeats < 1:
            raise ValueError("verification_repeats must be >= 1")
        if self.max_critic_rounds < 0:
            raise ValueError("max_critic_rounds must be >= 0")
        if self.max_total_evaluations is not None and self.max_total_evaluations < 1:
            raise ValueError("max_total_evaluations must be >= 1")


class AutomouseraResearchAgent(Generic[T]):
    """Coordinate a team of research agents around a frozen empirical evaluator."""

    def __init__(
        self,
        *,
        contract: EvaluationContract,
        evaluate_fn: Callable[[T], float | EvaluationOutcome],
        generate_fn: Callable[[T, float, int, list[Evidence], list[Hypothesis], list[PlannedExperiment]], T | CandidateProposal[T]],
        literature_fn: Callable[[EvaluationContract], Iterable[Evidence]] | None = None,
        hypothesis_fn: Callable[[EvaluationContract, list[Evidence]], Iterable[Hypothesis]] | None = None,
        planner_fn: Callable[[EvaluationContract, list[Evidence], list[Hypothesis]], Iterable[PlannedExperiment]] | None = None,
        critic_fn: Callable[[T, float, EvaluationContract, list[dict], list[Evidence], list[Hypothesis], int], ReviewDecision] | None = None,
        revise_fn: Callable[[T, float, ReviewDecision, int, list[Evidence], list[Hypothesis]], T | CandidateProposal[T]] | None = None,
        ablation_fn: Callable[[T, list[Hypothesis]], Iterable[tuple[str, T]]] | None = None,
        blackboard_path: str | Path | None = None,
        run_id: str = "run-1",
        config: AutomouseraConfig | None = None,
    ):
        contract.validate()
        self.contract = contract
        self.evaluate_fn = evaluate_fn
        self.generate_fn = generate_fn
        self.literature_fn = literature_fn
        self.hypothesis_fn = hypothesis_fn
        self.planner_fn = planner_fn or default_plan
        self.critic_fn = critic_fn
        self.revise_fn = revise_fn
        self.ablation_fn = ablation_fn
        self.config = config or AutomouseraConfig()
        self.config.validate()
        self.budget = ResearchBudget(
            max_evaluations=self.config.max_total_evaluations,
            max_critic_rounds=self.config.max_critic_rounds,
        )
        self.budget.validate()
        self.blackboard = TeamBlackboard(blackboard_path, run_id=run_id) if blackboard_path else None
        self._trace: list[dict] = []

    def _event(self, agent: str, event_type: str, payload) -> None:
        row = {"agent": agent, "event_type": event_type, "payload": payload}
        self._trace.append(row)
        if self.blackboard is not None:
            self.blackboard.append(agent=agent, event_type=event_type, payload=payload)

    def _task(self, task_id: str, agent: str, objective: str, requested_outputs: tuple[str, ...] = ()) -> AgentTask:
        task = AgentTask(task_id, agent, objective, requested_outputs=requested_outputs)  # type: ignore[arg-type]
        task.validate()
        self._event("orchestrator", "task_assigned", task)
        return task

    def _evaluate(self, candidate: T) -> EvaluationOutcome:
        self.budget.consume_evaluation()
        value = self.evaluate_fn(candidate)
        if isinstance(value, EvaluationOutcome):
            return EvaluationOutcome(
                score=float(value.score),
                metrics={k: float(v) for k, v in value.metrics.items()},
                diagnostics=value.diagnostics,
                status=value.status,
            )
        return EvaluationOutcome(score=float(value))

    def _better(self, score_a: float, score_b: float) -> bool:
        if self.contract.metric.direction == "maximize":
            return score_a > score_b
        return score_a < score_b

    def _default_review(self, candidate: T, score: float, round_index: int) -> ReviewDecision:
        return ReviewDecision(
            verdict="accept",
            rationale="No external critic was supplied; structural checks passed.",
            confidence=0.5,
        )

    def run(self, seed_candidate: T) -> tuple[AutonomousResearchRun[T], str]:
        self._event("orchestrator", "evaluation_contract_frozen", self.contract)

        self._task("T-LIT", "literature-scout", "Collect actionable research priors", ("evidence",))
        priors = list(self.literature_fn(self.contract)) if self.literature_fn else []
        self._event("literature-scout", "literature_priors", priors)

        self._task("T-HYP", "hypothesis-scientist", "Form diverse falsifiable hypotheses", ("hypotheses",))
        hypotheses = list(self.hypothesis_fn(self.contract, priors)) if self.hypothesis_fn else []
        self._event("hypothesis-scientist", "hypotheses", hypotheses)

        self._task("T-PLAN", "experiment-planner", "Build a hypothesis-driven experiment queue", ("plan",))
        plan = list(self.planner_fn(self.contract, priors, hypotheses))
        self._event("experiment-planner", "experiment_plan", [x.to_dict() for x in plan])

        self._task("T-BASE", "era-search-worker", "Measure the real baseline", ("baseline",))
        seed_outcome = self._evaluate(seed_candidate)
        seed_score = seed_outcome.score
        self._event(
            "era-search-worker",
            "baseline",
            {"candidate": seed_candidate, "score": seed_score, "metrics": seed_outcome.metrics, "diagnostics": seed_outcome.diagnostics},
        )

        # Reserve verification budget when a hard evaluation cap exists.
        search_iterations = self.contract.iterations
        remaining = self.budget.evaluations_remaining
        if remaining is not None:
            reserve = self.config.verification_repeats
            search_iterations = max(0, min(search_iterations, max(0, remaining - reserve)))

        def generate_adapter(parent: T, score: float, iteration: int):
            return self.generate_fn(parent, score, iteration, priors, hypotheses, plan)

        self._task("T-SEARCH", "era-search-worker", "Run ERA/FUTS empirical search", ("search_ledger", "winner"))
        search_result = flat_ucb_search(
            initial_candidate=seed_candidate,
            initial_score=seed_score,
            generate_fn=generate_adapter,
            evaluate_fn=self._evaluate,
            iterations=search_iterations,
            direction=self.contract.metric.direction,
            c_puct=self.config.c_puct,
            failure_score=self.config.failure_score,
            target_score=self.contract.target_score,
            patience=self.contract.patience,
            initial_metrics=seed_outcome.metrics,
        )
        ledger = search_result.ledger()
        self._event("era-search-worker", "search_ledger", ledger)
        self._event("era-search-worker", "search_stop", {"reason": search_result.stop_reason})
        best_candidate = search_result.best_candidate
        best_score = search_result.best_score

        # Independent critic can force targeted follow-up experiments.
        review_history: list[dict] = []
        accepted = False
        critic_stop_reason = "critic_not_run"
        self._task("T-CRITIC", "critic-reviewer", "Challenge winner, detect leakage/weak evidence, and request decisive follow-ups", ("review_decision",))
        critic_round = 0
        while True:
            if critic_round >= self.config.max_critic_rounds and self.config.max_critic_rounds > 0:
                critic_stop_reason = "critic_round_budget"
                break
            if self.config.max_critic_rounds == 0:
                decision = self._default_review(best_candidate, best_score, critic_round)
            else:
                self.budget.consume_critic_round()
                decision = (
                    self.critic_fn(best_candidate, best_score, self.contract, ledger, priors, hypotheses, critic_round)
                    if self.critic_fn
                    else self._default_review(best_candidate, best_score, critic_round)
                )
            decision.validate()
            review_history.append(decision.to_dict())
            self._event("critic-reviewer", "review_decision", decision)

            if decision.verdict == "accept":
                accepted = True
                critic_stop_reason = "accepted"
                break
            if decision.verdict == "reject":
                critic_stop_reason = "rejected"
                break
            if self.revise_fn is None:
                critic_stop_reason = "revision_unavailable"
                break

            try:
                proposal = self.revise_fn(best_candidate, best_score, decision, critic_round, priors, hypotheses)
                if isinstance(proposal, CandidateProposal):
                    revised_candidate = proposal.candidate
                    hyp_id = proposal.hypothesis_id
                    change_summary = proposal.change_summary
                else:
                    revised_candidate = proposal
                    hyp_id = ""
                    change_summary = "; ".join(decision.requested_experiments)
                revised_outcome = self._evaluate(revised_candidate)
            except BudgetExhausted:
                critic_stop_reason = "evaluation_budget"
                break

            followup_row = {
                "index": len(ledger),
                "parent_index": search_result.best_index,
                "candidate": revised_candidate,
                "raw_score": revised_outcome.score,
                "utility": revised_outcome.score if self.contract.metric.direction == "maximize" else -revised_outcome.score,
                "visits": 0,
                "rank_score": 0.0,
                "selection_score": 0.0,
                "status": revised_outcome.status,
                "hypothesis_id": hyp_id,
                "change_summary": f"critic-followup: {change_summary}",
                "metrics": revised_outcome.metrics,
                "diagnostics": revised_outcome.diagnostics,
            }
            ledger.append(followup_row)
            self._event("era-search-worker", "critic_followup_experiment", followup_row)
            if self._better(revised_outcome.score, best_score):
                best_candidate = revised_candidate
                best_score = revised_outcome.score
            critic_round += 1

        # Verification is only meaningful for a non-rejected candidate; it can
        # still run when critic acceptance is optional/unavailable.
        verification_scores: list[float] = []
        should_verify = critic_stop_reason != "rejected" and (accepted or not self.config.require_critic_acceptance)
        if should_verify:
            self._task("T-VERIFY", "statistical-verifier", "Rebuild/rerun the selected winner independently", ("verification_scores",))
            for _ in range(self.config.verification_repeats):
                try:
                    verification_scores.append(self._evaluate(best_candidate).score)
                except BudgetExhausted:
                    break
            self._event("statistical-verifier", "verification", {"candidate": best_candidate, "scores": verification_scores})

        ablations: list[dict] = []
        if self.ablation_fn and should_verify:
            self._task("T-ABLATE", "ablation-analyst", "Isolate which winner components caused the gain", ("ablations",))
            variants = list(self.ablation_fn(best_candidate, hypotheses))
            # Respect remaining budget by truncating variants deterministically.
            remaining = self.budget.evaluations_remaining
            if remaining is not None:
                variants = variants[:remaining]
            ablations = [
                x.to_dict()
                for x in run_ablations(
                    best_candidate=best_candidate,
                    best_score=best_score,
                    variants=variants,
                    evaluate_fn=self._evaluate,
                    direction=self.contract.metric.direction,
                    failure_score=self.config.failure_score,
                )
            ]
            self._event("ablation-analyst", "ablations", ablations)

        if critic_stop_reason == "rejected":
            final_status = "rejected_by_critic"
        elif self.config.require_critic_acceptance and not accepted:
            final_status = "needs_review"
        elif verification_scores and all(abs(x - best_score) <= 1e-12 for x in verification_scores):
            final_status = "verified"
        elif verification_scores:
            final_status = "verified_with_variance"
        else:
            final_status = "candidate_unverified"

        run = AutonomousResearchRun(
            contract=self.contract,
            seed_candidate=seed_candidate,
            seed_score=seed_score,
            priors=priors,
            hypotheses=hypotheses,
            search_ledger=ledger,
            best_candidate=best_candidate,
            best_score=best_score,
            verification_scores=verification_scores,
            ablations=ablations,
            plan=[x.to_dict() for x in plan],
            review_history=review_history,
            agent_trace=list(self._trace),
            final_status=final_status,
            stop_reason=critic_stop_reason,
            budget=self.budget.to_dict(),
            accepted_by_critic=accepted,
        )
        self._task("T-REPORT", "reporter", "Synthesize evidence, objections, verification, limitations, and next actions", ("markdown_report",))
        # Keep the report task in the final trace too.
        run.agent_trace = list(self._trace)
        report = build_autonomous_markdown_report(run)
        self._event("reporter", "report", {"markdown": report})
        run.agent_trace = list(self._trace)
        return run, report
