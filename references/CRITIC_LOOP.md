# Critic / Reviewer Loop

The v0.3 critic loop exists to prevent self-confirming research.

## Review checklist

Challenge the provisional winner for:
- data or benchmark leakage;
- hard-coded test answers;
- evaluator bugs;
- missing stronger baselines;
- metric/constraint mismatch;
- seed dependence;
- suspicious gain magnitude;
- untested hypotheses;
- runtime/resource violations;
- domain shift brittleness;
- insufficient causal attribution.

## Revise loop

A `revise` decision must contain a concrete experiment request. The Experiment Planner/Search Worker converts it into a candidate or evaluation, runs it with the same frozen evaluator, records it, and returns the result to the Critic.

The critic loop is bounded by `max_critic_rounds`. If the budget expires without acceptance, final status should remain `needs_review` rather than being silently promoted.

## Independence

Where practical, use a different prompt/model/context for the Critic than the candidate generator. At minimum, the reviewer must receive the ledger and constraints and be instructed to find falsifying evidence, not justify the winner.
