#!/usr/bin/env python3
"""Direct ComfyUI page runner scaffold for children's-book pipelines."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


PHASE_CHOICES = ("draft", "refine", "inpaint", "upscale_print")
PHASE_TO_DIR = {
    "draft": "draft",
    "refine": "refine",
    "inpaint": "final",
    "upscale_print": "final",
}


class ComfyApiError(RuntimeError):
    """Raised when ComfyUI returns an API error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one ComfyUI phase and persist artifacts for a single book page."
    )
    parser.add_argument("--book-id", required=True, help="Book identifier")
    parser.add_argument("--page", required=True, help="Page number or id (e.g. 7 or 0007)")
    parser.add_argument(
        "--phase",
        required=True,
        choices=PHASE_CHOICES,
        help="Workflow phase to execute",
    )
    parser.add_argument(
        "--renderspec",
        required=True,
        help="Path to renderspec.json for this page",
    )
    parser.add_argument(
        "--review",
        default=None,
        help="Optional review.json path; if omitted, uses page review.json if present",
    )
    parser.add_argument(
        "--source-image",
        default=None,
        help=(
            "Optional source image path for refine/inpaint/upscale. "
            "This is exposed as phase_inputs.source_image_*."
        ),
    )
    parser.add_argument(
        "--comfy-input-dir",
        default=None,
        help=(
            "Optional ComfyUI input directory path. If set with --source-image, "
            "the source image is copied there and source_image_name points to the copied filename."
        ),
    )
    parser.add_argument(
        "--comfy-url",
        default="http://127.0.0.1:8188",
        help="ComfyUI base URL",
    )
    parser.add_argument(
        "--workflow-dir",
        default="workflows",
        help="Directory containing <phase>.api.json and optional <phase>.bindings.json",
    )
    parser.add_argument(
        "--books-dir",
        default="books",
        help="Root books directory",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Max wait time for phase completion",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help="Polling interval while waiting for completion",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile workflow and write artifacts without queueing ComfyUI job",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def page_id(raw: str) -> str:
    raw = str(raw).strip()
    if raw.isdigit():
        return f"{int(raw):04d}"
    return raw


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def resolve_dotted(data: Any, dotted: str) -> Any:
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            continue
        raise KeyError(dotted)
    return cur


def interpolate_template(template: str, context: Dict[str, Any]) -> str:
    output = []
    i = 0
    while i < len(template):
        start = template.find("{", i)
        if start < 0:
            output.append(template[i:])
            break
        end = template.find("}", start + 1)
        if end < 0:
            output.append(template[i:])
            break
        output.append(template[i:start])
        token = template[start + 1 : end].strip()
        if token:
            try:
                value = resolve_dotted(context, token)
            except KeyError as exc:
                raise KeyError(f"template placeholder not found: {token}") from exc
            output.append(str(value))
        i = end + 1
    return "".join(output)


def set_node_input(workflow: Dict[str, Any], node_id: str, input_name: str, value: Any) -> None:
    node = workflow.get(str(node_id))
    if not isinstance(node, dict):
        raise KeyError(f"workflow node missing: {node_id}")
    inputs = node.setdefault("inputs", {})
    if not isinstance(inputs, dict):
        raise TypeError(f"workflow node {node_id} has non-dict inputs")
    inputs[input_name] = value


def apply_bindings(
    workflow: Dict[str, Any],
    bindings: Optional[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    applied = []
    if not bindings:
        return applied
    actions = bindings.get("actions", [])
    if not isinstance(actions, list):
        raise TypeError("bindings.actions must be a list")

    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            raise TypeError(f"binding action #{idx} is not an object")
        op = action.get("op", "set")
        node_id = str(action["node"])
        input_name = str(action["input"])
        optional = bool(action.get("optional", False))

        try:
            if op == "set":
                if "value" in action:
                    value = action["value"]
                elif "from" in action:
                    source = str(action["from"])
                    try:
                        value = resolve_dotted(context, source)
                    except KeyError:
                        if "default" in action:
                            value = action["default"]
                        else:
                            raise
                else:
                    raise ValueError(f"binding action #{idx}: set requires value or from")
            elif op == "format":
                template = str(action["template"])
                value = interpolate_template(template, context)
            else:
                raise ValueError(f"unsupported binding op: {op}")

            set_node_input(workflow, node_id=node_id, input_name=input_name, value=value)
            applied.append(
                {
                    "op": op,
                    "node": node_id,
                    "input": input_name,
                    "value_preview": (
                        value if isinstance(value, (int, float, bool)) else str(value)[:200]
                    ),
                }
            )
        except Exception as exc:
            if not optional:
                raise
            applied.append(
                {
                    "op": op,
                    "node": node_id,
                    "input": input_name,
                    "skipped_optional": True,
                    "reason": str(exc),
                }
            )
    return applied


class ComfyClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url=url, method=method.upper(), data=data, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ComfyApiError(f"{method} {path} failed: HTTP {exc.code} {details}") from exc
        except urllib.error.URLError as exc:
            raise ComfyApiError(f"{method} {path} failed: {exc.reason}") from exc
        if not body:
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ComfyApiError(f"{method} {path} returned non-JSON payload") from exc
        if not isinstance(parsed, dict):
            raise ComfyApiError(f"{method} {path} returned non-object JSON")
        return parsed

    def _request_bytes(self, path: str, query: Dict[str, str]) -> bytes:
        url = self.base_url + path + "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(url=url, method="GET")
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                return resp.read()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ComfyApiError(f"GET {path} failed: HTTP {exc.code} {details}") from exc
        except urllib.error.URLError as exc:
            raise ComfyApiError(f"GET {path} failed: {exc.reason}") from exc

    def queue_prompt(self, prompt: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        payload = {"prompt": prompt, "client_id": client_id}
        return self._request_json("POST", "/prompt", payload=payload)

    def get_prompt_history(self, prompt_id: str) -> Dict[str, Any]:
        return self._request_json("GET", f"/history/{prompt_id}")

    def fetch_output(self, ref: Dict[str, Any]) -> bytes:
        query = {
            "filename": str(ref.get("filename", "")),
            "subfolder": str(ref.get("subfolder", "")),
            "type": str(ref.get("type", "output")),
        }
        return self._request_bytes("/view", query=query)


def extract_history_record(history_payload: Dict[str, Any], prompt_id: str) -> Optional[Dict[str, Any]]:
    if prompt_id in history_payload and isinstance(history_payload[prompt_id], dict):
        return history_payload[prompt_id]
    if history_payload.get("prompt_id") == prompt_id:
        return history_payload
    return None


def collect_output_refs(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    outputs = record.get("outputs", {})
    if not isinstance(outputs, dict):
        return refs
    for node_id, node_output in outputs.items():
        if not isinstance(node_output, dict):
            continue
        for bucket in ("images", "gifs", "audio", "files"):
            items = node_output.get(bucket, [])
            if not isinstance(items, list):
                continue
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                filename = item.get("filename")
                if not filename:
                    continue
                refs.append(
                    {
                        "node_id": str(node_id),
                        "bucket": bucket,
                        "index": idx,
                        "filename": str(filename),
                        "subfolder": str(item.get("subfolder", "")),
                        "type": str(item.get("type", "output")),
                    }
                )
    return refs


def wait_for_completion(
    client: ComfyClient,
    prompt_id: str,
    timeout_seconds: int,
    poll_seconds: float,
) -> Dict[str, Any]:
    start = time.time()
    while True:
        history_payload = client.get_prompt_history(prompt_id)
        record = extract_history_record(history_payload, prompt_id)
        if record:
            status = record.get("status", {})
            refs = collect_output_refs(record)
            if refs:
                return record
            if isinstance(status, dict):
                status_str = str(status.get("status_str", "")).lower()
                if status.get("completed") is True or status_str in {"success", "succeeded", "completed"}:
                    return record
                if status_str in {"error", "failed"}:
                    raise RuntimeError(f"prompt {prompt_id} failed with status {status_str}")
        if (time.time() - start) > timeout_seconds:
            raise TimeoutError(f"timed out waiting for prompt {prompt_id}")
        time.sleep(poll_seconds)


def find_workflow_file(workflow_dir: Path, phase: str) -> Path:
    candidates = [
        workflow_dir / f"{phase}.api.json",
        workflow_dir / f"{phase}.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Missing workflow for phase {phase}. Expected one of: "
        + ", ".join(str(p) for p in candidates)
    )


def find_bindings_file(workflow_dir: Path, phase: str) -> Optional[Path]:
    candidate = workflow_dir / f"{phase}.bindings.json"
    if candidate.exists():
        return candidate
    return None


def ensure_page_layout(books_dir: Path, book_id: str, page_name: str) -> Path:
    page_dir = books_dir / book_id / "pages" / page_name
    for rel in ("draft", "selected", "refine", "final", "jobs"):
        (page_dir / rel).mkdir(parents=True, exist_ok=True)
    return page_dir


def maybe_copy_source_image(
    source_image: Optional[Path],
    comfy_input_dir: Optional[Path],
    page_name: str,
    phase: str,
) -> Dict[str, Any]:
    phase_inputs: Dict[str, Any] = {}
    if not source_image:
        return phase_inputs

    if not source_image.exists():
        raise FileNotFoundError(f"--source-image does not exist: {source_image}")

    source_abs = source_image.resolve()
    phase_inputs["source_image_path"] = str(source_abs)
    phase_inputs["source_image_stem"] = source_abs.stem
    phase_inputs["source_image_suffix"] = source_abs.suffix
    phase_inputs["source_image_name"] = source_abs.name

    if comfy_input_dir:
        comfy_input_dir.mkdir(parents=True, exist_ok=True)
        copied_name = f"{page_name}_{phase}_{source_abs.name}"
        copied_path = comfy_input_dir / copied_name
        shutil.copy2(source_abs, copied_path)
        phase_inputs["source_image_name"] = copied_name
        phase_inputs["source_image_copied_to"] = str(copied_path)

    return phase_inputs


def save_downloaded_files(
    client: ComfyClient,
    refs: List[Dict[str, Any]],
    output_dir: Path,
) -> List[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: List[str] = []
    for idx, ref in enumerate(refs, start=1):
        data = client.fetch_output(ref)
        filename = Path(ref["filename"]).name
        target = output_dir / f"{idx:03d}_{filename}"
        target.write_bytes(data)
        downloaded.append(str(target))
    return downloaded


def main() -> int:
    args = parse_args()

    books_dir = Path(args.books_dir)
    workflow_dir = Path(args.workflow_dir)
    renderspec_path = Path(args.renderspec)
    review_path = Path(args.review) if args.review else None
    source_image = Path(args.source_image) if args.source_image else None
    comfy_input_dir = Path(args.comfy_input_dir) if args.comfy_input_dir else None

    if not renderspec_path.exists():
        raise FileNotFoundError(f"--renderspec not found: {renderspec_path}")

    pid = page_id(args.page)
    page_dir = ensure_page_layout(books_dir=books_dir, book_id=args.book_id, page_name=pid)
    local_renderspec_path = page_dir / "renderspec.json"
    if local_renderspec_path.resolve() != renderspec_path.resolve():
        shutil.copy2(renderspec_path, local_renderspec_path)

    if review_path is None:
        implied_review = page_dir / "review.json"
        if implied_review.exists():
            review_path = implied_review

    render = read_json(local_renderspec_path)
    review = read_json(review_path) if review_path and review_path.exists() else None

    phase_inputs = maybe_copy_source_image(
        source_image=source_image,
        comfy_input_dir=comfy_input_dir,
        page_name=pid,
        phase=args.phase,
    )

    context: Dict[str, Any] = {
        "book_id": args.book_id,
        "page": pid,
        "phase": args.phase,
        "render": render,
        "review": review,
        "phase_inputs": phase_inputs,
        "paths": {
            "books_dir": str(books_dir.resolve()),
            "page_dir": str(page_dir.resolve()),
        },
        "runtime": {
            "timestamp_utc": now_utc_iso(),
            "client_id": str(uuid.uuid4()),
        },
    }

    workflow_file = find_workflow_file(workflow_dir=workflow_dir, phase=args.phase)
    bindings_file = find_bindings_file(workflow_dir=workflow_dir, phase=args.phase)
    workflow_payload = read_json(workflow_file)
    if not isinstance(workflow_payload, dict):
        raise TypeError(f"workflow must be a JSON object: {workflow_file}")

    compiled_workflow = copy.deepcopy(workflow_payload)
    applied_bindings: List[Dict[str, Any]] = []
    bindings_payload = None
    if bindings_file:
        bindings_payload = read_json(bindings_file)
        if not isinstance(bindings_payload, dict):
            raise TypeError(f"bindings must be a JSON object: {bindings_file}")
        applied_bindings = apply_bindings(compiled_workflow, bindings_payload, context)

    jobs_dir = page_dir / "jobs"
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    compiled_path = jobs_dir / f"{run_id}_{args.phase}_compiled_workflow.json"
    write_json(compiled_path, compiled_workflow)

    run_manifest: Dict[str, Any] = {
        "run_id": run_id,
        "book_id": args.book_id,
        "page": pid,
        "phase": args.phase,
        "renderspec_path": str(local_renderspec_path),
        "review_path": str(review_path) if review_path else None,
        "workflow_file": str(workflow_file),
        "bindings_file": str(bindings_file) if bindings_file else None,
        "compiled_workflow_path": str(compiled_path),
        "applied_bindings": applied_bindings,
        "phase_inputs": phase_inputs,
        "queued_at_utc": now_utc_iso(),
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        dry_manifest = jobs_dir / f"{run_id}_{args.phase}_dry_run.json"
        write_json(dry_manifest, run_manifest)
        print(f"[dry-run] compiled workflow written to {compiled_path}")
        print(f"[dry-run] manifest written to {dry_manifest}")
        return 0

    client = ComfyClient(base_url=args.comfy_url)
    queue_response = client.queue_prompt(
        prompt=compiled_workflow, client_id=context["runtime"]["client_id"]
    )
    prompt_id = queue_response.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise RuntimeError(f"ComfyUI did not return prompt_id: {queue_response}")

    history_record = wait_for_completion(
        client=client,
        prompt_id=prompt_id,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )
    refs = collect_output_refs(history_record)

    phase_dir_name = PHASE_TO_DIR.get(args.phase, args.phase)
    output_dir = page_dir / phase_dir_name
    downloaded_files = save_downloaded_files(client=client, refs=refs, output_dir=output_dir)

    run_manifest["prompt_id"] = prompt_id
    run_manifest["queue_response"] = queue_response
    run_manifest["history_record"] = history_record
    run_manifest["output_refs"] = refs
    run_manifest["downloaded_files"] = downloaded_files
    run_manifest["completed_at_utc"] = now_utc_iso()

    manifest_path = jobs_dir / f"{run_id}_{args.phase}_{prompt_id}.json"
    write_json(manifest_path, run_manifest)

    print(f"phase={args.phase} prompt_id={prompt_id}")
    print(f"downloaded_files={len(downloaded_files)}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
