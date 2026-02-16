#!/usr/bin/env python3
"""Write audit.json gate artifact for auditor-gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_GATES = {"pass", "fail", "needs-human"}
ALLOWED_RISK = {"low", "medium", "high"}
ALLOWED_POLICY = {"pass", "fail", "unknown"}
ALLOWED_TRACE = {"pass", "fail", "unknown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write audit gate artifact")
    parser.add_argument("--task-id", required=True, help="Task id")
    parser.add_argument("--output", required=True, help="Output audit.json path")
    parser.add_argument("--gate", required=True, choices=sorted(ALLOWED_GATES), help="Gate result")
    parser.add_argument("--audit-results", help="Path to audit-results.json")
    parser.add_argument(
        "--finding",
        action="append",
        default=[],
        help="Finding in format '<category>::<details>' (repeatable)",
    )
    parser.add_argument(
        "--required-action",
        action="append",
        default=[],
        help="Required follow-up action (repeatable)",
    )
    parser.add_argument("--risk-level", default="medium", choices=sorted(ALLOWED_RISK), help="Risk level")
    parser.add_argument("--notes", default="", help="Optional short note")
    return parser.parse_args()


def parse_findings(raw_findings: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for item in raw_findings:
        if "::" not in item:
            raise ValueError(f"Invalid --finding '{item}'. Expected '<category>::<details>'.")
        category, details = item.split("::", 1)
        category = category.strip()
        details = details.strip()
        if not category or not details:
            raise ValueError(f"Invalid --finding '{item}'. Category and details must be non-empty.")
        findings.append({"category": category, "details": details})
    return findings


def derive_from_results(path: Path) -> tuple[list[dict[str, str]], dict, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))

    derived_findings: list[dict[str, str]] = []
    issues: list[str] = []

    checks = data.get("checks", [])
    commands = data.get("commands", [])

    check_failures = [c for c in checks if str(c.get("status", "")) == "fail"]
    command_failures = [c for c in commands if str(c.get("status", "")) == "fail"]

    for item in check_failures:
        name = str(item.get("name", "check")).strip() or "check"
        details = str(item.get("details", "failed")).strip() or "failed"
        derived_findings.append({"category": "integrity", "details": f"{name}: {details}"})
        issues.append(f"{name}: {details}")

    for item in command_failures:
        cmd = str(item.get("command", "command")).strip() or "command"
        code = item.get("exit_code")
        derived_findings.append(
            {
                "category": "policy",
                "details": f"audit command failed (exit {code}): {cmd}",
            }
        )
        issues.append(f"audit command failed (exit {code}): {cmd}")

    policy = {
        "artifact_integrity": "fail" if check_failures else "pass",
        "eval_commands": "unknown" if not commands else ("fail" if command_failures else "pass"),
    }

    task_align = next((c for c in checks if c.get("name") == "task_id_alignment"), None)
    req_trace = next((c for c in checks if c.get("name") == "requirements_traceability"), None)
    traceability = {
        "task_id_match": "unknown"
        if task_align is None
        else ("pass" if task_align.get("status") == "pass" else "fail"),
        "requirements_coverage": "unknown"
        if req_trace is None
        else (
            "pass"
            if req_trace.get("status") == "pass"
            else ("fail" if req_trace.get("status") == "fail" else "unknown")
        ),
        "issues": issues,
    }

    return derived_findings, policy, traceability


def main() -> int:
    args = parse_args()

    findings = parse_findings(args.finding)
    policy = {"artifact_integrity": "unknown", "eval_commands": "unknown"}
    traceability = {"task_id_match": "unknown", "requirements_coverage": "unknown", "issues": []}

    if args.audit_results:
        results_path = Path(args.audit_results).resolve()
        if not results_path.is_file():
            raise SystemExit(f"error: audit results not found: {results_path}")
        derived_findings, policy, traceability = derive_from_results(results_path)
        findings.extend(derived_findings)

    required_actions = [a.strip() for a in args.required_action if a and a.strip()]
    if args.gate in {"fail", "needs-human"} and not findings:
        raise SystemExit("error: fail/needs-human gate requires at least one finding")

    risk_reasons = [f["details"] for f in findings]

    payload = {
        "task_id": args.task_id.strip(),
        "gate": args.gate,
        "risk": {
            "level": args.risk_level,
            "reasons": risk_reasons,
        },
        "findings": findings,
        "policy": policy,
        "traceability": traceability,
        "required_actions": required_actions,
        "notes": args.notes.strip(),
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
