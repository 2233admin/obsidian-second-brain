"""Optional TypeAgent Structured RAG runner adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess

from .dataset import DocumentSection, write_jsonl
from .queries import EvalQuery


def run_structured_rag(
    queries: list[EvalQuery],
    docs: list[DocumentSection],
    out_dir: Path,
    top_k: int = 5,
) -> list[dict]:
    """Run an external TypeAgent/KnowPro adapter if configured.

    Contract for TYPEAGENT_STRUCTURED_RAG_CMD:
    command <documents.jsonl> <queries.jsonl> <top_k>

    It must print JSONL rows with query_id, status, and results fields.
    """
    command = os.environ.get("TYPEAGENT_STRUCTURED_RAG_CMD")
    vendor = Path("tools/vendor/typeagent-knowpro")
    if not command and not vendor.exists():
        return [_skipped(query, "KnowPro runner not configured") for query in queries]

    docs_path = out_dir / "structured-rag-input.documents.jsonl"
    queries_path = out_dir / "structured-rag-input.queries.jsonl"
    write_jsonl(docs_path, docs)
    write_jsonl(
        queries_path,
        [
            {
                "id": query.id,
                "type": query.type,
                "question": query.question,
                "expected_sources": query.expected_sources,
            }
            for query in queries
        ],
    )

    if not command:
        return [
            _skipped(query, "KnowPro source exists but no runner command is configured")
            for query in queries
        ]

    proc = subprocess.run(
        [*shlex.split(command), str(docs_path), str(queries_path), str(top_k)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        return [_skipped(query, f"runner failed: {proc.stderr.strip()}") for query in queries]

    rows = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    seen = {row.get("query_id") for row in rows}
    rows.extend(
        _skipped(query, "runner returned no row")
        for query in queries
        if query.id not in seen
    )
    return rows


def _skipped(query: EvalQuery, reason: str) -> dict:
    return {
        "query_id": query.id,
        "runner": "structured-rag",
        "status": "skipped",
        "reason": reason,
        "question": query.question,
        "results": [],
    }
