# Automousera Orchestration v0.3

The Orchestrator owns phase transitions, research budget, Team Blackboard, and approval gates.

State machine:
`FRAME -> LITERATURE -> HYPOTHESES -> PLAN -> BASELINE -> SEARCH -> CRITIC_REVIEW -> FOLLOWUP* -> VERIFY -> ABLATE -> REPORT`.

Terminal states:
- `verified`
- `verified_with_variance`
- `candidate_unverified`
- `needs_review`
- `rejected_by_critic`

Never bypass the Evaluation Contract or promote a critic-rejected candidate.
