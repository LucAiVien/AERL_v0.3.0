"""ERA-style empirical search engine.

Independent implementation inspired by the Flat UCB/PUCT search published with
Google Research ERA. No Google source file is vendored.

The engine does not execute code itself. Callers provide generation and frozen
evaluation functions. Generated code must only be run by an appropriately
isolated runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import sqrt
from typing import Any, Callable, Generic, Literal, TypeVar

T = TypeVar("T")
Direction = Literal["maximize", "minimize"]


@dataclass(frozen=True)
class CandidateProposal(Generic[T]):
    candidate: T
    hypothesis_id: str = ""
    change_summary: str = ""


@dataclass(frozen=True)
class EvaluationOutcome:
    score: float
    metrics: dict[str, float] = field(default_factory=dict)
    diagnostics: str = ""
    status: str = "ok"


@dataclass
class SearchNode(Generic[T]):
    index: int
    parent_index: int | None
    candidate: T
    raw_score: float
    utility: float
    visits: int = 0
    rank_score: float = 0.5
    selection_score: float = 0.5
    status: str = "ok"
    hypothesis_id: str = ""
    change_summary: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    diagnostics: str = ""


@dataclass
class SearchResult(Generic[T]):
    best_candidate: T
    best_score: float
    best_index: int
    nodes: list[SearchNode[T]]
    stop_reason: str = "iteration_budget"

    def ledger(self) -> list[dict[str, Any]]:
        return [asdict(node) for node in self.nodes]


def _utility(score: float, direction: Direction) -> float:
    return score if direction == "maximize" else -score


def _is_target_reached(score: float, target: float, direction: Direction) -> bool:
    return score >= target if direction == "maximize" else score <= target


def _update_rank_scores(nodes: list[SearchNode[T]]) -> None:
    if len(nodes) == 1:
        nodes[0].rank_score = 0.5
        return
    ranked = sorted(nodes, key=lambda n: n.utility)
    denominator = len(ranked) - 1
    for rank, node in enumerate(ranked):
        node.rank_score = rank / denominator


def _update_selection_scores(nodes: list[SearchNode[T]], c_puct: float) -> None:
    prior = 1.0 / len(nodes)
    total_visits = sum(node.visits for node in nodes)
    exploration_base = sqrt(total_visits)
    for node in nodes:
        explore = c_puct * prior * exploration_base / (1 + node.visits)
        node.selection_score = node.rank_score + explore


def _backpropagate_visit(nodes: list[SearchNode[T]], node_index: int) -> None:
    current = node_index
    while current is not None:
        node = nodes[current]
        node.visits += 1
        current = node.parent_index


def _unwrap_proposal(value: T | CandidateProposal[T]) -> tuple[T, str, str]:
    if isinstance(value, CandidateProposal):
        return value.candidate, value.hypothesis_id, value.change_summary
    return value, "", ""


def _unwrap_evaluation(value: float | EvaluationOutcome) -> EvaluationOutcome:
    if isinstance(value, EvaluationOutcome):
        return EvaluationOutcome(
            score=float(value.score),
            metrics={k: float(v) for k, v in value.metrics.items()},
            diagnostics=value.diagnostics,
            status=value.status,
        )
    return EvaluationOutcome(score=float(value))


def flat_ucb_search(
    *,
    initial_candidate: T,
    initial_score: float,
    generate_fn: Callable[[T, float, int], T | CandidateProposal[T]],
    evaluate_fn: Callable[[T], float | EvaluationOutcome],
    iterations: int,
    direction: Direction = "maximize",
    c_puct: float = 1.0,
    failure_score: float | None = None,
    target_score: float | None = None,
    patience: int | None = None,
    initial_metrics: dict[str, float] | None = None,
) -> SearchResult[T]:
    """Search over complete candidates with a Flat-UCB/PUCT-style policy.

    Backwards compatible with simple float evaluators and raw candidates. Rich
    callers may return CandidateProposal and EvaluationOutcome to preserve
    hypothesis/change metadata, component metrics, and diagnostics.
    """
    if iterations < 0:
        raise ValueError("iterations must be >= 0")
    if c_puct < 0:
        raise ValueError("c_puct must be >= 0")
    if direction not in ("maximize", "minimize"):
        raise ValueError("direction must be 'maximize' or 'minimize'")
    if patience is not None and patience <= 0:
        raise ValueError("patience must be positive")

    nodes: list[SearchNode[T]] = [
        SearchNode(
            index=0,
            parent_index=None,
            candidate=initial_candidate,
            raw_score=float(initial_score),
            utility=_utility(float(initial_score), direction),
            metrics=dict(initial_metrics or {}),
            change_summary="baseline",
        )
    ]

    best_utility = nodes[0].utility
    no_improvement = 0
    if target_score is not None and _is_target_reached(float(initial_score), target_score, direction):
        return SearchResult(initial_candidate, float(initial_score), 0, nodes, "target_reached")

    stop_reason = "iteration_budget"
    for iteration in range(iterations):
        _update_rank_scores(nodes)
        _update_selection_scores(nodes, c_puct)
        parent = max(nodes, key=lambda n: (n.selection_score, n.utility, -n.index))
        proposal = generate_fn(parent.candidate, parent.raw_score, iteration)
        candidate, hypothesis_id, change_summary = _unwrap_proposal(proposal)

        try:
            outcome = _unwrap_evaluation(evaluate_fn(candidate))
        except Exception as exc:
            if failure_score is None:
                raise
            outcome = EvaluationOutcome(
                score=float(failure_score),
                status="failed",
                diagnostics=f"{type(exc).__name__}: {exc}",
            )

        child = SearchNode(
            index=len(nodes),
            parent_index=parent.index,
            candidate=candidate,
            raw_score=outcome.score,
            utility=_utility(outcome.score, direction),
            status=outcome.status,
            hypothesis_id=hypothesis_id,
            change_summary=change_summary,
            metrics=outcome.metrics,
            diagnostics=outcome.diagnostics,
        )
        nodes.append(child)
        _backpropagate_visit(nodes, child.index)

        if child.utility > best_utility:
            best_utility = child.utility
            no_improvement = 0
        else:
            no_improvement += 1

        current_best = max(nodes, key=lambda n: (n.utility, -n.index))
        if target_score is not None and _is_target_reached(current_best.raw_score, target_score, direction):
            stop_reason = "target_reached"
            break
        if patience is not None and no_improvement >= patience:
            stop_reason = "patience_exhausted"
            break

    best = max(nodes, key=lambda n: (n.utility, -n.index))
    return SearchResult(
        best_candidate=best.candidate,
        best_score=best.raw_score,
        best_index=best.index,
        nodes=nodes,
        stop_reason=stop_reason,
    )
