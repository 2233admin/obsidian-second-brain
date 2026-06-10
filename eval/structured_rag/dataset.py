"""Build a sectioned markdown dataset from an Obsidian vault."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from pathlib import Path
from typing import Iterable


PROTECTED_PARTS = {
    ".obsidian",
    ".git",
    ".trash",
    "node_modules",
    ".venv",
    "__pycache__",
}

DEFAULT_INCLUDE_DIRS = {
    "wiki",
    "Research",
    "Knowledge",
    "Projects",
    "Ideas",
    "People",
    "Decisions",
    "20-Decisions",
    "30-Architecture",
    "40-Runbooks",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class DocumentSection:
    id: str
    path: str
    heading: str
    level: int
    start_line: int
    end_line: int
    text: str
    tags: list[str]
    mtime: float


def is_protected(path: Path) -> bool:
    return any(part in PROTECTED_PARTS for part in path.parts)


def should_include(path: Path, include_all: bool = False) -> bool:
    if path.suffix.lower() != ".md" or is_protected(path):
        return False
    if include_all:
        return True
    if len(path.parts) == 1:
        return path.name in {"_CLAUDE.md", "index.md", "README.md"}
    return path.parts[0] in DEFAULT_INCLUDE_DIRS


def extract_tags(text: str) -> list[str]:
    tags: set[str] = set()
    match = FRONTMATTER_RE.match(text)
    if match:
        frontmatter = match.group(1)
        for line in frontmatter.splitlines():
            stripped = line.strip()
            if stripped.startswith("tags:"):
                raw = stripped.removeprefix("tags:").strip().strip("[]")
                for tag in re.split(r"[, ]+", raw):
                    tag = tag.strip().strip("\"'")
                    if tag:
                        tags.add(tag)
    for tag in re.findall(r"(?<!\w)#([A-Za-z0-9_/-]+)", text):
        tags.add(tag)
    return sorted(tags)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def split_sections(vault_root: Path, path: Path) -> list[DocumentSection]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(vault_root).as_posix()
    tags = extract_tags(text)
    mtime = path.stat().st_mtime
    headings = list(HEADING_RE.finditer(text))

    if not headings:
        return [
            DocumentSection(
                id=f"{rel}#L1",
                path=rel,
                heading=path.stem,
                level=0,
                start_line=1,
                end_line=max(1, text.count("\n") + 1),
                text=text.strip(),
                tags=tags,
                mtime=mtime,
            )
        ]

    sections: list[DocumentSection] = []
    preamble = text[: headings[0].start()].strip()
    if preamble:
        sections.append(
            DocumentSection(
                id=f"{rel}#L1",
                path=rel,
                heading=path.stem,
                level=0,
                start_line=1,
                end_line=_line_number(text, headings[0].start()),
                text=preamble,
                tags=tags,
                mtime=mtime,
            )
        )

    for index, heading in enumerate(headings):
        start = heading.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        start_line = _line_number(text, start)
        end_line = _line_number(text, end)
        title = heading.group(2).strip()
        sections.append(
            DocumentSection(
                id=f"{rel}#L{start_line}",
                path=rel,
                heading=title,
                level=len(heading.group(1)),
                start_line=start_line,
                end_line=end_line,
                text=text[start:end].strip(),
                tags=tags,
                mtime=mtime,
            )
        )
    return sections


def build_documents(vault_root: Path, include_all: bool = False) -> list[DocumentSection]:
    root = vault_root.resolve()
    docs: list[DocumentSection] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if should_include(rel, include_all=include_all):
            docs.extend(section for section in split_sections(root, path) if section.text)
    return docs


def write_jsonl(path: Path, rows: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if hasattr(row, "__dataclass_fields__"):
                row = asdict(row)
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

