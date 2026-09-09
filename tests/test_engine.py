import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from era_engine import CandidateProposal, EvaluationOutcome, flat_ucb_search


class EngineTests(unittest.TestCase):
    def test_minimize_finds_known_optimum(self):
        target = 7
        proposals = [2, 10, 6, 8, 7]

        def evaluate(x):
            return (x - target) ** 2

        def generate(parent, score, iteration):
            return proposals[iteration]

        result = flat_ucb_search(
            initial_candidate=0,
            initial_score=evaluate(0),
            generate_fn=generate,
            evaluate_fn=evaluate,
            iterations=len(proposals),
            direction="minimize",
        )
        self.assertEqual(result.best_candidate, 7)
        self.assertEqual(result.best_score, 0.0)
        self.assertEqual(len(result.nodes), 1 + len(proposals))

    def test_maximize_direction(self):
        proposals = [1, 3, 2]

        result = flat_ucb_search(
            initial_candidate=0,
            initial_score=0,
            generate_fn=lambda parent, score, iteration: proposals[iteration],
            evaluate_fn=float,
            iterations=3,
            direction="maximize",
        )
        self.assertEqual(result.best_candidate, 3)
        self.assertEqual(result.best_score, 3.0)

    def test_failure_score_retains_failed_candidate(self):
        proposals = [1, 2]

        def evaluate(x):
            if x == 1:
                raise RuntimeError("boom")
            return float(x)

        result = flat_ucb_search(
            initial_candidate=0,
            initial_score=0,
            generate_fn=lambda parent, score, iteration: proposals[iteration],
            evaluate_fn=evaluate,
            iterations=2,
            direction="maximize",
            failure_score=-999,
        )
        self.assertEqual(result.nodes[1].status, "failed")
        self.assertEqual(result.nodes[1].raw_score, -999.0)
        self.assertEqual(result.best_candidate, 2)

    def test_rich_metadata_and_target_stop(self):
        def generate(parent, score, iteration):
            return CandidateProposal(iteration + 1, "H1", "increment")

        def evaluate(x):
            return EvaluationOutcome(float(x), {"secondary": float(x * 2)}, "ok")

        result = flat_ucb_search(
            initial_candidate=0,
            initial_score=0,
            generate_fn=generate,
            evaluate_fn=evaluate,
            iterations=10,
            direction="maximize",
            target_score=3,
        )
        self.assertEqual(result.stop_reason, "target_reached")
        self.assertEqual(result.best_candidate, 3)
        self.assertEqual(result.nodes[-1].hypothesis_id, "H1")
        self.assertEqual(result.nodes[-1].metrics["secondary"], 6.0)

    def test_patience_stop(self):
        result = flat_ucb_search(
            initial_candidate=10,
            initial_score=10,
            generate_fn=lambda p, s, i: i,
            evaluate_fn=float,
            iterations=10,
            direction="maximize",
            patience=2,
        )
        self.assertEqual(result.stop_reason, "patience_exhausted")
        self.assertEqual(len(result.nodes), 3)

    def test_invalid_direction_rejected(self):
        with self.assertRaises(ValueError):
            flat_ucb_search(
                initial_candidate=0,
                initial_score=0,
                generate_fn=lambda p, s, i: 1,
                evaluate_fn=float,
                iterations=1,
                direction="sideways",  # type: ignore
            )


if __name__ == "__main__":
    unittest.main()
