#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request
import uuid


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def http_json(method: str, url: str, payload: dict | None = None, timeout: float = 30.0) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def http_bytes(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_value(raw: str):
    low = raw.lower()
    if low in {"true", "false", "null"}:
        return json.loads(low)
    if raw and raw[0] in "[{\"-0123456789":
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return raw


def set_nested(obj: dict, key_path: list[str], value) -> None:
    cur = obj
    for i, key in enumerate(key_path):
        last = i == len(key_path) - 1
        if last:
            cur[key] = value
            return
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]


def apply_binding(prompt: dict, binding: str) -> None:
    if "=" not in binding:
        die(f"Invalid --set binding (missing '='): {binding}")
    lhs, rhs = binding.split("=", 1)
    parts = lhs.split(".")
    if len(parts) < 3:
        die(f"Invalid --set binding. Expected node.inputs.key=val, got: {binding}")
    node_id = parts[0]
    if node_id not in prompt:
        die(f"Node id not found in workflow: {node_id}")
    value = parse_value(rhs)
    set_nested(prompt[node_id], parts[1:], value)


def gather_images(history_entry: dict) -> list[dict]:
    outputs = history_entry.get("outputs", {})
    found: list[dict] = []
    for node_id, node_payload in outputs.items():
        images = node_payload.get("images", []) if isinstance(node_payload, dict) else []
        for i, img in enumerate(images):
            if not isinstance(img, dict):
                continue
            filename = img.get("filename")
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")
            if filename:
                found.append(
                    {
                        "node_id": node_id,
                        "index": i,
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type,
                    }
                )
    return found


def main() -> None:
    ap = argparse.ArgumentParser(description="Queue a ComfyUI workflow JSON and collect outputs.")
    ap.add_argument("--workflow", required=True, help="Path to workflow JSON (.api.json) used as /prompt payload")
    ap.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    ap.add_argument("--client-id", default=str(uuid.uuid4()))
    ap.add_argument("--set", dest="sets", action="append", default=[], help="Binding override: node.inputs.key=value")
    ap.add_argument("--out-dir", help="Directory to download output images")
    ap.add_argument("--timeout-sec", type=float, default=600.0)
    ap.add_argument("--poll-interval-sec", type=float, default=1.0)
    ap.add_argument("--request-timeout-sec", type=float, default=30.0)
    ap.add_argument("--save-final-workflow", help="Optional path to save post-binding workflow JSON")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wf_path = Path(args.workflow)
    if not wf_path.exists():
        die(f"Workflow file not found: {wf_path}")

    prompt = json.loads(wf_path.read_text(encoding="utf-8"))
    if not isinstance(prompt, dict):
        die("Workflow JSON must be an object keyed by node id")

    for binding in args.sets:
        apply_binding(prompt, binding)

    if args.save_final_workflow:
        out_wf = Path(args.save_final_workflow)
        out_wf.parent.mkdir(parents=True, exist_ok=True)
        out_wf.write_text(json.dumps(prompt, indent=2, sort_keys=True), encoding="utf-8")

    payload = {"prompt": prompt, "client_id": args.client_id}

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run": True,
                    "comfy_url": args.comfy_url,
                    "client_id": args.client_id,
                    "workflow": str(wf_path),
                    "set_count": len(args.sets),
                },
                ensure_ascii=True,
            )
        )
        return

    queue_url = f"{args.comfy_url.rstrip('/')}/prompt"
    try:
        queued = http_json("POST", queue_url, payload=payload, timeout=args.request_timeout_sec)
    except Exception as exc:  # noqa: BLE001
        die(f"Queue request failed: {exc}")

    prompt_id = queued.get("prompt_id")
    if prompt_id is None:
        die(f"Queue response missing prompt_id: {queued}")
    prompt_id = str(prompt_id)

    start = time.time()
    history_entry = None
    status = "unknown"

    while time.time() - start <= args.timeout_sec:
        hist_url = f"{args.comfy_url.rstrip('/')}/history/{urllib.parse.quote(prompt_id)}"
        try:
            hist = http_json("GET", hist_url, timeout=args.request_timeout_sec)
        except Exception as exc:  # noqa: BLE001
            die(f"History request failed: {exc}")

        entry = hist.get(prompt_id)
        if entry is None and len(hist) == 1:
            entry = next(iter(hist.values()))

        if entry:
            st = entry.get("status", {}) if isinstance(entry, dict) else {}
            if isinstance(st, dict):
                status = st.get("status_str", status)
                if st.get("completed") is True:
                    history_entry = entry
                    break
                if status in {"error", "failed"}:
                    die(f"Run failed with status={status}: {json.dumps(entry, ensure_ascii=True)[:800]}")
            if entry.get("outputs"):
                history_entry = entry
                break

        time.sleep(args.poll_interval_sec)

    if history_entry is None:
        die(f"Timed out waiting for prompt_id={prompt_id} (last_status={status})")

    images = gather_images(history_entry)
    downloads = []

    if args.out_dir and images:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for item in images:
            params = {
                "filename": item["filename"],
                "subfolder": item["subfolder"],
                "type": item["type"],
            }
            view_url = f"{args.comfy_url.rstrip('/')}/view?{urllib.parse.urlencode(params)}"
            data = http_bytes(view_url, timeout=args.request_timeout_sec)
            safe_name = f"{prompt_id}_{item['node_id']}_{item['index']}_{os.path.basename(item['filename'])}"
            path = out_dir / safe_name
            path.write_bytes(data)
            downloads.append(str(path))

    print(
        json.dumps(
            {
                "ok": True,
                "prompt_id": prompt_id,
                "status": status,
                "image_count": len(images),
                "images": images,
                "downloads": downloads,
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
