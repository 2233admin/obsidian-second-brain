"""CLI entry point for Structured RAG evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from .baseline import run_baseline
from .dataset import build_documents, write_jsonl
from .queries import load_queries
from .score import render_report
from .structured_runner import run_structured_rag


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate vault retrieval against Structured RAG.")
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--include-all", action="store_true")
    parser.add_argument("--skip-structured", action="store_true")
    args = parser.parse_args()

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = build_documents(args.vault, include_all=args.include_all)
    queries = load_queries(args.queries)

    write_jsonl(out_dir / "documents.jsonl", docs)
    baseline_rows = run_baseline(queries, docs, top_k=args.top_k)
    write_jsonl(out_dir / "baseline.jsonl", baseline_rows)

    rows = list(baseline_rows)
    if not args.skip_structured:
        structured_rows = run_structured_rag(queries, docs, out_dir, top_k=args.top_k)
        write_jsonl(out_dir / "structured-rag.jsonl", structured_rows)
        rows.extend(structured_rows)

    render_report(queries, rows, out_dir / "report.md")
    print(f"Wrote {len(docs)} documents, {len(queries)} queries, report: {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

