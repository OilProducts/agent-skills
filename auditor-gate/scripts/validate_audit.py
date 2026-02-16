#!/usr/bin/env python3
"""Validate audit.json artifact for auditor-gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_GATES = {"pass", "fail", "needs-human"}
ALLOWED_RISK = {"low", "medium", "high"}
ALLOWED_POLICY = {"pass", "fail", "unknown"}
ALLOWED_TRACE = {"pass", "fail", "unknown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate audit artifact")
    parser.add_argument("--input", required=True, help="Path to audit.json")
    return parser.parse_args()


def fail(msg: str) -> int:
    print(f"error: {msg}")
    return 1


def main() -> int:
    args = parse_args()
    path = Path(args.input).resolve()
    if not path.is_file():
        return fail(f"input file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid JSON: {exc}")

    required = {
        "task_id": str,
        "gate": str,
        "risk": dict,
        "findings": list,
        "policy": dict,
        "traceability": dict,
        "required_actions": list,
        "notes": str,
    }
    for key, typ in required.items():
        if key not in data:
            return fail(f"missing key: {key}")
        if not isinstance(data[key], typ):
            return fail(f"key '{key}' must be {typ.__name__}")

    if data["gate"] not in ALLOWED_GATES:
        return fail(f"gate must be one of: {', '.join(sorted(ALLOWED_GATES))}")

    risk = data["risk"]
    if not isinstance(risk.get("level"), str) or risk["level"] not in ALLOWED_RISK:
        return fail(f"risk.level must be one of: {', '.join(sorted(ALLOWED_RISK))}")
    if not isinstance(risk.get("reasons"), list) or any(not isinstance(x, str) for x in risk["reasons"]):
        return fail("risk.reasons must be an array of strings")

    for i, item in enumerate(data["findings"]):
        if not isinstance(item, dict):
            return fail(f"findings[{i}] must be object")
        if "category" not in item or "details" not in item:
            return fail(f"findings[{i}] must include category and details")
        if not isinstance(item["category"], str) or not item["category"].strip():
            return fail(f"findings[{i}].category must be non-empty string")
        if not isinstance(item["details"], str) or not item["details"].strip():
            return fail(f"findings[{i}].details must be non-empty string")

    policy = data["policy"]
    for key in ("artifact_integrity", "eval_commands"):
        value = policy.get(key)
        if not isinstance(value, str) or value not in ALLOWED_POLICY:
            return fail(f"policy.{key} must be one of: {', '.join(sorted(ALLOWED_POLICY))}")

    traceability = data["traceability"]
    value = traceability.get("task_id_match")
    if not isinstance(value, str) or value not in ALLOWED_TRACE:
        return fail(f"traceability.task_id_match must be one of: {', '.join(sorted(ALLOWED_TRACE))}")
    req_value = traceability.get("requirements_coverage")
    if not isinstance(req_value, str) or req_value not in ALLOWED_TRACE:
        return fail(
            f"traceability.requirements_coverage must be one of: {', '.join(sorted(ALLOWED_TRACE))}"
        )
    issues = traceability.get("issues")
    if not isinstance(issues, list) or any(not isinstance(x, str) for x in issues):
        return fail("traceability.issues must be an array of strings")

    actions = data["required_actions"]
    if any(not isinstance(x, str) or not x.strip() for x in actions):
        return fail("required_actions must contain only non-empty strings")

    print("audit is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
