"""Algorithm pattern matcher — accepts hashtags, returns candidate algorithms.

Usage (CLI)::

    python matcher.py graph shortest-path weighted
    python matcher.py --min-overlap 3 graph shortest-path weighted greedy
    python matcher.py --tags          # list all tags by category

Usage (library)::

    from matcher import match, tag_vocabulary
    from catalog import Tag as T

    results = match({T.GRAPH, T.SHORTEST_PATH, T.WEIGHTED})
    for r in results:
        print(r.algorithm.name, r.score, sorted(r.matched_tags))
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from catalog import CATALOG, TAG_CATEGORIES, Algorithm, Tag


# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class MatchResult:
    """A candidate algorithm with its match metadata."""

    algorithm: Algorithm
    matched_tags: frozenset[Tag]
    score: int


def match(
    selected: set[Tag],
    *,
    min_overlap: int = 2,
    catalog: tuple[Algorithm, ...] = CATALOG,
) -> list[MatchResult]:
    """Return algorithms sharing >= *min_overlap* tags with *selected*.

    Results are sorted by descending score (overlap count), then name.
    """
    results: list[MatchResult] = []
    for algo in catalog:
        overlap = algo.tags & selected
        if len(overlap) >= min_overlap:
            results.append(MatchResult(algo, overlap, len(overlap)))
    results.sort(key=lambda r: (-r.score, r.algorithm.name))
    return results


def tag_vocabulary() -> dict[str, tuple[Tag, ...]]:
    """Return all tags organised by category."""
    return dict(TAG_CATEGORIES)


def resolve_tags(names: list[str]) -> set[Tag]:
    """Convert raw strings to ``Tag`` values.

    Accepts both enum names (``GRAPH``) and values (``graph``).
    Raises ``ValueError`` on unknown tags.
    """
    by_value = {t.value: t for t in Tag}
    by_name = {t.name: t for t in Tag}
    resolved: set[Tag] = set()
    for raw in names:
        key = raw.strip().lower().replace("_", "-")
        tag = by_value.get(key) or by_name.get(raw.strip().upper().replace("-", "_"))
        if tag is None:
            raise ValueError(
                f"Unknown tag: {raw!r}. Use --tags to see all available tags."
            )
        resolved.add(tag)
    return resolved


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def _print_tags() -> None:
    for category, tags in TAG_CATEGORIES.items():
        print(f"\n{'─' * 4} {category} {'─' * 40}")
        for t in tags:
            print(f"  #{t.value}")


def _print_results(results: list[MatchResult]) -> None:
    if not results:
        print("No matching algorithms.")
        return
    max_name = max(len(r.algorithm.name) for r in results)
    for r in results:
        tags_str = ", ".join(f"#{t.value}" for t in sorted(r.matched_tags, key=lambda x: x.value))
        print(f"  [{r.score}] {r.algorithm.name:<{max_name}}  {tags_str}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Match problem hashtags to candidate algorithms.",
    )
    parser.add_argument(
        "hashtags",
        nargs="*",
        help="Hashtags to match (e.g. graph shortest-path weighted). "
             "Accepts tag values or enum names.",
    )
    parser.add_argument(
        "--min-overlap", "-m",
        type=int,
        default=2,
        help="Minimum number of matching tags (default: 2).",
    )
    parser.add_argument(
        "--tags", "-t",
        action="store_true",
        help="List all available tags and exit.",
    )

    args = parser.parse_args()

    if args.tags:
        _print_tags()
        return

    if not args.hashtags:
        parser.print_help()
        return

    try:
        selected = resolve_tags(args.hashtags)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    print(f"\nSelected: {', '.join(f'#{t.value}' for t in sorted(selected, key=lambda x: x.value))}")
    print(f"Min overlap: {args.min_overlap}\n")

    results = match(selected, min_overlap=args.min_overlap)
    _print_results(results)
    print(f"\n{len(results)} candidate(s) found.")


if __name__ == "__main__":
    main()
