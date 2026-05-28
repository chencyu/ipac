#!/usr/bin/env python
"""trace.py — dispatch entry for code-context-trace.

Routes a (file, line-range) query to the per-language tracer.
Language detection: extension → shebang → --lang override.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve sibling tracer modules regardless of CWD.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


LANG_BY_EXT = {
    ".py": "python",
    ".pyi": "python",
    ".pyw": "python",
}


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in LANG_BY_EXT:
        return LANG_BY_EXT[ext]
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
    except OSError:
        return ""
    if first and first[0].startswith("#!") and "python" in first[0]:
        return "python"
    return ""


def parse_range(s: str) -> tuple[int, int]:
    raw = s.replace("L", "").replace("l", "").strip()
    if "-" in raw:
        a, b = raw.split("-", 1)
    elif ":" in raw:
        a, b = raw.split(":", 1)
    else:
        a = b = raw
    l1, l2 = int(a), int(b)
    if l1 > l2:
        l1, l2 = l2, l1
    return l1, l2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="trace.py",
        description="Trace dependency chain and implicit invariants for a code range.",
    )
    p.add_argument("file", help="Source file to analyze.")
    p.add_argument("range", help="Line range, e.g. L10-L25, 10-25, 10:25, or L10.")
    p.add_argument("--lang", help="Force language (default: auto-detect).")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    p.add_argument("--project-root", dest="project_root",
                   help="Override auto-detected project root for cross-file resolution.")
    args = p.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    lang = (args.lang or detect_language(path)).lower()
    try:
        l1, l2 = parse_range(args.range)
    except ValueError:
        print(f"error: invalid range: {args.range!r}", file=sys.stderr)
        return 2

    if lang == "python":
        import python_tracer
        proot = Path(args.project_root).resolve() if args.project_root else None
        out = python_tracer.trace_file(
            path, l1, l2, as_json=args.json, project_root=proot
        )
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    print(f"error: unsupported language for {path.name} (detected: {lang or 'unknown'})",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
