---
name: code-context-trace
description: "Must load before tracing variable origins, callee definitions, or implicit invariants over a code range. Do not perform such tracing without this skill."
---

# Code Context Trace

Extract the **dependency chain + implicit invariants** for a specific code range without burning LLM tokens on the search. The work is delegated to a deterministic AST-based script; you only call it.

## When to call

- User asks "where does this variable come from?" / "what does this function actually call?" / "what's holding this together?"
- Before editing a non-trivial range, when origins of variables or callees are not all visible in the snippet.
- Before reasoning about correctness in a range that is inside `with` / `try` blocks or under decorators whose body you don't have.

If the range is fully self-contained and all symbols are defined within it, skip this skill.

## How to call

```
python scripts/trace.py <file> <range> [--lang python|rust] [--project-root <dir>] [--json]
```

- `<file>` — path to source file (absolute or workspace-relative).
- `<range>` — accepts `L10-L25`, `10-25`, `10:25`, or single `L10` (single line treated as `L10-L10`).
- `--lang` — force language. Default: auto-detect by extension; fallback to shebang for extensionless files.
- `--project-root` — override auto-detected project root. Auto-detection looks upward from `<file>` for `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`, `requirements.txt`, `Cargo.toml`, `.git`, or `.hg`.
- `--json` — emit JSON instead of Markdown (use only when the caller is another tool).

Default output is **Markdown**. Reasoning: LLM training corpus is Markdown-heavy; `##/###` headers anchor sections robustly; empty sections are omitted so output scales with information density, not range size.

## What you get back

Sections appear only if non-empty:

1. **Source** — the queried range, line-numbered, fenced.
2. **Variable origins** — for every `Name` used in the range with `Load` context: initial binding, all reassignments / aug-assigns, scope, type annotation (if any), parameter-of (if any). When the origin is an import, the **resolution chain** follows it across project-local files to the final definition.
3. **Call bindings** — for every `Call`: a **resolution chain** that follows the callee through imports, class instantiations, and attribute access. Chain steps include `binding`, `module-file`, `instance` (object → class def), `external` (outside project root), `builtin`, `unresolved`, `star-import`, `cycle`, `depth-limit`.
4. **Implicit invariants**:
   - **Enclosing context managers** — `with` blocks bracketing the range.
   - **Enclosing try blocks** — error-semantics: which exceptions caught, where, with `finally` cleanup.
   - **Asserts as preconditions** — `assert` statements visible above the range in the same function.
   - **Decorators on enclosing function** — with resolution chain to their definition.
   - **Type annotations** — explicit invariants on involved variables / parameters / return.
   - **Resource pairings** — `with X(...) as y:` listed as auto-managed; manual `acquire`/`release` pairs matched; unpaired manual acquires reported as hazard.
   - **Hazards** — mutable default args, `global` writes, bare `except:`, unpaired resources.
   - **Side effects in range** — I/O-like calls, attribute mutations, subscript writes.

## Cross-file resolution

Resolution stays within the project root. Followed:

- `import pkg.mod` + `pkg.mod.func()` — drills into the project-local module file.
- `from pkg.mod import X` — follows to `X`'s definition; if `X` is itself a re-export, follows further (with cycle detection).
- `from pkg import submod` — recognized as sub-module import.
- `obj = SomeClass(...)` + `obj.method()` — resolves `method` in the class body (and direct bases if not found).
- Relative imports (`from .x import y`) — relative to the file's package.

Not followed:

- Modules outside the project root (third-party packages, stdlib) — marked `external`.
- `from x import *` — marked `star-import`.
- Dynamic attribute access, `getattr`, reflection.

## Languages

- **Python** — implemented. Stdlib `ast` only; no external deps.
- **Rust** — implemented. Backed by a compiled binary (`scripts/rust_tracer/`) built automatically on first use via `cargo build --release`. Requires a Rust toolchain on PATH (`rustup` recommended; MSRV 1.70+, tested through 1.94). Uses `syn` 2.x; deterministic project-local resolution including:
  - `mod foo;` filesystem walk (with `mod.rs` and `foo.rs` layouts, lib/bin/workspace members from `Cargo.toml`).
  - `use a::b::C [as D]` aliases + `pub use` re-exports.
  - `crate::`, `self::`, `super::`, and sibling-crate prefixes inside a workspace.
  - Associated functions (`Type::method`), inherent `impl` blocks, and `impl Trait for Type` lookups for instance methods.
  - Implicit invariants: `unsafe` blocks, `?` propagation, panic surfaces (`unwrap`/`expect`/`panic!`/`assert!`/`todo!`/...), `mut` bindings, type annotations, lifetimes, `#[cfg(...)]` gates, attribute macros, I/O macros, mutation method calls.
  - Std prelude names (`Ok`, `Err`, `Option`, `Vec`, ...) are recognized; not treated as unresolved.
- Other languages — script reports "unsupported language for `<file>`" and exits 2.

Detection order: extension → shebang. To force, use `--lang`.

## Limitations

Python:
- Re-binding flow (e.g. `obj = factory(); obj = wrap(obj)`) — only the first binding's class is resolved.
- Conditional imports — the first binding by line number is taken as authoritative.
- Inherited methods are resolved via direct bases only (one-hop per base, recursive with cycle protection); diamond-inheritance order is best-effort, not strict MRO.
- Side-effect detection is heuristic (name-based for I/O, AST-shape-based for mutations).
- Python 3.8+ required (`ast.end_lineno`).

Rust:
- Macro expansion is not performed; items introduced by `macro_rules!` or proc-macros are reported as-is.
- Inline `mod foo { ... }` modules are detected but not deeply walked by file path (their items are still seen at the enclosing file).
- Method dispatch on receivers without a discoverable type binding (e.g., chained calls, generic params, `dyn Trait`) is reported as `unresolved-method` with the partial chain.
- Workspace globs in `[workspace] members = ["crates/*"]` are handled for direct subfolders only; deeper glob patterns are not expanded.
- External crates (anything not under the discovered workspace root) are marked but not traversed.

## Gotcha

Don't paraphrase the script's output back to the user — it's already structured for both you and the user to read. Cite specific `L<n>` references from it when answering follow-ups.
