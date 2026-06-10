# Structured RAG Evaluation

This harness compares the existing vault-first lexical retrieval used by
`obsidian-second-brain` with an optional TypeAgent KnowPro / Structured RAG
runner.

The vault markdown remains the source of truth. Any Structured RAG index is a
rebuildable cache used only for evaluation until its results beat the baseline.

## Quick start

```powershell
py -m eval.structured_rag.run_eval `
  --vault examples/sample-vault `
  --queries eval/structured-rag/datasets/queries.example.yaml `
  --out eval/structured-rag/results/example
```

The baseline always runs. The Structured RAG runner is optional and is skipped
unless either of these is available:

- `TYPEAGENT_STRUCTURED_RAG_CMD`: command that accepts the dataset JSON path and
  query JSON path, then prints JSON results.
- `tools/vendor/typeagent-knowpro/`: pinned TypeAgent KnowPro source snapshot
  with a compatible runner installed by a later integration step.

## Output

- `documents.jsonl`: sectioned markdown corpus.
- `baseline.jsonl`: baseline retrieval results.
- `structured-rag.jsonl`: TypeAgent runner results, or skipped status.
- `report.md`: metrics and notable failures.

