"""Deterministic end-to-end test of the ERA Research v0.2 orchestration.

Safe by construction: the candidate is a small declarative tuple, not code.
The scientific objective is a synthetic response surface with known optimum.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from contracts import EvaluationContract, Evidence, Hypothesis, MetricSpec
from research_agent import ERAResearchAgent, ResearchAgentConfig
from era_engine import CandidateProposal
from research_memory import ResearchMemory


@dataclass(frozen=True)
class Candidate:
    x: int
    regularizer: int = 0


def evaluate(c: Candidate) -> float:
    # Minimum at x=7, regularizer=1.
    return float((c.x - 7) ** 2 + (c.regularizer - 1) ** 2)


def literature(contract):
    return [
        Evidence("literature", "Search near the response-surface basin before fine tuning.", "synthetic prior"),
        Evidence("diagnostic", "Regularization may reduce the auxiliary penalty.", "task definition"),
    ]


def hypotheses(contract, priors):
    return [
        Hypothesis("H1", "Move x toward 7", "The dominant squared-error term is centered at x=7."),
        Hypothesis("H2", "Set regularizer to 1", "The auxiliary penalty is minimized at one."),
    ]


PROPOSALS = [
    Candidate(2, 0),
    Candidate(10, 1),
    Candidate(6, 0),
    Candidate(8, 1),
    Candidate(7, 0),
    Candidate(7, 1),
]


def generate(parent, parent_score, iteration, priors, hypotheses):
    hypothesis_id = "H2" if PROPOSALS[iteration].regularizer == 1 else "H1"
    return CandidateProposal(PROPOSALS[iteration], hypothesis_id, f"try proposal {iteration + 1}")


def ablate(best, hypotheses):
    return [
        ("remove-regularizer", Candidate(best.x, 0)),
        ("shift-x-minus-1", Candidate(best.x - 1, best.regularizer)),
    ]


def main() -> None:
    contract = EvaluationContract(
        problem="Find the minimum of a synthetic empirical response surface.",
        candidate_interface="Candidate(x:int, regularizer:int)",
        metric=MetricSpec("synthetic loss", "minimize"),
        inputs=("deterministic fixture",),
        evaluator_id="synthetic-v1",
        iterations=len(PROPOSALS),
    )
    with tempfile.TemporaryDirectory() as td:
        memory_path = Path(td) / "research.jsonl"
        agent = ERAResearchAgent(
            contract=contract,
            evaluate_fn=evaluate,
            generate_fn=generate,
            literature_fn=literature,
            hypothesis_fn=hypotheses,
            ablation_fn=ablate,
            memory_path=memory_path,
            config=ResearchAgentConfig(verification_repeats=3),
        )
        run, report = agent.run(Candidate(0, 0))
        events = ResearchMemory(memory_path).read_all()

    print("ERA-RESEARCH v0.2 FULL AGENT TEST")
    print(f"baseline={run.seed_score:.1f}")
    print(f"best={run.best_candidate} score={run.best_score:.1f}")
    print(f"verification={run.verification_scores}")
    print(f"ablations={[(a['label'], a['score']) for a in run.ablations]}")
    print(f"memory_events={len(events)}")
    if run.best_candidate != Candidate(7, 1) or run.best_score != 0.0:
        raise SystemExit("FAIL: full agent did not recover the optimum")
    if len(run.verification_scores) != 3 or any(x != 0.0 for x in run.verification_scores):
        raise SystemExit("FAIL: verification did not reproduce the winner")
    required_events = {"evaluation_contract", "evidence", "hypothesis", "baseline", "experiment", "verification", "ablation", "report"}
    if not required_events.issubset({e['event_type'] for e in events}):
        raise SystemExit("FAIL: research memory is missing required event types")
    if "## Ablations" not in report or "## Verification" not in report:
        raise SystemExit("FAIL: report is missing full-agent sections")
    print("PASS: framing -> priors -> hypotheses -> ERA search -> verification -> ablation -> memory -> report")


if __name__ == "__main__":
    main()
