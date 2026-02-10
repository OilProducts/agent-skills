#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


BookFormat = Literal["board-book", "picture-book", "early-reader", "chapter-book", "middle-grade"]


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "untitled"


@dataclass(frozen=True)
class BookMeta:
    title: str
    author: str | None
    age: str
    format: BookFormat
    page_count: int | None
    notes: str | None


def _default_sections(book_format: BookFormat) -> int | None:
    if book_format in ("board-book", "picture-book"):
        return 14 if book_format == "picture-book" else 10
    if book_format == "early-reader":
        return 12
    if book_format == "chapter-book":
        return 10
    if book_format == "middle-grade":
        return 20
    return None


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _scaffold_page_plan_table(sections: int) -> str:
    rows = "\n".join(
        f"| {i} |  |  |  |  |"
        for i in range(1, sections + 1)
    )
    return (
        "| Section | Goal (what changes) | Text (draft) | Illustration must show | Page-turn hook |\n"
        "|---:|---|---|---|---|\n"
        f"{rows}\n"
    )


def _manuscript_scaffold(book_format: BookFormat, sections: int | None) -> str:
    if book_format == "picture-book" and sections:
        parts = ["# Manuscript\n", "## Front matter\n", "- (optional) endpapers / title page / dedication\n"]
        for i in range(1, sections + 1):
            parts.append(f"\n## Spread {i}\n\n[Text]\n\n[Illustration note]\n")
        parts.append("\n## Back matter\n\n- (optional) author note / activities\n")
        return "".join(parts)
    return "# Manuscript\n\n[Draft here]\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a children's book project folder.")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--author", default=None, help="Author name (optional)")
    parser.add_argument(
        "--format",
        default="picture-book",
        choices=["board-book", "picture-book", "early-reader", "chapter-book", "middle-grade"],
        help="Book format",
    )
    parser.add_argument("--age", default="3-7", help='Target age range (e.g., "3-7")')
    parser.add_argument("--page-count", type=int, default=32, help="Page count (optional; default 32)")
    parser.add_argument("--notes", default=None, help="Any extra notes (optional)")
    parser.add_argument("--slug", default=None, help="Folder slug (defaults to slugified title)")
    parser.add_argument("--out", default="books", help='Output base directory (default "books")')
    parser.add_argument(
        "--sections",
        type=int,
        default=None,
        help="Number of sections/spreads/chapters to scaffold (defaults by format)",
    )
    args = parser.parse_args()

    book_format: BookFormat = args.format
    slug = args.slug or _slugify(args.title)
    base_dir = Path(args.out).expanduser().resolve()
    book_dir = base_dir / slug

    if book_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing folder: {book_dir}")

    book_dir.mkdir(parents=True, exist_ok=False)

    sections = args.sections if args.sections is not None else _default_sections(book_format)
    meta = BookMeta(
        title=args.title,
        author=args.author,
        age=args.age,
        format=book_format,
        page_count=args.page_count,
        notes=args.notes,
    )
    _write_text(book_dir / "book.json", json.dumps(asdict(meta), indent=2) + "\n")

    _write_text(
        book_dir / "book_brief.md",
        "# Book brief\n\n"
        "## Premise (one sentence)\n\n"
        "- \n\n"
        "## Audience + format\n\n"
        f"- Age: {meta.age}\n"
        f"- Format: {meta.format}\n\n"
        "## Promise of the book\n\n"
        "- (What feeling should remain?)\n\n"
        "## Characters\n\n"
        "- Lead:\n"
        "- Supporting:\n\n"
        "## Setting\n\n"
        "- \n\n"
        "## Constraints\n\n"
        "- Vocabulary:\n"
        "- Topics to avoid:\n",
    )

    _write_text(
        book_dir / "characters.md",
        "# Characters (book bible)\n\n"
        "For each character: want, fear, quirks, voice, visual anchors.\n\n"
        "## Lead\n\n"
        "- Name:\n"
        "- Want:\n"
        "- Fear:\n"
        "- Quirks:\n"
        "- Visual anchors (if illustrated):\n\n"
        "## Supporting\n\n"
        "- \n",
    )

    _write_text(
        book_dir / "outline.md",
        "# Outline\n\n"
        "Write beats first, then refine into a page/spread plan.\n\n"
        "1. Setup\n"
        "2. Problem\n"
        "3. Attempts (escalate)\n"
        "4. Lowest point\n"
        "5. Twist / new idea\n"
        "6. Resolution\n"
        "7. Cozy landing / final joke\n",
    )

    page_plan_body = (
        "# Page / spread plan\n\n"
        "Use **spreads** (two facing pages) for picture books.\n\n"
    )
    if sections:
        page_plan_body += _scaffold_page_plan_table(sections)
    else:
        page_plan_body += "- (Add your section-by-section plan here)\n"
    _write_text(book_dir / "page_plan.md", page_plan_body)

    _write_text(book_dir / "manuscript.md", _manuscript_scaffold(book_format, sections))

    _write_text(
        book_dir / "revision_notes.md",
        "# Revision notes\n\n"
        "## Pass 1: Structure + clarity\n\n"
        "- \n\n"
        "## Pass 2: Language + read-aloud\n\n"
        "- \n\n"
        "## Pass 3: Audience + sensitivity\n\n"
        "- \n",
    )

    _write_text(
        book_dir / "art_direction.md",
        "# Art direction (optional)\n\n"
        "If this book will be illustrated, define a consistent style lock.\n\n"
        "- Style keywords:\n"
        "- Palette:\n"
        "- Line/texture:\n"
        "- Camera language:\n"
        "- Continuity rules:\n",
    )

    _write_text(
        book_dir / "art_prompts.md",
        "# Art prompts (optional)\n\n"
        "## Style lock (repeat verbatim)\n\n"
        "- \n\n"
        "## Character sheet prompts\n\n"
        "- Lead turnaround + expressions:\n\n"
        "## Per-section prompts\n\n"
        "For each section/spread: scene goal, characters, setting, composition, continuity notes.\n",
    )

    print(f"Created: {book_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

