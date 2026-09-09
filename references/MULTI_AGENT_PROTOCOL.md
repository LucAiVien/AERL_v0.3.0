# Multi-Agent Protocol

Automousera uses explicit coordination instead of hidden role-play state.

## Roles

- orchestrator
- literature-scout
- hypothesis-scientist
- experiment-planner
- era-search-worker
- critic-reviewer
- statistical-verifier
- ablation-analyst
- reporter

## Tasks and artifacts

Every substantive phase should be represented as an assigned task and one or more artifacts/events on the Team Blackboard. Preserve task IDs, agent role, artifact type, and provenance.

A review decision has one of three verdicts:
- `accept`: proceed to independent verification;
- `revise`: request at least one decisive follow-up experiment;
- `reject`: stop promotion of the current result.

The Critic should not silently mutate candidates itself. It requests experiments; the Search Worker executes them under the frozen evaluator.

## Provenance rules

Do not overwrite prior events. Failed candidates, negative results, critic concerns, and evaluator diagnostics remain part of the run record. A later successful experiment does not erase earlier uncertainty.
