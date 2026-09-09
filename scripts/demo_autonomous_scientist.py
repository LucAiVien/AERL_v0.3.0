"""Deterministic end-to-end demo for Automousera Research v0.3.

Safe by construction: candidates are declarative dataclasses, never generated
Python. The critic deliberately rejects the first winner and requests a focused
follow-up that reaches the known optimum.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from agent_protocol import ReviewDecision
from autonomous_agent import AutomouseraConfig, AutomouseraResearchAgent
from contracts import EvaluationContract, Evidence, Hypothesis, MetricSpec
from era_engine import CandidateProposal
from team_blackboard import TeamBlackboard


@dataclass(frozen=True)
class Candidate:
    x: int
    regularizer: int = 0


def evaluate(c: Candidate) -> float:
    return float((c.x - 7) ** 2 + (c.regularizer - 1) ** 2)


def literature(contract):
    return [Evidence("literature", "Search near x=7; regularization can reduce the auxiliary penalty.", "synthetic fixture")]


def hypotheses(contract, priors):
    return [
        Hypothesis("H1", "Move x toward 7", "Main squared-error basin is centered at seven.", falsification_test="Try symmetric offsets."),
        Hypothesis("H2", "Set regularizer to 1", "Auxiliary penalty is minimized at one.", falsification_test="Ablate regularizer."),
    ]


PROPOSALS = [Candidate(3, 0), Candidate(6, 0), Candidate(8, 0), Candidate(7, 0)]


def generate(parent, parent_score, iteration, priors, hypotheses, plan):
    return CandidateProposal(PROPOSALS[iteration], "H1", f"search proposal {iteration + 1}")


def critic(candidate, score, contract, ledger, priors, hypotheses, round_index):
    if candidate.regularizer != 1:
        return ReviewDecision(
            "revise",
            "The search improved x but did not test the explicit regularizer hypothesis.",
            concerns=("H2 remains untested in the winner",),
            requested_experiments=("set regularizer=1 while holding x fixed",),
            confidence=0.95,
        )
    return ReviewDecision("accept", "The targeted follow-up resolves the critic concern.", confidence=0.98)


def revise(candidate, score, decision, round_index, priors, hypotheses):
    return CandidateProposal(Candidate(candidate.x, 1), "H2", "critic requested regularizer=1")


def ablate(best, hypotheses):
    return [
        ("remove-regularizer", Candidate(best.x, 0)),
        ("shift-x-minus-1", Candidate(best.x - 1, best.regularizer)),
    ]


def main() -> None:
    contract = EvaluationContract(
        problem="Recover the known optimum of a synthetic response surface.",
        candidate_interface="Candidate(x:int, regularizer:int)",
        metric=MetricSpec("loss", "minimize"),
        evaluator_id="synthetic-v3",
        iterations=len(PROPOSALS),
        validation_protocol="deterministic fixture",
    )
    with tempfile.TemporaryDirectory() as td:
        blackboard_path = Path(td) / "blackboard.jsonl"
        agent = AutomouseraResearchAgent(
            contract=contract,
            evaluate_fn=evaluate,
            generate_fn=generate,
            literature_fn=literature,
            hypothesis_fn=hypotheses,
            critic_fn=critic,
            revise_fn=revise,
            ablation_fn=ablate,
            blackboard_path=blackboard_path,
            config=AutomouseraConfig(verification_repeats=3, max_critic_rounds=2, max_total_evaluations=20),
        )
        run, report = agent.run(Candidate(0, 0))
        events = TeamBlackboard(blackboard_path).read_all()

    print("AUTOMOUSERA-RESEARCH v0.3 AUTONOMOUS SCIENTIST TEST")
    print(f"baseline={run.seed_score:.1f}")
    print(f"best={run.best_candidate} score={run.best_score:.1f}")
    print(f"reviews={[x['verdict'] for x in run.review_history]}")
    print(f"verification={run.verification_scores}")
    print(f"status={run.final_status} budget={run.budget}")
    print(f"blackboard_events={len(events)}")
    if run.best_candidate != Candidate(7, 1) or run.best_score != 0.0:
        raise SystemExit("FAIL: critic-guided follow-up did not recover optimum")
    if [x["verdict"] for x in run.review_history] != ["revise", "accept"]:
        raise SystemExit("FAIL: expected revise -> accept critic loop")
    if run.final_status != "verified":
        raise SystemExit("FAIL: winner was not verified")
    if "## Critic / reviewer loop" not in report or "## Agent trace / provenance" not in report:
        raise SystemExit("FAIL: autonomous report sections missing")
    print("PASS: multi-agent plan -> ERA search -> critic revision -> verification -> ablation -> report")


if __name__ == "__main__":
    main()
