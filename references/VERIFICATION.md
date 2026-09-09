# Verification and threats to validity

## Minimum winner verification

1. Rebuild/reload the selected candidate from a clean state.
2. Rerun the frozen evaluator.
3. For stochastic systems, use multiple predeclared seeds or repeated trials.
4. Report central tendency and variability.
5. Compare to the baseline under the same protocol.
6. Inspect for leakage, answer hard-coding, benchmark-specific hacks, and invalid shortcuts.
7. Evaluate on untouched holdout data when available.

## Statistical guidance

`scripts/verification_stats.py` provides a lightweight normal-approximation 95% interval for repeated scalar scores. This is a diagnostic convenience only.

Use a domain-appropriate method for serious claims, for example:
- paired tests when the same units/cases are evaluated under two methods;
- bootstrap intervals for non-normal metrics;
- confidence intervals for proportions/defect rates;
- time-series-aware resampling for temporal data;
- hierarchical/mixed analysis when data is grouped by tool, line, product, patient, site, etc.

Predeclare the primary decision rule when feasible.

## Manufacturing threats to validity

A good random split can still be misleading if records from the same lot, wafer, machine, recipe, shift, or product family leak across train/validation boundaries. Prefer group/time/tool-aware splits that resemble deployment.

Before controlling a real process, validate offline gains in shadow mode or an approved simulator/digital twin and maintain rollback/human approval.
