"""Package validator for Automousera Research v0.3."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_NAME = "automousera-research"
EXPECTED_VERSION = "0.3.0"


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.exists():
        return ["SKILL.md is missing"]
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ["SKILL.md must start with YAML frontmatter"]
    try:
        _, yaml_text, body = text.split("---", 2)
        meta = yaml.safe_load(yaml_text) or {}
    except Exception as exc:
        return [f"frontmatter parse failed: {exc}"]

    name = meta.get("name")
    desc = meta.get("description")
    version = (meta.get("metadata") or {}).get("version")
    if name != EXPECTED_NAME:
        errors.append(f"name must be {EXPECTED_NAME}")
    elif not NAME_RE.fullmatch(name):
        errors.append("name must use lowercase letters, numbers, and hyphens")
    if root.name not in {EXPECTED_NAME, f"{EXPECTED_NAME}-v0.3", "automousera-research-package"}:
        errors.append(f"directory name '{root.name}' is not compatible with skill name '{EXPECTED_NAME}'")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("description is required")
    elif len(desc) > 1024:
        errors.append("description exceeds 1024 chars")
    if version != EXPECTED_VERSION:
        errors.append(f"metadata.version must be {EXPECTED_VERSION}")
    if not body.strip():
        errors.append("SKILL.md body is empty")

    required = [
        "scripts/era_engine.py",
        "scripts/contracts.py",
        "scripts/agent_protocol.py",
        "scripts/autonomous_agent.py",
        "scripts/experiment_planner.py",
        "scripts/research_budget.py",
        "scripts/team_blackboard.py",
        "scripts/verification_stats.py",
        "scripts/ablation.py",
        "scripts/reporting.py",
        "scripts/demo_autonomous_scientist.py",
        "references/ERA_METHOD.md",
        "references/MULTI_AGENT_PROTOCOL.md",
        "references/CRITIC_LOOP.md",
        "references/AUTONOMY_BOUNDARIES.md",
        "references/VERIFICATION.md",
        "references/SAFETY.md",
        "evals/evals.json",
    ]
    for path in required:
        if not (root / path).exists():
            errors.append(f"missing bundled resource: {path}")
    try:
        evals = json.loads((root / "evals" / "evals.json").read_text(encoding="utf-8"))
        if evals.get("version") != EXPECTED_VERSION:
            errors.append(f"eval suite version must be {EXPECTED_VERSION}")
    except Exception as exc:
        errors.append(f"evals/evals.json invalid: {exc}")
    return errors


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("PASS: Automousera Research v0.3 package structure/frontmatter is valid")


if __name__ == "__main__":
    main()
