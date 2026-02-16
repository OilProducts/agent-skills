#!/usr/bin/env python3
"""Validate doer handoff.json shape."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_KEYS = {
    "task_id": str,
    "summary": str,
    "requirements_touched": list,
    "files_touched": list,
    "assumptions": list,
    "smoke_checks": list,
    "notes": str,
}

ALLOWED_STATUSES = {"pass", "fail", "skip", "unknown"}
REQUIREMENT_ID_PATTERN = re.compile(r"^(RQ|NFR|ASMP|ADR)-\d{3,4}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate doer handoff artifact")
    parser.add_argument("--input", required=True, help="Path to handoff.json")
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

    for key, expected_type in REQUIRED_KEYS.items():
        if key not in data:
            return fail(f"missing key: {key}")
        if not isinstance(data[key], expected_type):
            return fail(f"key '{key}' must be {expected_type.__name__}")

    for key in ("requirements_touched", "files_touched", "assumptions"):
        values = data[key]
        if any(not isinstance(v, str) for v in values):
            return fail(f"all values in '{key}' must be strings")

    for i, requirement in enumerate(data["requirements_touched"]):
        if not REQUIREMENT_ID_PATTERN.match(requirement.strip()):
            return fail(
                f"requirements_touched[{i}] must match ID pattern "
                f"(RQ|NFR|ASMP|ADR)-<3-4 digits>: {requirement!r}"
            )

    for i, check in enumerate(data["smoke_checks"]):
        if not isinstance(check, dict):
            return fail(f"smoke_checks[{i}] must be object")
        if "command" not in check or "status" not in check:
            return fail(f"smoke_checks[{i}] must include command and status")
        if not isinstance(check["command"], str) or not check["command"].strip():
            return fail(f"smoke_checks[{i}].command must be non-empty string")
        if not isinstance(check["status"], str) or check["status"] not in ALLOWED_STATUSES:
            return fail(
                f"smoke_checks[{i}].status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}"
            )

    print("handoff is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
