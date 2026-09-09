# ERA method mapping

## Primary sources

- Paper: Eser Aygün et al., **An AI system to help scientists write expert-level empirical software**, arXiv:2509.06503.
  - https://arxiv.org/abs/2509.06503
- Official implementation: Google Research ERA.
  - https://github.com/google-research/era
  - https://github.com/google-research/era/tree/main/implementation
- Generated experimental code/trees:
  - https://google-research.github.io/era/

## Preserved ERA core

The ERA reference implementation separates task-specific candidate generation and execution/evaluation from a Flat-UCB/PUCT-style search policy. The search maintains candidate nodes, uses rank-normalized quality, balances exploitation and visits, selects a promising parent, creates one child, evaluates it, retains the node, and propagates visit counts.

`scripts/era_engine.py` is an independent implementation of those published ideas; no Google source file is vendored.

## What v0.2 adds

v0.2 does not replace ERA. It wraps ERA search in a research control plane:
- Literature Agent;
- Hypothesis Agent;
- Experiment Designer / frozen Evaluation Contract;
- Research Orchestrator;
- append-only Research Memory;
- Statistical Verifier;
- Ablation Agent;
- Scientific Report Generator;
- manufacturing/robotics validation ladder.

The purpose is to ensure that empirical search answers a stable scientific question and that the selected winner is verified rather than merely optimized on one validation metric.

## Sandbox distinction

The official repository's sandbox abstraction does not by itself make arbitrary local execution safe. This skill therefore treats execution isolation as a host responsibility and never labels a normal subprocess as a secure sandbox.
