import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_protocol import AgentArtifact, AgentTask, ReviewDecision
from autonomous_agent import AutomouseraConfig, AutomouseraResearchAgent
from contracts import EvaluationContract, Evidence, Hypothesis, MetricSpec
from era_engine import CandidateProposal
from research_budget import BudgetExhausted, ResearchBudget
from team_blackboard import TeamBlackboard


@dataclass(frozen=True)
class Candidate:
    x: int
    reg: int = 0


def contract(iterations=4):
    return EvaluationContract(
        problem="synthetic",
        candidate_interface="Candidate",
        metric=MetricSpec("loss", "minimize"),
        evaluator_id="fixture-v3",
        iterations=iterations,
        validation_protocol="fixed fixture",
    )


class ProtocolTests(unittest.TestCase):
    def test_task_and_artifact_validate(self):
        AgentTask("T1", "literature-scout", "find priors").validate()
        AgentArtifact("A1", "T1", "literature-scout", "evidence", {"x": 1}).validate()

    def test_review_requires_experiment_on_revise(self):
        with self.assertRaises(ValueError):
            ReviewDecision("revise", "needs more", requested_experiments=()).validate()

    def test_budget_enforced(self):
        b = ResearchBudget(max_evaluations=2, max_critic_rounds=1)
        b.consume_evaluation(2)
        with self.assertRaises(BudgetExhausted):
            b.consume_evaluation()
        b.consume_critic_round()
        with self.assertRaises(BudgetExhausted):
            b.consume_critic_round()

    def test_blackboard_query_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            bb = TeamBlackboard(Path(td) / "b.jsonl", run_id="R")
            bb.append(agent="orchestrator", event_type="start", payload={})
            bb.append(agent="critic-reviewer", event_type="review", payload={"ok": True})
            self.assertEqual(len(bb.query(agent="critic-reviewer")), 1)
            cp = bb.checkpoint()
            self.assertEqual(cp["event_count"], 2)
            self.assertIn("critic-reviewer", cp["agents_seen"])


class AutonomousLifecycleTests(unittest.TestCase):
    def test_revise_then_accept_improves_winner(self):
        proposals = [Candidate(5, 0), Candidate(7, 0), Candidate(8, 0)]

        def evaluate(c):
            return float((c.x - 7) ** 2 + (c.reg - 1) ** 2)

        def literature(c):
            return [Evidence("literature", "reg=1 may help", "fixture")]

        def hypotheses(c, p):
            return [Hypothesis("H1", "x->7", "basin"), Hypothesis("H2", "reg->1", "penalty")]

        def generate(parent, score, iteration, priors, hyps, plan):
            return CandidateProposal(proposals[iteration], "H1", "move x")

        def critic(best, score, c, ledger, priors, hyps, round_index):
            if best.reg == 0:
                return ReviewDecision("revise", "H2 untested", requested_experiments=("set reg=1",), confidence=0.9)
            return ReviewDecision("accept", "concern resolved", confidence=0.9)

        def revise(best, score, decision, round_index, priors, hyps):
            return CandidateProposal(Candidate(best.x, 1), "H2", "critic follow-up")

        def ablate(best, hyps):
            return [("remove-reg", Candidate(best.x, 0))]

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bb.jsonl"
            agent = AutomouseraResearchAgent(
                contract=contract(len(proposals)),
                evaluate_fn=evaluate,
                generate_fn=generate,
                literature_fn=literature,
                hypothesis_fn=hypotheses,
                critic_fn=critic,
                revise_fn=revise,
                ablation_fn=ablate,
                blackboard_path=path,
                config=AutomouseraConfig(verification_repeats=2, max_critic_rounds=2, max_total_evaluations=12),
            )
            run, report = agent.run(Candidate(0, 0))
            events = TeamBlackboard(path).read_all()

        self.assertEqual(run.best_candidate, Candidate(7, 1))
        self.assertEqual(run.best_score, 0.0)
        self.assertEqual([x["verdict"] for x in run.review_history], ["revise", "accept"])
        self.assertTrue(run.accepted_by_critic)
        self.assertEqual(run.final_status, "verified")
        self.assertEqual(run.verification_scores, [0.0, 0.0])
        self.assertEqual(run.ablations[0]["score"], 1.0)
        self.assertTrue(any(e["event_type"] == "critic_followup_experiment" for e in events))
        self.assertIn("# Automousera Research Report", report)
        self.assertIn("## Critic / reviewer loop", report)
        self.assertIn("## Agent trace / provenance", report)

    def test_reject_blocks_verification(self):
        def critic(best, score, c, ledger, priors, hyps, round_index):
            return ReviewDecision("reject", "benchmark leakage detected", concerns=("leakage",), confidence=1.0)

        agent = AutomouseraResearchAgent(
            contract=contract(1),
            evaluate_fn=lambda c: float(c.x),
            generate_fn=lambda parent, score, i, p, h, plan: Candidate(0),
            critic_fn=critic,
            config=AutomouseraConfig(verification_repeats=2, max_critic_rounds=1),
        )
        run, _ = agent.run(Candidate(1))
        self.assertEqual(run.final_status, "rejected_by_critic")
        self.assertEqual(run.verification_scores, [])
        self.assertFalse(run.accepted_by_critic)

    def test_evaluation_budget_reserves_verification(self):
        agent = AutomouseraResearchAgent(
            contract=contract(10),
            evaluate_fn=lambda c: float(c.x),
            generate_fn=lambda parent, score, i, p, h, plan: Candidate(i),
            config=AutomouseraConfig(
                verification_repeats=2,
                max_critic_rounds=0,
                max_total_evaluations=5,
                require_critic_acceptance=False,
            ),
        )
        run, _ = agent.run(Candidate(10))
        self.assertLessEqual(run.budget["evaluations_used"], 5)
        self.assertEqual(len(run.verification_scores), 2)
        # baseline + at most two search evals + two verification = five
        self.assertLessEqual(len(run.search_ledger), 3)


if __name__ == "__main__":
    unittest.main()
