#!/usr/bin/env python3
"""Write doer handoff.json from repo state and explicit metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

ALLOWED_STATUSES = {"pass", "fail", "skip", "unknown"}


@dataclass(frozen=True)
class SmokeCheck:
    command: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write doer handoff artifact")
    parser.add_argument("--repo", required=True, help="Git repository root")
    parser.add_argument("--task-id", required=True, help="Task id (for example TASK-0042)")
    parser.add_argument("--summary", required=True, help="Short implementation summary")
    parser.add_argument("--output", required=True, help="Output handoff JSON path")
    parser.add_argument(
        "--requirement",
        action="append",
        default=[],
        help="Requirement ID touched by this change (repeatable, for example RQ-0102)",
    )
    parser.add_argument("--assumption", action="append", default=[], help="Assumption id/text (repeatable)")
    parser.add_argument(
        "--smoke-check",
        action="append",
        default=[],
        help="Smoke check in format '<status>::<command>' (repeatable)",
    )
    parser.add_argument("--notes", default="", help="Optional short note")
    return parser.parse_args()


def run_git_status(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout


def parse_touched_files(status_output: str) -> list[str]:
    files: set[str] = set()
    for raw in status_output.splitlines():
        if not raw:
            continue
        path_part = raw[3:].strip()
        if not path_part:
            continue
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1].strip()
        files.add(path_part)
    return sorted(files)


def parse_smoke_checks(raw_items: list[str]) -> list[SmokeCheck]:
    checks: list[SmokeCheck] = []
    for item in raw_items:
        if "::" not in item:
            raise ValueError(f"Invalid --smoke-check '{item}'. Expected '<status>::<command>'.")
        status, command = item.split("::", 1)
        status = status.strip().lower()
        command = command.strip()
        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid smoke check status '{status}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}."
            )
        if not command:
            raise ValueError(f"Invalid --smoke-check '{item}'. Command cannot be empty.")
        checks.append(SmokeCheck(command=command, status=status))
    return checks


def main() -> int:
    args = parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        raise SystemExit(f"error: repo not found: {repo}")

    try:
        subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"error: not a git repository: {repo}") from exc

    try:
        smoke_checks = parse_smoke_checks(args.smoke_check)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    status_output = run_git_status(repo)
    files_touched = parse_touched_files(status_output)

    assumptions = [a.strip() for a in args.assumption if a and a.strip()]
    requirements_touched = [r.strip() for r in args.requirement if r and r.strip()]

    payload = {
        "task_id": args.task_id.strip(),
        "summary": args.summary.strip(),
        "requirements_touched": requirements_touched,
        "files_touched": files_touched,
        "assumptions": assumptions,
        "smoke_checks": [{"command": c.command, "status": c.status} for c in smoke_checks],
        "notes": args.notes.strip(),
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
