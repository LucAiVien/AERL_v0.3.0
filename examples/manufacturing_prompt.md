# Example: Automousera Research for Advanced Manufacturing

Use Automousera Research to improve a semiconductor visual-inspection pipeline.

Available:
- labeled historical images with product/tool/lot metadata;
- current model and inference pipeline;
- frozen validation split with macro-F1 as the primary metric;
- secondary metrics: false-negative rate, latency, GPU memory;
- isolated offline evaluation environment.

Ask the agent team to:
1. research strong recent priors;
2. create falsifiable hypotheses;
3. plan and run ERA/FUTS experiments;
4. have an independent Critic challenge the provisional winner for leakage, rare-defect coverage, product/lot shift, and latency constraints;
5. run targeted follow-ups requested by the Critic;
6. independently verify the accepted winner across fixed seeds and historical holdout groups;
7. run ablations;
8. propose a shadow-mode pilot only if evidence is strong.

Do not deploy or change production equipment. Any pilot recommendation must retain human approval and rollback.
