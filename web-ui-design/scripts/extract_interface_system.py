#!/usr/bin/env python3
"""Extract repeated frontend token patterns from a codebase."""

from __future__ import annotations

import argparse
import collections
import math
import pathlib
import re
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
RADIUS_PATTERN = re.compile(r"border-radius\s*:\s*([^;]+);", re.IGNORECASE)
CLASS_RADIUS_PATTERN = re.compile(r"\brounded(?:-[a-z0-9_[\]-]+)?\b")
CLASS_SHADOW_PATTERN = re.compile(r"\bshadow(?:-[a-z0-9_[\]-]+)?\b")
CLASS_BORDER_PATTERN = re.compile(r"\bborder(?:-[a-z0-9_[\]-]+)?\b")


def iter_ui_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") and part not in {".interface-design"} for part in path.parts):
            continue
        if path.suffix.lower() in UI_EXTENSIONS:
            yield path


def infer_base(px_counter: collections.Counter[float]) -> int:
    ints = [int(v) for v, n in px_counter.items() if v.is_integer() and n >= 2 and 1 <= v <= 128]
    if len(ints) < 2:
        return 4
    base = ints[0]
    for value in ints[1:]:
        base = math.gcd(base, value)
    if base in {4, 8}:
        return base
    if base % 4 == 0:
        return 4
    return 4


def infer_depth(border_count: int, shadow_count: int) -> str:
    if shadow_count == 0 or border_count >= shadow_count * 3:
        return "borders-only"
    if shadow_count <= border_count:
        return "subtle-shadows"
    return "layered-shadows"


def write_system_file(path: pathlib.Path, base: int, scale: list[int], depth: str) -> None:
    content = f"""# Design System

## Direction
Personality: Utility & Function
Foundation: neutral
Depth: {depth}

## Tokens
### Spacing
Base: {base}px
Scale: {", ".join(str(v) for v in scale)}

### Radius
Scale: 6px, 8px, 12px

## Patterns
### Button Primary
- Height: 36px
- Padding: 12px 16px
- Radius: 8px
- States: hover/focus/active/disabled

### Card Default
- Padding: 16px
- Radius: 8px
- Border/shadow: align with depth strategy

## Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| Extracted spacing/depth baseline | Seed from existing code patterns before manual refinement | YYYY-MM-DD |
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract design-token hints from frontend files.")
    parser.add_argument("--path", default=".", help="Project directory to scan.")
    parser.add_argument(
        "--write-system",
        action="store_true",
        help="Write a starter .interface-design/system.md file.",
    )
    parser.add_argument(
        "--system-file",
        default=".interface-design/system.md",
        help="System file path to write when --write-system is set.",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.path).resolve()
    files = list(iter_ui_files(root))
    if not files:
        print(f"No frontend files found under: {root}")
        return 0

    px_counter: collections.Counter[float] = collections.Counter()
    radius_counter: collections.Counter[str] = collections.Counter()
    border_count = 0
    shadow_count = 0

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1", errors="ignore")

        for raw in PX_PATTERN.findall(text):
            px_counter[float(raw)] += 1

        for raw in RADIUS_PATTERN.findall(text):
            radius_counter[raw.strip()] += 1

        border_count += text.count("border:")
        border_count += len(CLASS_BORDER_PATTERN.findall(text))

        shadow_count += text.count("box-shadow:")
        shadows = CLASS_SHADOW_PATTERN.findall(text)
        shadow_count += sum(1 for token in shadows if token not in {"shadow-none", "shadow-ring"})

        radius_counter.update(CLASS_RADIUS_PATTERN.findall(text))

    most_common_px = sorted(px_counter.items(), key=lambda item: (-item[1], item[0]))
    base = infer_base(px_counter)
    spacing_values = [
        int(v)
        for v, _ in most_common_px
        if v.is_integer() and base <= v <= 96 and int(v) % base == 0
    ]
    spacing_scale = sorted(set(spacing_values[:10]))
    if not spacing_scale:
        spacing_scale = [base, base * 2, base * 3, base * 4, base * 6, base * 8]

    depth = infer_depth(border_count, shadow_count)

    print(f"Scanned files: {len(files)}")
    print()
    print("Suggested system:")
    print(f"- Spacing base: {base}px")
    print(f"- Spacing scale: {', '.join(str(v) for v in spacing_scale)}")
    print(f"- Depth: {depth} (borders={border_count}, shadows={shadow_count})")

    top_px = ", ".join(f"{int(v) if v.is_integer() else v}px ({count})" for v, count in most_common_px[:12])
    if top_px:
        print(f"- Top px values: {top_px}")

    if radius_counter:
        common_radius = ", ".join(f"{k} ({v})" for k, v in radius_counter.most_common(8))
        print(f"- Radius signals: {common_radius}")

    if args.write_system:
        target = pathlib.Path(args.system_file)
        if not target.is_absolute():
            target = root / target
        write_system_file(target, base, spacing_scale, depth)
        print(f"\nWrote system file: {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
