#!/usr/bin/env python3
"""Validate verdict.json shape for judge-evaluate."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ALLOWED_VERDICTS = {"pass", "reject", "needs-human"}
REQUIREMENT_ID_PATTERN = re.compile(r"^(RQ|NFR|ASMP|ADR)-\d{3,4}$")
REQUIRED_KEYS = {
    "task_id": str,
    "verdict": str,
    "reasons": list,
    "required_changes": list,
    "suggested_tests": list,
    "requirements_checked": list,
    "requirements_missing": list,
    "notes": str,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate verdict artifact")
    parser.add_argument("--input", required=True, help="Path to verdict.json")
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

    for key, expected in REQUIRED_KEYS.items():
        if key not in data:
            return fail(f"missing key: {key}")
        if not isinstance(data[key], expected):
            return fail(f"key '{key}' must be {expected.__name__}")

    if data["verdict"] not in ALLOWED_VERDICTS:
        return fail(f"verdict must be one of: {', '.join(sorted(ALLOWED_VERDICTS))}")

    for i, reason in enumerate(data["reasons"]):
        if not isinstance(reason, dict):
            return fail(f"reasons[{i}] must be object")
        if "check" not in reason or "details" not in reason:
            return fail(f"reasons[{i}] must include check and details")
        if not isinstance(reason["check"], str) or not reason["check"].strip():
            return fail(f"reasons[{i}].check must be non-empty string")
        if not isinstance(reason["details"], str) or not reason["details"].strip():
            return fail(f"reasons[{i}].details must be non-empty string")

    for key in ("required_changes", "suggested_tests", "requirements_checked", "requirements_missing"):
        if any(not isinstance(v, str) or not v.strip() for v in data[key]):
            return fail(f"all values in '{key}' must be non-empty strings")

    for key in ("requirements_checked", "requirements_missing"):
        for i, requirement in enumerate(data[key]):
            if not REQUIREMENT_ID_PATTERN.match(requirement.strip()):
                return fail(
                    f"{key}[{i}] must match ID pattern "
                    f"(RQ|NFR|ASMP|ADR)-<3-4 digits>: {requirement!r}"
                )

    print("verdict is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
