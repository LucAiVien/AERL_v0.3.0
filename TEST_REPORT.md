# Automousera Research v0.3.0 — Test Report

## Scope

This package was tested as a local Agent Skill reference implementation before packaging. Tests use deterministic or allow-listed declarative candidates; they do not claim that arbitrary generated code is safely sandboxed.

## 1. Package validation

Command:

```bash
python scripts/validate_skill.py .
```

Result: **PASS**

Validated:
- `name: automousera-research`;
- version `0.3.0`;
- YAML frontmatter;
- required multi-agent modules and references;
- eval suite version;
- package directory compatibility.

## 2. Unit / contract tests

Command:

```bash
python -m unittest discover -s tests -v
```

Result: **23 / 23 PASS**

Coverage includes:
- ERA maximize/minimize search;
- failed candidate retention;
- rich candidate/evaluator metadata;
- target and patience stopping;
- Evaluation Contract validation;
- score summaries;
- v0.2 single-orchestrator compatibility;
- agent task/artifact protocol validation;
- critic `revise` contract requiring follow-up experiments;
- evaluation and critic-round budget enforcement;
- shared Team Blackboard query/checkpoint;
- autonomous `revise -> follow-up -> accept` lifecycle;
- critic rejection blocking verification;
- budget reservation for independent verification;
- activation eval modes and package validator.

## 3. v0.3 autonomous-scientist E2E

Command:

```bash
python scripts/demo_autonomous_scientist.py
```

Synthetic objective:

```text
loss = (x - 7)^2 + (regularizer - 1)^2
```

Baseline:

```text
Candidate(x=0, regularizer=0) -> loss 50
```

ERA search intentionally stops at a provisional winner that has not tested the regularizer hypothesis. The Critic then requests the targeted experiment `regularizer=1`.

Observed critic sequence:

```text
revise -> accept
```

Final result:

```text
Candidate(x=7, regularizer=1) -> loss 0
verification = [0, 0, 0]
final_status = verified
```

Research budget:

```text
max_evaluations=20
evaluations_used=11
max_critic_rounds=2
critic_rounds_used=2
```

Shared blackboard recorded 22 events in this deterministic run.

Result: **PASS**

## 4. ERA engine compatibility dry-run

Command:

```bash
python scripts/demo_era_search.py
```

Baseline squared error: `49`.
Known optimum: `candidate=7`, score `0`.

Result: **PASS**

## 5. v0.2 lifecycle compatibility

Command:

```bash
python scripts/demo_full_research_agent.py
```

The retained v0.2 orchestrator still completes:

```text
framing -> priors -> hypotheses -> ERA search -> verification -> ablation -> memory -> report
```

Result: **PASS**

## 6. Empirical sklearn integration

Command:

```bash
python scripts/test_empirical_pipeline.py
```

Dataset: scikit-learn Breast Cancer fixture.
Primary metric: macro-F1, maximize.
Frozen split: `random_state=41`.

Baseline:

```text
LogisticRegression C=0.05 -> 0.955237
```

Best allow-listed candidate:

```text
SVC C=1.0 gamma=scale -> 0.974697
```

Absolute improvement: `+0.019459`.
Clean rerun: `0.974697`.

Result: **PASS**

## 7. Safety / test limitations

Not tested locally:
- actual ChatGPT skill-routing behavior after installation;
- real web/deep-research adapters;
- real multi-model independence between generator and critic;
- arbitrary model-generated code execution in a production-grade sandbox;
- real physical/production deployment;
- domain-specific statistical power or peer review.

The package explicitly requires host-provided isolation and approval gates for external/physical side effects.
