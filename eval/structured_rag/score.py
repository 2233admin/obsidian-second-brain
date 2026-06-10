"""Evaluation metrics and report rendering."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .queries import EvalQuery


def score_results(queries: list[EvalQuery], rows: list[dict]) -> dict:
    expected = {query.id: set(query.expected_sources) for query in queries}
    by_runner: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_runner[row.get("runner", "unknown")].append(row)

    summary = {}
    for runner, runner_rows in by_runner.items():
        ok_rows = [row for row in runner_rows if row.get("status") == "ok"]
        skipped_rows = [row for row in runner_rows if row.get("status") == "skipped"]
        hit1 = 0
        hit5 = 0
        recall_sum = 0.0
        precision_sum = 0.0
        for row in ok_rows:
            exp = expected.get(row["query_id"], set())
            paths = [_result_path(result) for result in row.get("results", [])[:5]]
            paths = [path for path in paths if path]
            if exp:
                hit1 += int(bool(paths[:1] and paths[0] in exp))
                hit5 += int(bool(set(paths) & exp))
                recall_sum += len(set(paths) & exp) / len(exp)
                precision_sum += len(set(paths) & exp) / max(len(paths), 1)
        denom = max(len(ok_rows), 1)
        summary[runner] = {
            "queries": len(runner_rows),
            "ok": len(ok_rows),
            "skipped": len(skipped_rows),
            "hit@1": hit1 / denom,
            "hit@5": hit5 / denom,
            "source_recall@5": recall_sum / denom,
            "citation_precision": precision_sum / denom,
        }
    return summary


def render_report(queries: list[EvalQuery], rows: list[dict], out_path: Path) -> None:
    summary = score_results(queries, rows)
    lines = ["# Structured RAG Evaluation Report", ""]
    lines.append(
        "| Runner | Queries | OK | Skipped | hit@1 | hit@5 | "
        "source_recall@5 | citation_precision |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for runner, data in sorted(summary.items()):
        lines.append(
            f"| {runner} | {data['queries']} | {data['ok']} | {data['skipped']} | "
            f"{data['hit@1']:.2f} | {data['hit@5']:.2f} | "
            f"{data['source_recall@5']:.2f} | {data['citation_precision']:.2f} |"
        )

    lines.extend(["", "## Per-query Results", ""])
    by_query: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_query[row["query_id"]].append(row)
    for query in queries:
        lines.append(f"### {query.id}")
        lines.append("")
        lines.append(f"Question: {query.question}")
        lines.append("")
        lines.append(f"Expected: {', '.join(query.expected_sources) or '(none)'}")
        for row in by_query.get(query.id, []):
            lines.append("")
            lines.append(f"- {row.get('runner')}: {row.get('status')}")
            if row.get("reason"):
                lines.append(f"  Reason: {row['reason']}")
            for result in row.get("results", [])[:5]:
                path = _result_path(result)
                score = result.get("score", "")
                lines.append(f"  - {path} ({score})")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _result_path(result: dict) -> str:
    document = result.get("document", result)
    return str(document.get("path", ""))
