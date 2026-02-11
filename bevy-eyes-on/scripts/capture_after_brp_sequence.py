#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send BRP action/probe sequence and capture screenshot."
    )
    parser.add_argument(
        "--requests-jsonl",
        required=True,
        help="JSONL file with BRP action/probe steps (supports until-gated probes)",
    )
    parser.add_argument(
        "--brp-url", default="http://127.0.0.1:15702", help="BRP endpoint URL"
    )
    parser.add_argument(
        "--step-wait-ms",
        type=int,
        default=120,
        help="Default wait between action requests in milliseconds",
    )
    parser.add_argument(
        "--settle-ms",
        type=int,
        default=250,
        help="Wait after final request before capture in milliseconds",
    )
    parser.add_argument("--app", default="", help="App name for targeted capture")
    parser.add_argument(
        "--window-id", type=int, default=None, help="Window ID for targeted capture"
    )
    parser.add_argument(
        "--mode",
        default="temp",
        help="Mode forwarded to capture_after_delay.sh when --path is not set",
    )
    parser.add_argument("--path", default="", help="Explicit screenshot output path")
    parser.add_argument(
        "--debug-dir",
        default="",
        help="Optional directory for debug outputs (request/response logs)",
    )
    return parser.parse_args()


def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def load_jsonl_line(
    raw_line: str, line_no: int
) -> tuple[dict[str, Any], int, dict[str, Any] | None]:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("#"):
        return {}, -1, None

    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON on line {line_no}: {exc.msg}", 1)

    if not isinstance(obj, dict):
        fail(f"line {line_no} must be a JSON object", 1)

    until = obj.get("until")
    wait_ms = obj.get("wait_ms")
    has_probe = "probe" in obj
    has_body = "body" in obj
    if has_probe and has_body:
        fail(f"line {line_no} must include only one of 'body' or 'probe'", 1)
    if has_probe:
        body = obj["probe"]
        if wait_ms is None:
            wait_ms = 0
    elif has_body:
        body = obj["body"]
        if wait_ms is None:
            wait_ms = -1
    else:
        body = obj
        wait_ms = -1

    if not isinstance(body, dict):
        fail(f"line {line_no} body must be a JSON object", 1)

    if wait_ms != -1:
        if not isinstance(wait_ms, int) or wait_ms < 0:
            fail(f"line {line_no} wait_ms must be a non-negative integer", 1)

    if until is not None:
        if not isinstance(until, dict):
            fail(f"line {line_no} until must be an object", 1)
        if "path" not in until:
            fail(f"line {line_no} until.path is required", 1)
        if not isinstance(until["path"], str) or not until["path"].strip():
            fail(f"line {line_no} until.path must be a non-empty string", 1)
        has_equals = "equals" in until
        has_in = "in" in until
        if has_equals == has_in:
            fail(f"line {line_no} until requires exactly one of equals or in", 1)
        if has_in and not isinstance(until["in"], list):
            fail(f"line {line_no} until.in must be an array", 1)
        timeout_ms = until.get("timeout_ms", 5000)
        interval_ms = until.get("interval_ms", 100)
        if not isinstance(timeout_ms, int) or timeout_ms < 0:
            fail(f"line {line_no} until.timeout_ms must be a non-negative integer", 1)
        if not isinstance(interval_ms, int) or interval_ms <= 0:
            fail(f"line {line_no} until.interval_ms must be a positive integer", 1)
        until = {
            "path": until["path"],
            "equals": until.get("equals"),
            "in": until.get("in"),
            "timeout_ms": timeout_ms,
            "interval_ms": interval_ms,
        }

    return body, wait_ms, until


def post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            response_bytes = resp.read()
    except urllib.error.URLError as exc:
        fail(f"failed to call BRP endpoint '{url}': {exc}", 1)

    try:
        response_json = json.loads(response_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        fail("BRP response is not valid JSON", 1)

    if not isinstance(response_json, dict):
        fail("BRP response must be a JSON object", 1)
    return response_json


def lookup_path(data: Any, dotted_path: str) -> Any:
    current = data
    for segment in dotted_path.split("."):
        if not segment:
            fail(f"invalid path segment in '{dotted_path}'", 1)
        if isinstance(current, dict):
            if segment not in current:
                return None
            current = current[segment]
            continue
        if isinstance(current, list):
            if not segment.isdigit():
                return None
            idx = int(segment)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
            continue
        return None
    return current


def condition_matches(candidate: Any, until: dict[str, Any]) -> bool:
    if "equals" in until and until["equals"] is not None:
        return candidate == until["equals"]
    if "in" in until and until["in"] is not None:
        return candidate in until["in"]
    return False


def poll_until(
    url: str,
    probe_body: dict[str, Any],
    until: dict[str, Any],
    line_no: int,
    debug_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    timeout_s = until["timeout_ms"] / 1000.0
    interval_s = until["interval_ms"] / 1000.0
    deadline = time.monotonic() + timeout_s
    last_response: dict[str, Any] | None = None

    while True:
        response = post_json(url, probe_body)
        last_response = response
        if debug_records is not None:
            debug_records.append(
                {
                    "line": line_no,
                    "request": probe_body,
                    "response": response,
                    "poll": True,
                }
            )
        if "error" in response:
            fail(
                f"BRP response returned error at line {line_no} while polling: {response['error']}",
                1,
            )

        candidate = lookup_path(response, until["path"])
        if condition_matches(candidate, until):
            return response

        if time.monotonic() >= deadline:
            fail(
                (
                    f"line {line_no} until condition timed out after {until['timeout_ms']}ms "
                    f"(path={until['path']}, last_value={candidate!r})"
                ),
                1,
            )
        time.sleep(interval_s)


def run_capture(
    script_dir: Path,
    app: str,
    window_id: int | None,
    mode: str,
    output_path: str,
    debug_dir: str,
) -> str:
    delay_script = script_dir / "capture_after_delay.sh"
    cmd = ["bash", str(delay_script), "--delay-seconds", "0"]

    if output_path:
        cmd.extend(["--path", output_path])
    else:
        cmd.extend(["--mode", mode])

    if app:
        cmd.extend(["--app", app])
    if window_id is not None:
        cmd.extend(["--window-id", str(window_id)])
    if debug_dir:
        cmd.extend(["--debug-dir", debug_dir])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if debug_dir:
        out_path = Path(debug_dir) / "capture-wrapper.out"
        out_path.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        fail(stderr or "capture_after_delay.sh failed", 1)

    shot = ""
    for line in (proc.stdout or "").splitlines():
        candidate = line.strip()
        if candidate.startswith("/") and Path(candidate).exists():
            shot = candidate
            break
    if not shot:
        fail("capture command did not return a valid screenshot path", 1)
    return shot


def main() -> None:
    args = parse_args()

    requests_path = Path(args.requests_jsonl)
    if not requests_path.exists():
        fail(f"requests file not found: {requests_path}", 1)
    if args.step_wait_ms < 0:
        fail("--step-wait-ms must be a non-negative integer", 2)
    if args.settle_ms < 0:
        fail("--settle-ms must be a non-negative integer", 2)

    debug_dir_path: Path | None = None
    if args.debug_dir:
        debug_dir_path = Path(args.debug_dir)
        debug_dir_path.mkdir(parents=True, exist_ok=True)

    processed = 0
    debug_records: list[dict[str, Any]] = []
    with requests_path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            body, wait_ms, until = load_jsonl_line(raw_line, line_no)
            if wait_ms == -1 and not body:
                continue
            if wait_ms == -1:
                wait_ms = args.step_wait_ms

            if until is None:
                response = post_json(args.brp_url, body)
                processed += 1
                if debug_dir_path is not None:
                    debug_records.append(
                        {"line": line_no, "request": body, "response": response}
                    )

                if "error" in response:
                    if debug_dir_path is not None:
                        (debug_dir_path / "brp-responses.jsonl").write_text(
                            "\n".join(
                                json.dumps(rec, separators=(",", ":"))
                                for rec in debug_records
                            )
                            + ("\n" if debug_records else ""),
                            encoding="utf-8",
                        )
                    fail(
                        f"BRP response returned error at line {line_no}: {response['error']}",
                        1,
                    )
            else:
                poll_until(
                    url=args.brp_url,
                    probe_body=body,
                    until=until,
                    line_no=line_no,
                    debug_records=debug_records if debug_dir_path is not None else None,
                )
                processed += 1

            time.sleep(wait_ms / 1000.0)

    if processed == 0:
        fail("requests file did not contain any executable request lines", 1)

    if debug_dir_path is not None:
        (debug_dir_path / "brp-responses.jsonl").write_text(
            "\n".join(json.dumps(rec, separators=(",", ":")) for rec in debug_records)
            + ("\n" if debug_records else ""),
            encoding="utf-8",
        )

    time.sleep(args.settle_ms / 1000.0)
    shot = run_capture(
        script_dir=Path(__file__).resolve().parent,
        app=args.app,
        window_id=args.window_id,
        mode=args.mode,
        output_path=args.path,
        debug_dir=args.debug_dir,
    )
    print(shot)


if __name__ == "__main__":
    main()
