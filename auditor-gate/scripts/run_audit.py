#!/usr/bin/env python3
"""Collect audit evidence for auditor-gate."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run audit checks and emit audit-results JSON")
    parser.add_argument("--repo", required=True, help="Git repository root")
    parser.add_argument("--handoff", required=True, help="Path to handoff.json")
    parser.add_argument("--verdict", required=True, help="Path to verdict.json")
    parser.add_argument("--output", required=True, help="Path to audit-results.json")
    parser.add_argument("--log-dir", help="Optional log directory (default: <output-dir>/logs)")
    parser.add_argument("--command", action="append", default=[], help="Audit command to run (repeatable)")
    return parser.parse_args()


def status(ok: bool) -> str:
    return "pass" if ok else "fail"


def normalize_id_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if value:
            values.append(value)
    return values


def main() -> int:
    args = parse_args()

    repo = Path(args.repo).resolve()
    handoff_path = Path(args.handoff).resolve()
    verdict_path = Path(args.verdict).resolve()
    output_path = Path(args.output).resolve()

    if not repo.is_dir():
        raise SystemExit(f"error: repo not found: {repo}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = Path(args.log_dir).resolve() if args.log_dir else output_path.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []

    checks.append(
        {
            "name": "handoff_present",
            "status": status(handoff_path.is_file()),
            "details": str(handoff_path),
        }
    )
    checks.append(
        {
            "name": "verdict_present",
            "status": status(verdict_path.is_file()),
            "details": str(verdict_path),
        }
    )

    handoff_data = None
    verdict_data = None

    if handoff_path.is_file():
        try:
            handoff_data = json.loads(handoff_path.read_text(encoding="utf-8"))
            checks.append(
                {
                    "name": "handoff_json_valid",
                    "status": "pass",
                    "details": "handoff parsed",
                }
            )
        except json.JSONDecodeError as exc:
            checks.append(
                {
                    "name": "handoff_json_valid",
                    "status": "fail",
                    "details": f"invalid JSON: {exc}",
                }
            )

    if verdict_path.is_file():
        try:
            verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
            checks.append(
                {
                    "name": "verdict_json_valid",
                    "status": "pass",
                    "details": "verdict parsed",
                }
            )
        except json.JSONDecodeError as exc:
            checks.append(
                {
                    "name": "verdict_json_valid",
                    "status": "fail",
                    "details": f"invalid JSON: {exc}",
                }
            )

    if handoff_data is not None and verdict_data is not None:
        handoff_task = str(handoff_data.get("task_id", "")).strip()
        verdict_task = str(verdict_data.get("task_id", "")).strip()
        aligned = bool(handoff_task) and handoff_task == verdict_task
        details = (
            f"handoff task_id={handoff_task}, verdict task_id={verdict_task}"
            if handoff_task or verdict_task
            else "task_id missing in one or both artifacts"
        )
        checks.append(
            {
                "name": "task_id_alignment",
                "status": status(aligned),
                "details": details,
            }
        )

        requirements_touched = set(normalize_id_list(handoff_data.get("requirements_touched")))
        requirements_checked = set(normalize_id_list(verdict_data.get("requirements_checked")))
        requirements_missing = set(normalize_id_list(verdict_data.get("requirements_missing")))

        if not requirements_touched:
            checks.append(
                {
                    "name": "requirements_traceability",
                    "status": "unknown",
                    "details": "handoff has no requirements_touched values",
                }
            )
        elif not requirements_checked and not requirements_missing:
            checks.append(
                {
                    "name": "requirements_traceability",
                    "status": "fail",
                    "details": "verdict has no requirements_checked/requirements_missing values",
                }
            )
        else:
            uncovered = sorted(requirements_touched - requirements_checked - requirements_missing)
            if uncovered:
                checks.append(
                    {
                        "name": "requirements_traceability",
                        "status": "fail",
                        "details": f"requirements without verdict coverage: {', '.join(uncovered)}",
                    }
                )
            else:
                checks.append(
                    {
                        "name": "requirements_traceability",
                        "status": "pass",
                        "details": "all touched requirements accounted for in verdict",
                    }
                )

    commands: list[dict] = []
    for i, raw_cmd in enumerate(args.command, start=1):
        cmd = raw_cmd.strip()
        if not cmd:
            continue

        proc = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout_log = (log_dir / f"cmd-{i:02d}.stdout.log").resolve()
        stderr_log = (log_dir / f"cmd-{i:02d}.stderr.log").resolve()
        stdout_log.write_text(proc.stdout, encoding="utf-8")
        stderr_log.write_text(proc.stderr, encoding="utf-8")

        commands.append(
            {
                "command": cmd,
                "status": status(proc.returncode == 0),
                "exit_code": proc.returncode,
                "stdout_log": str(stdout_log),
                "stderr_log": str(stderr_log),
            }
        )

    checks_failed = sum(1 for item in checks if item["status"] == "fail")
    commands_failed = sum(1 for item in commands if item["status"] == "fail")

    payload = {
        "repo": str(repo),
        "handoff": str(handoff_path),
        "verdict": str(verdict_path),
        "checks": checks,
        "commands": commands,
        "summary": {
            "checks": len(checks),
            "checks_failed": checks_failed,
            "commands": len(commands),
            "commands_failed": commands_failed,
        },
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
