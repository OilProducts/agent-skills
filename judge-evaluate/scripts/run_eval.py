#!/usr/bin/env python3
"""Run judge evaluation commands and emit structured results."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run evaluation commands and write eval-results JSON")
    parser.add_argument("--repo", required=True, help="Git repository root")
    parser.add_argument("--output", required=True, help="Path to eval-results.json")
    parser.add_argument("--log-dir", help="Optional log directory (default: <output-dir>/logs)")
    parser.add_argument("--command", action="append", default=[], help="Command to run (repeatable)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        raise SystemExit(f"error: repo not found: {repo}")

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_dir = Path(args.log_dir).resolve() if args.log_dir else output_path.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    passed = 0
    failed = 0

    for i, cmd in enumerate(args.command, start=1):
        cmd = cmd.strip()
        if not cmd:
            continue

        proc = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        status = "pass" if proc.returncode == 0 else "fail"
        if status == "pass":
            passed += 1
        else:
            failed += 1

        stdout_log = (log_dir / f"cmd-{i:02d}.stdout.log").resolve()
        stderr_log = (log_dir / f"cmd-{i:02d}.stderr.log").resolve()
        stdout_log.write_text(proc.stdout, encoding="utf-8")
        stderr_log.write_text(proc.stderr, encoding="utf-8")

        results.append(
            {
                "command": cmd,
                "status": status,
                "exit_code": proc.returncode,
                "stdout_log": str(stdout_log),
                "stderr_log": str(stderr_log),
            }
        )

    payload = {
        "repo": str(repo),
        "results": results,
        "summary": {
            "commands": len(results),
            "passed": passed,
            "failed": failed,
        },
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
