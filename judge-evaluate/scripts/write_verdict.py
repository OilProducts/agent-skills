#!/usr/bin/env python3
"""Create verdict.json for judge-evaluate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_VERDICTS = {"pass", "reject", "needs-human"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write verdict artifact")
    parser.add_argument("--task-id", required=True, help="Task id")
    parser.add_argument("--output", required=True, help="Output verdict.json path")
    parser.add_argument("--verdict", required=True, choices=sorted(ALLOWED_VERDICTS), help="Verdict status")
    parser.add_argument("--eval-results", help="Path to eval-results.json")
    parser.add_argument(
        "--reason",
        action="append",
        default=[],
        help="Reason in format '<check>::<details>' (repeatable)",
    )
    parser.add_argument(
        "--required-change",
        action="append",
        default=[],
        help="Required change text (repeatable)",
    )
    parser.add_argument(
        "--suggested-test",
        action="append",
        default=[],
        help="Runnable suggested test command (repeatable)",
    )
    parser.add_argument(
        "--requirement-checked",
        action="append",
        default=[],
        help="Requirement ID validated by this verdict (repeatable)",
    )
    parser.add_argument(
        "--requirement-missing",
        action="append",
        default=[],
        help="Requirement ID still unmet (repeatable)",
    )
    parser.add_argument("--notes", default="", help="Optional short note")
    return parser.parse_args()


def parse_reasons(raw_reasons: list[str]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    for item in raw_reasons:
        if "::" not in item:
            raise ValueError(f"Invalid --reason '{item}'. Expected '<check>::<details>'.")
        check, details = item.split("::", 1)
        check = check.strip()
        details = details.strip()
        if not check or not details:
            raise ValueError(f"Invalid --reason '{item}'. Check and details must be non-empty.")
        reasons.append({"check": check, "details": details})
    return reasons


def collect_eval_failures(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    failures: list[dict[str, str]] = []
    for item in data.get("results", []):
        status = str(item.get("status", "")).strip()
        if status != "fail":
            continue
        cmd = str(item.get("command", "")).strip()
        exit_code = item.get("exit_code")
        failures.append(
            {
                "check": "eval",
                "details": f"Command failed (exit {exit_code}): {cmd}",
            }
        )
    return failures


def main() -> int:
    args = parse_args()

    reasons = parse_reasons(args.reason)

    if args.eval_results:
        eval_path = Path(args.eval_results).resolve()
        if not eval_path.is_file():
            raise SystemExit(f"error: eval results not found: {eval_path}")
        reasons.extend(collect_eval_failures(eval_path))

    required_changes = [c.strip() for c in args.required_change if c and c.strip()]
    suggested_tests = [t.strip() for t in args.suggested_test if t and t.strip()]
    requirements_checked = [r.strip() for r in args.requirement_checked if r and r.strip()]
    requirements_missing = [r.strip() for r in args.requirement_missing if r and r.strip()]

    if args.verdict in {"reject", "needs-human"} and not reasons:
        raise SystemExit("error: reject/needs-human verdict requires at least one reason")

    payload = {
        "task_id": args.task_id.strip(),
        "verdict": args.verdict,
        "reasons": reasons,
        "required_changes": required_changes,
        "suggested_tests": suggested_tests,
        "requirements_checked": requirements_checked,
        "requirements_missing": requirements_missing,
        "notes": args.notes.strip(),
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
