"""Lexical baseline retrieval for vault sections."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import math
import re

from .dataset import DocumentSection
from .queries import EvalQuery


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")
STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "what",
    "where",
    "which",
    "should",
    "does",
    "into",
    "from",
    "this",
    "your",
}


def tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def run_baseline(
    queries: list[EvalQuery],
    docs: list[DocumentSection],
    top_k: int = 5,
) -> list[dict]:
    doc_tokens = [tokenize(f"{doc.path} {doc.heading} {doc.text}") for doc in docs]
    doc_freq = Counter()
    for tokens in doc_tokens:
        doc_freq.update(set(tokens))
    total_docs = max(len(docs), 1)

    results: list[dict] = []
    for query in queries:
        q_tokens = tokenize(query.question)
        ranked = []
        for doc, tokens in zip(docs, doc_tokens, strict=True):
            score = _bm25_like(q_tokens, tokens, doc_freq, total_docs)
            if score > 0:
                ranked.append((score, doc))
        ranked.sort(key=lambda item: item[0], reverse=True)
        results.append(
            {
                "query_id": query.id,
                "runner": "baseline",
                "status": "ok",
                "question": query.question,
                "results": [
                    {
                        "score": round(score, 6),
                        "document": asdict(doc),
                    }
                    for score, doc in ranked[:top_k]
                ],
            }
        )
    return results


def _bm25_like(
    query_tokens: list[str],
    doc_tokens: list[str],
    doc_freq: Counter[str],
    total_docs: int,
) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for token in query_tokens:
        if token not in tf:
            continue
        idf = math.log((total_docs + 1) / (doc_freq[token] + 0.5))
        score += (tf[token] / (tf[token] + 1.2 * (0.25 + 0.75 * doc_len / 250))) * idf
    return score
