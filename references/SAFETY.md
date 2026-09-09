# Generated-code execution safety

ERA-style research repeatedly proposes candidate programs. Treat arbitrary generated code as untrusted.

## Minimum policy

1. Prefer a dedicated isolated sandbox/container supplied by the host environment.
2. Default-deny network access and credentials.
3. Mount only files needed for the evaluator, ideally read-only.
4. Use CPU/time/memory/process limits when available.
5. Keep hidden labels/test targets outside candidate-visible files and prompts.
6. Never interpolate secrets into candidate code or prompts.
7. Log candidate source/hash, evaluator version/hash, exit status, and metric.
8. A plain `exec`, `eval`, `subprocess`, temp directory, or local virtualenv is not a security boundary.

## Safer candidate spaces

When scientifically sufficient, prefer candidate representations that cannot express arbitrary system actions:
- validated YAML/JSON configs;
- allow-listed model families;
- bounded numeric hyperparameters;
- declarative pipeline graphs;
- SQL restricted to a read-only evaluation database;
- simulator policy parameters with schema validation.

## If isolation is unavailable

Do not execute arbitrary generated code. Alternatives:
- deterministic safe fixtures;
- allow-listed declarative candidates;
- static review;
- user-approved sandbox/runtime.

Label the result as a dry-run or restricted empirical evaluation.

## Physical systems

For robotics/manufacturing/process-control tasks, do not directly deploy a search-generated winner to equipment based only on offline metrics. Require an appropriate progression such as simulator/digital twin, offline replay, shadow mode, limited pilot, human approval, monitoring, and rollback.
