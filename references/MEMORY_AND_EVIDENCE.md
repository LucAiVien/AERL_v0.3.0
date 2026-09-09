# Research memory and evidence model

## Research memory is not profile memory

ERA Research memory stores experiment provenance for a research project. It should not be used as a hidden store of personal user attributes.

## Event types

Recommended append-only events:
- `evaluation_contract`
- `evidence`
- `hypothesis`
- `baseline`
- `experiment`
- `verification`
- `ablation`
- `report`

Every empirical event should be traceable to the evaluator version and candidate specification/code hash when available.

## Evidence classes

### Literature evidence
A claim supported by a paper, official implementation, benchmark documentation, or supplied source. Preserve citation/provenance.

### Measured empirical evidence
A result produced by the frozen evaluator in the current compatible experiment environment.

### Hypothesis / interpretation
A proposed explanation or mechanism. It remains a hypothesis even if plausible; ablation or targeted experiments are needed to strengthen causal attribution.

### Diagnostic evidence
Runtime errors, failure traces, data-quality observations, drift signals, or other measurements that guide the next experiment but are not the primary objective.

## Compatibility before reuse

Do not reuse a past score as directly comparable if any of these changed materially:
- dataset/version;
- split/protocol;
- evaluator implementation;
- primary metric formula;
- hardware/runtime behavior affecting metric;
- constraints;
- candidate interface.

When in doubt, rerun the baseline under the current contract.
