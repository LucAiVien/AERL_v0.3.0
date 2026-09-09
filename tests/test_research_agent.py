import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ablation import run_ablations
from contracts import EvaluationContract, Evidence, Hypothesis, MetricSpec
from research_agent import ERAResearchAgent, ResearchAgentConfig
from research_memory import ResearchMemory
from verification_stats import directional_improvement, summarize_scores


@dataclass(frozen=True)
class Candidate:
    x: int


class ContractAndStatisticsTests(unittest.TestCase):
    def test_contract_validation(self):
        contract = EvaluationContract(
            problem="minimize fixture",
            candidate_interface="Candidate(x)",
            metric=MetricSpec("loss", "minimize"),
            evaluator_id="fixture-v1",
            iterations=3,
        )
        contract.validate()

    def test_invalid_contract_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationContract(
                problem="",
                candidate_interface="Candidate(x)",
                metric=MetricSpec("loss", "minimize"),
            ).validate()

    def test_score_summary(self):
        summary = summarize_scores([1.0, 2.0, 3.0])
        self.assertEqual(summary.n, 3)
        self.assertAlmostEqual(summary.mean, 2.0)
        self.assertGreater(summary.ci95_high, summary.mean)
        self.assertLess(summary.ci95_low, summary.mean)

    def test_directional_improvement(self):
        self.assertEqual(directional_improvement(1, 3, "maximize"), 2)
        self.assertEqual(directional_improvement(3, 1, "minimize"), 2)


class MemoryAndAblationTests(unittest.TestCase):
    def test_memory_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            memory = ResearchMemory(Path(td) / "m.jsonl")
            memory.append("hypothesis", {"id": "H1"})
            memory.append("experiment", {"score": 1.2})
            self.assertEqual(len(memory.read_all()), 2)
            self.assertEqual(len(memory.by_type("experiment")), 1)

    def test_ablation_direction(self):
        results = run_ablations(
            best_candidate=3,
            best_score=0,
            variants=[("minus-one", 2), ("plus-one", 4)],
            evaluate_fn=lambda x: float((x - 3) ** 2),
            direction="minimize",
        )
        self.assertEqual([r.score for r in results], [1.0, 1.0])
        self.assertEqual([r.delta_from_best for r in results], [-1.0, -1.0])


class FullAgentTests(unittest.TestCase):
    def test_full_lifecycle(self):
        proposals = [Candidate(3), Candidate(6), Candidate(8), Candidate(7)]

        def evaluate(c):
            return float((c.x - 7) ** 2)

        def literature(contract):
            return [Evidence("literature", "Search around x=7", "fixture")]

        def hypotheses(contract, priors):
            return [Hypothesis("H1", "Move x toward 7", "Known synthetic basin")]

        def generate(parent, score, iteration, priors, hypotheses):
            return proposals[iteration]

        def ablate(best, hypotheses):
            return [("shift-left", Candidate(best.x - 1))]

        contract = EvaluationContract(
            problem="recover x=7",
            candidate_interface="Candidate(x)",
            metric=MetricSpec("loss", "minimize"),
            evaluator_id="fixture-v1",
            iterations=len(proposals),
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "memory.jsonl"
            agent = ERAResearchAgent(
                contract=contract,
                evaluate_fn=evaluate,
                generate_fn=generate,
                literature_fn=literature,
                hypothesis_fn=hypotheses,
                ablation_fn=ablate,
                memory_path=path,
                config=ResearchAgentConfig(verification_repeats=2),
            )
            run, report = agent.run(Candidate(0))
            event_types = {x["event_type"] for x in ResearchMemory(path).read_all()}

        self.assertEqual(run.best_candidate, Candidate(7))
        self.assertEqual(run.best_score, 0.0)
        self.assertEqual(run.verification_scores, [0.0, 0.0])
        self.assertEqual(run.ablations[0]["score"], 1.0)
        self.assertIn("verification", event_types)
        self.assertIn("ablation", event_types)
        self.assertIn("report", event_types)
        self.assertIn("# ERA Research Report", report)
        self.assertIn("## Literature / prior evidence", report)
        self.assertIn("## Hypotheses", report)
        self.assertIn("## Experiment ledger", report)


if __name__ == "__main__":
    unittest.main()
