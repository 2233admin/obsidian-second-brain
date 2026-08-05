"""OpenCLI adapter source. Runs opencli search commands for web/academic research.

Adds a third mode to /research alongside:
  - paid: Perplexity Sonar
  - free: DuckDuckGo/SearXNG + Wikipedia + HN + arXiv + ...

This module calls `opencli list` once, parses the plain-text adapter list,
and wires search commands into the existing Result/aggregator pipeline.
No API keys needed - opencli uses the user's installed adapters.

Auto-discovered adapters include:
  brave, google, duckduckgo (web search)
  arxiv, google-scholar, baidu-scholar, openalex, dblp, pubmed (academic)
  wikipedia, wikidata (knowledge base)
  hackernews, reddit (discussion)
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from typing import Any

from .. import cache
from ..result import Result

# Adapters that are safe and useful for automated research.
# Discovered dynamically from `opencli list` output.
# Format: adapter_name -> (description snippet, is_academic, is_web)
_KNOWN_ADAPTERS: dict[str, tuple[str, bool, bool]] = {
    "arxiv":            ("Search arXiv papers",             True,  False),
    "google-scholar":   ("Search Google Scholar",           True,  False),
    "baidu-scholar":   ("百度学术搜索",                    True,  False),
    "openalex":         ("OpenAlex academic",               True,  False),
    "dblp":             ("Search dblp",                    True,  False),
    "pubmed":           ("PubMed medical",                  True,  False),
    "openreview":       ("OpenReview papers",               True,  False),
    "brave":            ("Search Brave Search",             False, True),
    "google":           ("Search Google",                   False, True),
    "duckduckgo":       ("Search DuckDuckGo",               False, True),
    "wikipedia":        ("Search Wikipedia",                False, True),
    "wikidata":        ("Search Wikidata",                  False, True),
    "hackernews":      ("Hacker News",                    False, True),
    "reddit":           ("Search Reddit",                   False, True),
    "youtube":         ("Search YouTube",                  False, True),
}


# ── opencli invocation helpers ────────────────────────────────────────────────


def _run(args: list[str], timeout: int = 30) -> str:
    """Run opencli and return stdout. Returns "" on any failure."""
    try:
        exe = shutil.which("opencli") or "opencli"
        r = subprocess.run(
            [exe] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError, Exception):
        return ""


def _discover() -> dict[str, bool | None]:
    """Call `opencli list`, parse plain-text output, return {adapter_name: is_public?}.

    Parsing strategy: adapters have 2 leading spaces; commands have 4.
    Each adapter block starts with 2-space name and contains 4-space `search` lines.
    """
    out = _run(["list"])
    if not out:
        return {}

    lines = out.split("\n")
    result: dict[str, bool | None] = {}
    current_adapter: str | None = None

    for line in lines:
        stripped = line.strip()
        leading = len(line) - len(stripped)

        if leading == 2 and stripped:
            # Adapter name line
            current_adapter = stripped.lower()
        elif leading == 4 and current_adapter:
            # Command line
            if stripped.lower().startswith("search"):
                result[current_adapter] = "[public]" in stripped
            elif stripped.startswith("search [") and stripped.endswith("] —"):
                result[current_adapter] = "[public]" in stripped

    return result


# ── result parsers ──────────────────────────────────────────────────────────


def _parse_json(out: str, source: str) -> list[Result]:
    """Try JSON parse, then YAML/simple-text fallback."""
    # Try JSON first
    try:
        data = json.loads(out)
        items = data if isinstance(data, list) else data.get("results", data.get("items", []))
        return _build_results(items, source)
    except Exception:
        pass
    # arxiv emits YAML - try simple line-based parse
    return _parse_yaml_fallback(out, source)


def _parse_yaml_fallback(out: str, source: str) -> list[Result]:
    """Parse YAML-like output from arxiv and similar adapters.
    
    arxiv search emits YAML. This parses it into a list of dicts
    without a YAML library dependency.
    """
    results: list[Result] = []
    current: dict[str, str] = {}
    for raw_line in out.splitlines():
        line = raw_line.rstrip()
        # Get indent level
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent > 4:
            continue
        if not stripped:
            continue
        # List item marker at indent 0
        if stripped.startswith("- "):
            if current:
                results.append(current)
            current = {}
            stripped = stripped[2:]
        if not stripped.startswith("#"):
            if ": " in stripped:
                key, _, val = stripped.partition(": ")
                current[key.strip()] = val.strip()
    if current:
        results.append(current)
    return _build_results(results[:10], source)


def _build_results(items: list, source: str) -> list[Result]:
    results: list[Result] = []
    for i in items:
        if not isinstance(i, dict):
            continue
        if not i.get("title") and not i.get("url"):
            continue
        authors_raw = i.get("authors", [])
        if isinstance(authors_raw, list):
            authors = [str(a.get("name", a) if isinstance(a, dict) else str(a)) for a in authors_raw]
        else:
            authors = []
        year = None
        pub = i.get("published") or i.get("date", "")
        if isinstance(pub, str) and len(pub) >= 4:
            try:
                year = int(pub[:4])
            except ValueError:
                pass
        results.append(Result(
            source=source,
            title=str(i.get("title", "")),
            url=str(i.get("url", i.get("link", ""))),
            snippet=i.get("snippet") or i.get("description"),
            abstract=i.get("abstract"),
            authors=authors,
            year=year,
        ))
    return results


def _search_adapter(adapter: str, query: str, n: int = 10) -> list[Result]:
    """Run `opencli <adapter> search <query>` and parse results."""
    out = _run([adapter, "search", query])
    if not out:
        return []
    results = _parse_json(out, f"opencli-{adapter}")
    return results[:n]


# ── public source class ───────────────────────────────────────────────────


class OpenCLISource:
    """Aggregates multiple OpenCLI search adapters into one SourceClient.

    Usage:
        src = OpenCLISource()                    # auto-discover
        src = OpenCLISource(adapters=["arxiv", "brave", "google-scholar"])
        src = OpenCLISource(mode="academic")      # arxiv/gscholar/dblp/openalex only
        src = OpenCLISource(mode="web")           # brave/google/ddg only
        results = src.search("machine learning")
        print(src.adapters())   # list of active adapters
    """

    name = "opencli"

    # Mode presets
    PRESETS: dict[str, list[str]] = {
        "academic": ["arxiv", "google-scholar", "openalex", "dblp", "pubmed", "openreview", "baidu-scholar"],
        "web":     ["brave", "google", "duckduckgo", "wikipedia", "hackernews", "reddit"],
        "all":     list(_KNOWN_ADAPTERS),
    }

    def __init__(
        self,
        adapters: list[str] | None = None,
        mode: str = "academic+web",
        n: int = 8,
    ) -> None:
        """
        Args:
            adapters: explicit list of opencli adapter names. None = auto-discover.
            mode: preset filter ("academic", "web", "all"). Only used when adapters=None.
            n: results per adapter.
        """
        self._n = n
        if adapters is not None:
            self._adapters = adapters
        else:
            self._adapters = self._auto_discover(mode)

    def _auto_discover(self, mode: str = "academic+web") -> list[str]:
        """Find adapters from `opencli list` output that have a search command."""
        discovered = _discover()
        preset = set(self.PRESETS.get(mode, self.PRESETS["academic"] + self.PRESETS["web"]))

        selected: list[str] = []
        for adapter, is_public in discovered.items():
            if adapter not in _KNOWN_ADAPTERS:
                continue
            if adapter not in preset:
                continue
            selected.append(adapter)

        # Fallback: include any known adapter even if not in preset (just in case)
        for adapter in _KNOWN_ADAPTERS:
            if adapter not in selected and adapter in discovered:
                selected.append(adapter)

        return selected

    def search(self, query: str, n: int = 10) -> list[Result]:
        cached = cache.get(self.name, query, ttl_hours=24)
        if cached is not None:
            return [Result(**r) for r in cached]

        all_results: list[Result] = []
        for adapter in self._adapters:
            results = _search_adapter(adapter, query, n=self._n)
            all_results.extend(results)

        # Dedupe by URL
        seen: set[str] = set()
        unique: list[Result] = []
        for r in all_results:
            if r.url and r.url not in seen:
                seen.add(r.url)
                unique.append(r)
            elif not r.url:
                unique.append(r)

        cache.put(self.name, query, [vars(r) for r in unique])
        return unique[:n]

    def adapters(self) -> list[str]:
        return list(self._adapters)


__all__ = ["OpenCLISource"]
