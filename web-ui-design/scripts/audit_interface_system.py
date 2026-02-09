#!/usr/bin/env python3
"""Audit frontend files against a saved .interface-design/system.md."""

from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass
from typing import Iterable

UI_EXTENSIONS = {
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".styl",
    ".pcss",
    ".html",
    ".tsx",
    ".jsx",
    ".ts",
    ".js",
    ".vue",
    ".svelte",
}

PX_PATTERN = re.compile(r"(?<![\w.-])(\d+(?:\.\d+)?)px\b")
DEPTH_PATTERN = re.compile(r"^Depth:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
SCALE_PATTERN = re.compile(r"^Scale:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
SHADOW_TOKEN = re.compile(r"\bshadow(?:-[a-z0-9_[\]-]+)?\b")


@dataclass
class SystemRules:
    spacing_scale: set[int]
    depth: str


def iter_ui_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") and part not in {".interface-design"} for part in path.parts):
            continue
        if path.suffix.lower() in UI_EXTENSIONS:
            yield path


def parse_scale(raw: str) -> set[int]:
    values: set[int] = set()
    for token in re.split(r"[,\s]+", raw):
        token = token.strip().replace("px", "")
        if not token:
            continue
        if token.isdigit():
            values.add(int(token))
    return values


def load_system_rules(system_path: pathlib.Path) -> SystemRules:
    text = system_path.read_text(encoding="utf-8")
    depth_match = DEPTH_PATTERN.search(text)
    depth = depth_match.group(1).strip().lower() if depth_match else "borders-only"

    scale_matches = SCALE_PATTERN.findall(text)
    spacing_scale: set[int] = set()
    for candidate in scale_matches:
        parsed = parse_scale(candidate)
        if parsed:
            spacing_scale = parsed
            break
    if not spacing_scale:
        spacing_scale = {4, 8, 12, 16, 24, 32}

    return SystemRules(spacing_scale=spacing_scale, depth=depth)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frontend code against system.md spacing/depth rules.")
    parser.add_argument("--path", default=".", help="Project directory to scan.")
    parser.add_argument(
        "--system",
        default=".interface-design/system.md",
        help="Path to design system file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=120,
        help="Maximum number of violations to print.",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.path).resolve()
    system = pathlib.Path(args.system)
    if not system.is_absolute():
        system = root / system

    if not system.exists():
        print(f"System file not found: {system}")
        print("Create one first (manual or with extract_interface_system.py --write-system).")
        return 1

    rules = load_system_rules(system)
    files = list(iter_ui_files(root))

    spacing_violations: list[str] = []
    depth_violations: list[str] = []

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1", errors="ignore")

        rel = file_path.relative_to(root)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for raw in PX_PATTERN.findall(line):
                value = float(raw)
                if not value.is_integer():
                    continue
                pixel = int(value)
                if 2 <= pixel <= 96 and pixel not in rules.spacing_scale:
                    spacing_violations.append(f"{rel}:{line_no} -> {pixel}px not in scale")

            if rules.depth == "borders-only":
                has_box_shadow = "box-shadow" in line
                tailwind_shadows = [s for s in SHADOW_TOKEN.findall(line) if s not in {"shadow-none", "shadow-ring"}]
                if has_box_shadow or tailwind_shadows:
                    depth_violations.append(f"{rel}:{line_no} -> shadow used but depth is borders-only")

    total = len(spacing_violations) + len(depth_violations)
    print(f"Scanned files: {len(files)}")
    print(f"Spacing scale: {sorted(rules.spacing_scale)}")
    print(f"Depth rule: {rules.depth}")
    print(f"Violations: {total}")

    if total == 0:
        print("No violations found.")
        return 0

    print("\nFindings:")
    count = 0
    for item in spacing_violations + depth_violations:
        if count >= args.limit:
            print(f"... truncated (limit={args.limit})")
            break
        print(f"- {item}")
        count += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
