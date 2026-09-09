# Automousera Research v0.3.0

**Automousera Research** is a multi-agent autonomous empirical research skill built on the ERA/FUTS optimization pattern.

## What changed from ERA Research v0.2

v0.2 managed a full research lifecycle through one orchestrator. v0.3 introduces explicit research agents and a challenge/revision loop:

```text
Research Orchestrator
    |
    +--> Literature Scout
    +--> Hypothesis Scientist
    +--> Experiment Planner
    +--> ERA Search Worker ----> provisional winner
    |                              |
    |                              v
    +--> Critic / Reviewer <---- challenge
    |          |
    |          +-- revise --> targeted follow-up --> review again
    |          +-- reject --> stop / needs redesign
    |          `-- accept
    |
    +--> Statistical Verifier
    +--> Ablation Analyst
    `--> Reporter

All agents <----> Team Blackboard
                   + provenance
                   + failures
                   + reviewer concerns
                   + budget/checkpoints
```

## Key v0.3 capabilities

- explicit `AgentTask`, `AgentArtifact`, and `ReviewDecision` protocol;
- hypothesis-driven experiment planning;
- shared append-only Team Blackboard;
- evaluation and critic-round budgets;
- ERA/FUTS search over complete candidates;
- critic `accept / revise / reject` loop;
- targeted critic-requested follow-up experiments;
- independent clean-rerun verification;
- ablation analysis;
- evidence/provenance-aware research reporting;
- explicit autonomy boundaries for production/physical side effects;
- backward-compatible v0.2 orchestrator and ERA engine.

## Safe local validation

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
python scripts/demo_era_search.py
python scripts/demo_full_research_agent.py
python scripts/demo_autonomous_scientist.py
python scripts/test_empirical_pipeline.py
```

The deterministic demos use declarative candidates and do **not** execute model-generated Python. The sklearn integration test uses an allow-listed candidate space.

## Host integration

A ChatGPT/Codex host can map:
- web/deep research -> Literature Scout;
- model reasoning -> Hypothesis Scientist / Experiment Planner / Critic;
- model/code generation -> ERA Search Worker candidate generator;
- isolated benchmark runner -> evaluator;
- repeated independent runner -> Statistical Verifier;
- domain variant generator -> Ablation Analyst.

The host remains responsible for secure execution and approval gates for external or physical side effects.

## Package root

The installable ZIP should contain a directory named `automousera-research` with `SKILL.md` inside that directory.
