"""Query dataset loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class EvalQuery:
    id: str
    type: str
    question: str
    expected_sources: list[str]


def load_queries(path: Path) -> list[EvalQuery]:
    """Load the small YAML subset used by this harness.

    The file format is intentionally simple to avoid adding a PyYAML dependency
    to the project just for evaluation fixtures.
    """
    text = path.read_text(encoding="utf-8")
    items: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_list: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- id:"):
            if current:
                items.append(current)
            current = {"id": _value(stripped.removeprefix("- id:"))}
            current_list = None
            continue
        if current is None:
            continue
        if re.match(r"^[A-Za-z_]+:", stripped):
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current[key] = _value(value)
                current_list = None
            else:
                current[key] = []
                current_list = key
            continue
        if stripped.startswith("- ") and current_list:
            casted = current[current_list]
            if isinstance(casted, list):
                casted.append(_value(stripped[2:]))

    if current:
        items.append(current)

    queries: list[EvalQuery] = []
    for item in items:
        queries.append(
            EvalQuery(
                id=str(item["id"]),
                type=str(item.get("type", "factual")),
                question=str(item["question"]),
                expected_sources=[str(x) for x in item.get("expected_sources", [])],
            )
        )
    return queries


def _value(raw: str) -> str:
    return raw.strip().strip("\"'")

