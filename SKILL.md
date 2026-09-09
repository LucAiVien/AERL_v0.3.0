---
name: AERL
description: >
  Run a multi-agent autonomous empirical research workflow built on ERA/FUTS: frame a research question, gather actionable literature evidence, generate falsifiable hypotheses, plan experiments, freeze an evaluation contract, search over executable candidates, challenge the provisional winner with an independent critic/reviewer loop, run targeted follow-up experiments, verify statistically, perform ablations, preserve provenance in a shared research blackboard, and generate a decision-ready scientific report. Use for algorithm discovery, model/pipeline optimization, robotics, semiconductor/manufacturing analytics, simulation, forecasting, scientific computing, and other research tasks with an automatable evaluator. Also use in benchmark-first or review-and-verify mode. Do not use for prose-only literature reviews or tasks without a meaningful empirical evaluation loop.
license: Apache-2.0
compatibility: ChatGPT/Codex or another Agent Skills client with Python 3.10+. Web/search is useful for literature grounding. Arbitrary generated code requires a genuinely isolated execution environment; never treat subprocess or a temporary directory as a secure sandbox.
metadata:
  author: OpenAI-generated for user
  version: "0.3.0"
  methodology: "ERA-inspired multi-agent autonomous empirical research"
---

# Automousera Research v0.3

Automousera Research is a **multi-agent autonomous scientist skill** built around the empirical search principles of ERA. ERA/FUTS remains the optimization engine, but v0.3 adds explicit agent roles, a shared blackboard, a research budget, an independent critic loop, targeted revision experiments, verification, ablation, and provenance-aware reporting.

Core lifecycle:

`frame -> literature -> hypotheses -> experiment plan -> baseline -> ERA/FUTS search -> critic -> targeted revisions -> verification -> ablation -> report`

The skill must keep four evidence classes separate:
- **Literature evidence**: externally sourced or user-provided research claims.
- **Measured empirical evidence**: outputs produced by the frozen evaluator.
- **Critic judgment**: review concerns/decisions; useful but not empirical evidence.
- **Hypothesis / interpretation**: falsifiable explanation, not a measured fact.

## 1. Activation modes

Classify the task before running.

### A. Autonomous-agent mode
Use when the user wants a full research loop and there is, or can be constructed, an executable evaluation process.

Required or constructible:
- concrete research question;
- data, simulator, benchmark, deterministic fixture, or measurable environment;
- candidate artifact represented as code/config/pipeline/model spec;
- executable evaluator;
- primary scalar objective;
- constraints and safety boundary.

Run the complete multi-agent workflow.

### B. Search-only mode
Use when the user already has a frozen benchmark, baseline, evaluator, metric, and constraints. Skip broad literature unless needed for better candidate generation. Run ERA/FUTS, critic review, verification, and optional ablation.

### C. Benchmark-first mode
Use when the research objective exists but metric, split, evaluator, or validation protocol is not ready. **Do not start ERA/FUTS.** First define and freeze the Evaluation Contract and measure the baseline.

### D. Review-and-verify mode
Use when an existing ERA/optimization winner looks suspicious, overfit, leaky, brittle, or insufficiently justified. Start from the existing ledger/candidate and prioritize critic analysis, targeted challenge experiments, and independent verification.

### E. Not an Automousera task
Do not activate for ordinary summarization, rewriting, pure literature review, brainstorming with no desire to build a benchmark, or qualitative analysis with no meaningful empirical loop.

## 2. Multi-agent team

Automousera coordinates these roles:

1. **Research Orchestrator** — owns state, task dispatch, budget, stop conditions, and approval gates.
2. **Literature Scout** — collects only actionable research priors and established baselines.
3. **Hypothesis Scientist** — creates diverse falsifiable hypotheses.
4. **Experiment Planner** — maps hypotheses and critic requests into a prioritized experiment queue.
5. **ERA Search Worker** — runs baseline measurement and ERA/FUTS candidate search.
6. **Critic / Reviewer** — independently challenges the provisional winner for leakage, weak attribution, missing baselines, constraint violations, and untested hypotheses.
7. **Statistical Verifier** — independently reruns the accepted candidate and checks robustness.
8. **Ablation Analyst** — isolates which components of the winner matter.
9. **Reporter** — synthesizes evidence, objections, verification, limitations, and next actions.

When programmatic execution is available, use `scripts/autonomous_agent.py` as the reference orchestrator.

## 3. Agent protocol

Agents communicate with explicit tasks and artifacts rather than hidden implicit state.

Reference primitives are in `scripts/agent_protocol.py`:

```yaml
AgentTask:
  id: T-HYP
  assigned_to: hypothesis-scientist
  objective: Form falsifiable hypotheses
  requested_outputs: [hypotheses]

ReviewDecision:
  verdict: accept | revise | reject
  rationale: <why>
  concerns: [<specific concern>]
  requested_experiments: [<decisive follow-up>]
  confidence: 0..1
```

Rules:
- every agent output should be traceable to an assigned task or explicit phase;
- preserve provenance for evidence, hypotheses, candidate changes, reviewer concerns, and verification results;
- a `revise` verdict must request at least one concrete follow-up experiment;
- do not convert reviewer opinion into measured evidence.

See `references/MULTI_AGENT_PROTOCOL.md`.

## 4. Shared Research Blackboard

Use an append-only, run-scoped **Team Blackboard** for coordination and provenance.

Record:
- frozen Evaluation Contract;
- agent task assignments;
- literature priors and citations;
- hypotheses;
- experiment plan;
- baseline;
- every search candidate and failure;
- critic decisions;
- critic-requested follow-up experiments;
- verification;
- ablations;
- final report/checkpoint.

Use `scripts/team_blackboard.py` for the local JSONL reference implementation.

Rules:
- never rewrite failed experiments into successes;
- never erase a critic objection because a later result looks good;
- reuse prior results only when evaluator/data/contract compatibility is explicit;
- treat the blackboard as research-run state, not user-profile memory.

## 5. Research Orchestrator

Recommended state machine:

1. `FRAME`
2. `LITERATURE`
3. `HYPOTHESES`
4. `PLAN`
5. `BASELINE`
6. `SEARCH`
7. `CRITIC_REVIEW`
8. `FOLLOWUP` (zero or more)
9. `VERIFY`
10. `ABLATE`
11. `REPORT`
12. `DONE | NEEDS_REVIEW | REJECTED`

The Orchestrator must not jump directly from a vague problem to autonomous mutation.

It must enforce a declared research budget, using `scripts/research_budget.py` when available:
- maximum evaluator calls;
- maximum critic rounds;
- ERA iteration budget;
- verification reserve;
- optional target metric/patience.

If the budget is exhausted, stop cleanly and report the incomplete evidence rather than silently skipping verification.

## 6. Literature Scout

Gather only priors that can change experiment design or candidate generation.

Prioritize:
- official papers and repositories;
- peer-reviewed work where available;
- recent high-quality preprints when relevant;
- official benchmark/evaluation docs;
- strong implementation baselines;
- credible negative results/failure modes.

Extract:
- established baselines;
- algorithms/model families worth testing;
- expected failure modes;
- evaluation conventions;
- runtime/data constraints;
- known robustness issues.

If external/current sources are used, cite them. Convert the literature into compact actionable priors instead of a long generic summary.

## 7. Hypothesis Scientist

Each hypothesis should be falsifiable:

```yaml
id: H1
statement: <what change should improve the metric>
rationale: <mechanism>
expected_effect: <metric/failure mode>
risk: <possible regression>
falsification_test: <experiment that can disprove it>
```

Prefer mechanistically diverse hypotheses over many tiny hyperparameter changes.

A hypothesis is not evidence until evaluated.

## 8. Experiment Planner

Create a hypothesis-driven queue before search. Use `scripts/experiment_planner.py` for the default implementation.

Each planned experiment should include:
- experiment ID;
- hypothesis ID;
- objective;
- priority;
- rationale.

The plan is a guide, not a reason to ignore promising unexpected results. Critic-requested experiments should be inserted as high-priority follow-ups.

## 9. Evaluation Contract

Freeze the benchmark before optimization.

```yaml
problem: <precise research question>
candidate_interface: <complete candidate contract>
inputs: [<datasets / simulator / fixtures>]
metric:
  name: <primary scalar metric>
  direction: maximize | minimize
constraints: [<latency / memory / safety / cost / validity>]
validation_protocol: <fixed split / seeds / simulation protocol>
evaluator_id: <version/hash>
final_test_visibility: hidden-from-candidates
budget:
  iterations: <N>
  target_score: <optional>
  patience: <optional>
```

Rules:
- **Never invent a baseline score.** Execute it or mark it not measured.
- Freeze evaluator, split/protocol, metric direction, and aggregate formula before search.
- Prefer one primary scalar metric; report secondary metrics separately.
- Keep final-test labels/targets inaccessible to candidate generation.
- If the evaluator is unstable or changes, stop and repair/re-freeze before comparing candidates.

## 10. ERA / FUTS Search Worker

Use `scripts/era_engine.py` as the empirical search core.

Per iteration:
1. rank measured candidates;
2. compute normalized exploitation/rank score;
3. compute PUCT-style selection value;
4. select a parent;
5. generate one complete child candidate;
6. evaluate with the frozen evaluator;
7. log score, metrics, diagnostics, parent, hypothesis, change summary, and status;
8. retain failures as evidence;
9. continue until target, patience, budget, or safety stop.

Candidates should be complete replacements, not code fragments.

Generation context should include:
- Evaluation Contract;
- selected parent + measured diagnostics;
- relevant literature priors;
- target hypothesis/experiment plan;
- previous failures;
- runtime/dependency/I/O constraints;
- reproducibility requirements.

## 11. Critic / Reviewer loop

The provisional ERA winner is **not final** until independently challenged.

The Critic should inspect:
- benchmark/data leakage;
- hard-coded answers or benchmark gaming;
- evaluator bugs or metric mismatch;
- missing stronger baselines;
- constraint violations;
- suspiciously large gains;
- untested core hypotheses;
- brittle seed dependence;
- domain shift risk;
- implausible runtime/resource assumptions;
- weak causal attribution.

Possible decisions:
- `accept` — evidence is sufficient to proceed to independent verification;
- `revise` — request one or more decisive follow-up experiments;
- `reject` — result is invalid or unsafe to promote.

On `revise`, the ERA Search Worker runs targeted follow-up experiment(s), records them on the blackboard, updates the provisional winner only if empirically better/valid, and sends the result back to the Critic.

Never accept a result merely because the same agent that generated it says it is correct.

See `references/CRITIC_LOOP.md`.

## 12. Statistical Verifier

After critic acceptance, independently verify the selected candidate.

Minimum checks:
1. clean rebuild/rerun from fresh state;
2. fixed/predeclared seeds where applicable;
3. repeated runs for stochastic systems;
4. mean/variance or appropriate confidence interval;
5. comparison with seed and strongest relevant baseline;
6. hidden-test/untouched validation when feasible;
7. leakage/hard-coding/constraint checks.

Use `scripts/verification_stats.py` for lightweight score summaries. For serious scientific claims, choose domain-appropriate statistical tests and power analysis rather than relying only on the bundled normal-approximation CI.

A candidate that fails independent verification is not a final winner.

## 13. Ablation Analyst

Run hypothesis-linked ablations where useful:
- remove a new component;
- revert one feature/input;
- neutralize an objective term;
- swap one algorithmic choice;
- test sensitivity to a critical hyperparameter;
- test under shifted conditions.

Use `scripts/ablation.py` when programmatic evaluation is available.

Do not claim a component is causal unless the ablation isolates it sufficiently.

## 14. Reporter

The final report must include:
1. Research question
2. Evaluation Contract
3. Literature evidence/baselines
4. Hypotheses
5. Multi-agent experiment plan
6. ERA/FUTS method and budget
7. Experiment ledger
8. Baseline vs provisional/final best
9. Critic decisions and requested follow-ups
10. Independent verification
11. Ablations
12. Failure analysis
13. Threats to validity / limitations
14. Autonomy boundary / approval requirements
15. Next experiments

Use `scripts/reporting.py` as a minimal renderer.

## 15. Autonomy boundary and approval gates

Automousera is autonomous **inside a pre-authorized research sandbox**, not autonomous over real-world side effects.

The agent may independently:
- search/read research sources when tools allow;
- reason about hypotheses;
- create experiment plans;
- generate candidate code/configs;
- run pre-authorized isolated/offline evaluators;
- critique results;
- run verification/ablation within the declared budget;
- write reports.

Require explicit host/user approval before:
- production deployment;
- physical robot/machine/process control;
- changing external systems or customer data;
- using credentials/secrets not already authorized for the research run;
- purchasing/financial commitments;
- irreversible or high-impact external actions.

See `references/AUTONOMY_BOUNDARIES.md`.

## 16. Execution safety

Generated code is untrusted.

- Use a genuinely isolated sandbox/container when available.
- Never describe `subprocess`, `exec`, a temporary directory, or Code Interpreter alone as a security boundary for arbitrary untrusted code.
- Default-deny network, credentials, host filesystem, and shell access unless required and isolated.
- Mount only required inputs, preferably read-only.
- Enforce time/memory/process limits where supported.
- Keep hidden labels/test targets outside candidate-visible files.
- Log evaluator version, code/artifact identity, exit status, metric, and diagnostics.

If secure arbitrary-code execution is unavailable, use declarative allow-listed candidate specs, deterministic fixtures, static analysis, or an approved external sandbox; label the result as dry-run/limited validation.

See `references/SAFETY.md`.

## 17. Robotics / semiconductor / advanced manufacturing playbook

For robotics, inspection, semiconductor, predictive maintenance, process control, or smart-factory tasks, explicitly consider:
- cross-run memory vs within-run adaptation;
- simulator/digital twin vs real-line validation;
- product/tool/recipe/lot/time domain shifts;
- false-negative cost and rare-defect coverage;
- edge latency/compute constraints;
- drift/degradation detection;
- equipment/process safety;
- rollback and human approval;
- shadow mode before closed-loop deployment.

Recommended validation ladder:

`offline replay -> simulator/digital twin -> historical holdout -> shadow production -> limited pilot -> human-approved deployment`

A strong offline metric alone must never justify autonomous physical control.

## 18. Stop conditions

Stop when any declared condition applies:
- target score reached and evidence is sufficient;
- ERA iteration budget exhausted;
- patience exhausted;
- evaluation budget exhausted;
- critic rejects the candidate;
- critic rounds exhausted without acceptance;
- evaluator instability invalidates comparisons;
- safety/resource constraints block further work;
- winner is independently verified for the research decision.

Do not consume budget merely because it exists.

## 19. Quality gate before final answer

Check:
- [ ] correct activation mode;
- [ ] frozen Evaluation Contract;
- [ ] real baseline measurement;
- [ ] actionable literature evidence cited when external sources were used;
- [ ] falsifiable hypotheses;
- [ ] explicit experiment plan;
- [ ] every empirical score came from execution;
- [ ] failures retained in ledger/blackboard;
- [ ] critic independently reviewed provisional winner;
- [ ] critic `revise` requests produced concrete follow-up experiments;
- [ ] rejected candidates are not promoted;
- [ ] accepted winner was independently rerun;
- [ ] stochastic results use repeated runs when needed;
- [ ] hidden/held-out validation used when feasible;
- [ ] ablations run or explicitly marked unavailable/unnecessary;
- [ ] report separates literature, measurements, critic judgment, and hypotheses;
- [ ] autonomy/approval boundary is explicit for external or physical actions;
- [ ] limitations and next experiments are stated.

## 20. Bundled resources

Multi-agent core:
- `scripts/autonomous_agent.py` — v0.3 autonomous-scientist orchestrator.
- `scripts/agent_protocol.py` — agent tasks, artifacts, reviewer decisions.
- `scripts/team_blackboard.py` — shared append-only coordination/provenance store.
- `scripts/research_budget.py` — evaluation and critic-round budget accounting.
- `scripts/experiment_planner.py` — hypothesis-driven experiment plan.

Empirical core:
- `scripts/era_engine.py` — ERA-style Flat UCB/PUCT engine.
- `scripts/contracts.py` — evaluation/evidence/hypothesis/run contracts.
- `scripts/verification_stats.py` — repeated-score summaries.
- `scripts/ablation.py` — ablation runner.
- `scripts/reporting.py` — v0.2/v0.3 Markdown report renderers.

Compatibility/examples:
- `scripts/research_agent.py` — retained v0.2 single-orchestrator compatibility layer.
- `scripts/demo_era_search.py` — deterministic search-only demo.
- `scripts/demo_full_research_agent.py` — v0.2 compatibility demo.
- `scripts/demo_autonomous_scientist.py` — v0.3 multi-agent critic-loop demo.
- `scripts/test_empirical_pipeline.py` — declarative sklearn integration test.
- `scripts/validate_skill.py` — package validator.
- `evals/evals.json` — activation/mode tests.

Local validation:

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
python scripts/demo_era_search.py
python scripts/demo_full_research_agent.py
python scripts/demo_autonomous_scientist.py
python scripts/test_empirical_pipeline.py
```
