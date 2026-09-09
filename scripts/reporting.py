"""Markdown reporting for Automousera Research v0.3 and v0.2 compatibility."""

from __future__ import annotations

from typing import Any

from contracts import AutonomousResearchRun, ResearchRun
from verification_stats import summarize_scores


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _base_sections(run: ResearchRun, title: str) -> list[str]:
    metric = run.contract.metric
    improvement = run.improvement()
    lines = [
        title,
        "",
        "## Research question",
        run.contract.problem,
        "",
        "## Evaluation Contract",
        f"- Candidate interface: {run.contract.candidate_interface}",
        f"- Metric: {metric.name} ({metric.direction})",
        f"- Evaluator: {run.contract.evaluator_id}",
        f"- Iteration budget: {run.contract.iterations}",
        f"- Validation protocol: {run.contract.validation_protocol or 'not specified'}",
        f"- Final-test visibility: {run.contract.final_test_visibility}",
        "",
        "## Literature / prior evidence",
    ]
    if run.priors:
        for e in run.priors:
            lines.append(f"- [{e.kind}] {e.claim}" + (f" — {e.source}" if e.source else ""))
    else:
        lines.append("- No external priors were supplied in this run.")

    lines += ["", "## Hypotheses"]
    if run.hypotheses:
        for h in run.hypotheses:
            extra = f"; falsification={h.falsification_test}" if h.falsification_test else ""
            lines.append(f"- **{h.id}**: {h.statement} — {h.rationale}{extra}")
    else:
        lines.append("- No explicit hypotheses were supplied.")

    lines += [
        "",
        "## Baseline vs best",
        f"- Baseline score: {_fmt(run.seed_score)}",
        f"- Best score: {_fmt(run.best_score)}",
        f"- Directional improvement: {_fmt(improvement)}",
        "",
        "## Experiment ledger",
        "| Node | Parent | Hypothesis | Change | Score | Status |",
        "|---:|---:|---|---|---:|---|",
    ]
    for row in run.search_ledger:
        lines.append(
            f"| {row.get('index')} | {row.get('parent_index')} | {row.get('hypothesis_id', '')} | "
            f"{row.get('change_summary', '')} | {_fmt(row.get('raw_score'))} | {row.get('status')} |"
        )
    return lines


def build_markdown_report(run: ResearchRun) -> str:
    lines = _base_sections(run, "# ERA Research Report")
    lines += ["", "## Verification"]
    if run.verification_scores:
        s = summarize_scores(run.verification_scores)
        lines.append(
            f"- Clean reruns: n={s.n}, mean={_fmt(s.mean)}, std={_fmt(s.std)}, "
            f"95% CI≈[{_fmt(s.ci95_low)}, {_fmt(s.ci95_high)}]"
        )
    else:
        lines.append("- Not run.")
    lines += ["", "## Ablations"]
    if run.ablations:
        for a in run.ablations:
            lines.append(f"- {a.get('label')}: score={_fmt(a.get('score'))}; delta_from_best={_fmt(a.get('delta_from_best'))}; status={a.get('status')}")
    else:
        lines.append("- No ablations were requested.")
    lines += ["", "## Limitations"]
    lines.extend(f"- {x}" for x in run.limitations) if run.limitations else lines.append("- None recorded by the orchestrator; domain-specific limitations may still apply.")
    lines += [
        "",
        "## Evidence labels",
        "- **Literature evidence** comes from external sources or supplied priors.",
        "- **Measured empirical evidence** comes from the frozen evaluator.",
        "- **Hypotheses / interpretation** explain why a change may have helped and are not measurements.",
    ]
    return "\n".join(lines) + "\n"


def build_autonomous_markdown_report(run: AutonomousResearchRun) -> str:
    lines = _base_sections(run, "# Automousera Research Report")

    lines += ["", "## Multi-agent experiment plan"]
    for item in run.plan:
        lines.append(
            f"- **{item.get('id')}** [{item.get('hypothesis_id') or 'unassigned'}] "
            f"priority={item.get('priority')}: {item.get('objective')}"
        )

    lines += ["", "## Critic / reviewer loop"]
    if run.review_history:
        for i, review in enumerate(run.review_history, 1):
            requests = "; ".join(review.get("requested_experiments") or []) or "none"
            concerns = "; ".join(review.get("concerns") or []) or "none"
            lines.append(
                f"- Round {i}: **{review.get('verdict')}** (confidence={_fmt(review.get('confidence'))}) — "
                f"{review.get('rationale')}; concerns={concerns}; requested={requests}"
            )
    else:
        lines.append("- Critic was not run.")

    lines += [
        "",
        "## Autonomous run status",
        f"- Final status: **{run.final_status}**",
        f"- Critic accepted winner: {run.accepted_by_critic}",
        f"- Stop reason: {run.stop_reason}",
        f"- Budget: {run.budget}",
        "",
        "## Verification",
    ]
    if run.verification_scores:
        s = summarize_scores(run.verification_scores)
        lines.append(
            f"- Independent reruns: n={s.n}, mean={_fmt(s.mean)}, std={_fmt(s.std)}, "
            f"95% CI≈[{_fmt(s.ci95_low)}, {_fmt(s.ci95_high)}]"
        )
    else:
        lines.append("- Not completed; do not promote this result as verified.")

    lines += ["", "## Ablations"]
    if run.ablations:
        for a in run.ablations:
            lines.append(f"- {a.get('label')}: score={_fmt(a.get('score'))}; delta_from_best={_fmt(a.get('delta_from_best'))}; status={a.get('status')}")
    else:
        lines.append("- Not run or no budget/adapter was available.")

    lines += ["", "## Agent trace / provenance"]
    for i, event in enumerate(run.agent_trace, 1):
        lines.append(f"- {i}. `{event.get('agent')}` → `{event.get('event_type')}`")

    lines += ["", "## Limitations and autonomy boundary"]
    if run.limitations:
        lines.extend(f"- {x}" for x in run.limitations)
    lines += [
        "- Agent autonomy is limited to research reasoning and pre-authorized empirical evaluation.",
        "- External side effects, production deployment, physical control, credential use, or irreversible actions require an explicit host/user approval gate.",
        "- A critic acceptance is not a substitute for hidden-test validation, statistical power, domain safety review, or peer review.",
        "",
        "## Evidence labels",
        "- **Literature evidence**: externally sourced prior claims.",
        "- **Measured empirical evidence**: outputs of the frozen evaluator.",
        "- **Critic judgment**: a review decision, not empirical evidence.",
        "- **Hypothesis / interpretation**: falsifiable explanation, not measurement.",
    ]
    return "\n".join(lines) + "\n"
