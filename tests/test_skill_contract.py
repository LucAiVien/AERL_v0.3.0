import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_skill import validate


class SkillContractTests(unittest.TestCase):
    def test_package_validates(self):
        self.assertEqual(validate(ROOT), [])

    def test_eval_suite_has_positive_negative_and_modes(self):
        data = json.loads((ROOT / "evals" / "evals.json").read_text())
        flags = {case["should_trigger"] for case in data["cases"]}
        modes = {case.get("mode") for case in data["cases"] if case["should_trigger"]}
        self.assertEqual(flags, {True, False})
        self.assertTrue({"autonomous-agent", "benchmark-first", "search-only", "review-and-verify"}.issubset(modes))
        self.assertGreaterEqual(len(data["cases"]), 10)

    def test_skill_contains_v03_multi_agent_gates(self):
        text = (ROOT / "SKILL.md").read_text()
        for phrase in [
            "Automousera Research v0.3",
            "Research Orchestrator",
            "Literature Scout",
            "Hypothesis Scientist",
            "Experiment Planner",
            "ERA / FUTS Search Worker",
            "Critic / Reviewer loop",
            "Statistical Verifier",
            "Ablation Analyst",
            "Shared Research Blackboard",
            "Never invent a baseline score",
            "Autonomy boundary and approval gates",
            "Execution safety",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
