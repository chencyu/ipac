"""python_tracer.py — AST-based tracer with project-local cross-file resolution.

Single entry: `trace_file(path, l1, l2, as_json=False, project_root=None) -> str`.

Determinism rules
-----------------
- All facts emitted are locally verifiable from AST. No LLM.
- Cross-file resolution stays within `project_root` (auto-detected via markers,
  override via CLI). External modules are marked `external` and not expanded.
- Resolution chains terminate at definitions, cycles, externals, unresolved,
  or `max_depth` (default 12).
- `with X(...) as y:` is the project-recommended acquire form; pairings are
  reported as auto-managed (not flagged as hazards).
"""
from __future__ import annotations

import ast
import builtins as _builtins
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Project-root detection
# ---------------------------------------------------------------------------

PROJECT_MARKERS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "requirements.txt",
    ".git",
    ".hg",
)


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for parent in [cur, *cur.parents]:
        for marker in PROJECT_MARKERS:
            if (parent / marker).exists():
                return parent
    return cur


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _line(n: ast.AST) -> int:
    return getattr(n, "lineno", 0)


def _end(n: ast.AST) -> int:
    return getattr(n, "end_lineno", _line(n))


def _intersects(n: ast.AST, l1: int, l2: int) -> bool:
    return _line(n) <= l2 and _end(n) >= l1


def _contains(n: ast.AST, l1: int, l2: int) -> bool:
    return _line(n) <= l1 and _end(n) >= l2


def _src(source: str, n: ast.AST) -> str:
    seg = ast.get_source_segment(source, n)
    return (seg or "").strip()


def _attr_path(node: ast.AST) -> list[str] | None:
    """Return dotted attribute path for `Name | Attribute(... Name)` nodes."""
    parts: list[str] = []
    cur: ast.AST = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return parts
    return None


# ---------------------------------------------------------------------------
# Bindings & Scopes
# ---------------------------------------------------------------------------

@dataclass
class Binding:
    name: str
    node: ast.AST
    kind: str          # assign | augassign | annassign | import | from-import |
                       # param | for-target | with-target | except-as |
                       # function-def | class-def | global-decl | nonlocal-decl
    detail: str = ""

    @property
    def lineno(self) -> int:
        return _line(self.node)


@dataclass
class Scope:
    kind: str          # module | class | function | comprehension
    node: ast.AST
    name: str
    parent: "Scope | None" = None
    children: list["Scope"] = field(default_factory=list)
    bindings: dict[str, list[Binding]] = field(default_factory=lambda: defaultdict(list))
    uses: dict[str, list[ast.AST]] = field(default_factory=lambda: defaultdict(list))
    globals_decl: set[str] = field(default_factory=set)
    nonlocals_decl: set[str] = field(default_factory=set)

    @property
    def lineno(self) -> int:
        return _line(self.node)

    @property
    def end_lineno(self) -> int:
        return _end(self.node)

    def contains_line(self, lineno: int) -> bool:
        return self.lineno <= lineno <= self.end_lineno

    def innermost_at(self, lineno: int) -> "Scope":
        for ch in self.children:
            if ch.contains_line(lineno):
                return ch.innermost_at(lineno)
        return self

    def chain(self) -> list["Scope"]:
        out, s = [], self
        while s is not None:
            out.append(s)
            s = s.parent
        return out


# ---------------------------------------------------------------------------
# Scope builder
# ---------------------------------------------------------------------------

class ScopeBuilder(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.module_scope: Scope | None = None
        self._stack: list[Scope] = []

    @property
    def scope(self) -> Scope:
        return self._stack[-1]

    def _push(self, s: Scope) -> None:
        if self._stack:
            s.parent = self._stack[-1]
            self._stack[-1].children.append(s)
        self._stack.append(s)

    def _pop(self) -> None:
        self._stack.pop()

    def _bind(self, name: str, node: ast.AST, kind: str, detail: str = "") -> None:
        self.scope.bindings[name].append(Binding(name, node, kind, detail))

    def _bind_target(self, tgt: ast.AST, owner: ast.AST, kind: str, detail: str) -> None:
        if isinstance(tgt, ast.Name):
            self._bind(tgt.id, owner, kind, detail)
        elif isinstance(tgt, (ast.Tuple, ast.List)):
            for elt in tgt.elts:
                self._bind_target(elt, owner, kind, detail)
        elif isinstance(tgt, ast.Starred):
            self._bind_target(tgt.value, owner, kind, detail)

    def visit_Module(self, node: ast.Module) -> None:
        s = Scope(kind="module", node=node, name="<module>")
        self.module_scope = s
        self._push(s)
        for stmt in node.body:
            self.visit(stmt)
        self._pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for dec in node.decorator_list:
            self.visit(dec)
        for d in list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]:
            self.visit(d)
        self._bind(node.name, node, "function-def", f"def {node.name}(...)")
        s = Scope(kind="function", node=node, name=node.name)
        self._push(s)
        args = node.args
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            self._bind(a.arg, a, "param")
        if args.vararg:
            self._bind(args.vararg.arg, args.vararg, "param", "*args")
        if args.kwarg:
            self._bind(args.kwarg.arg, args.kwarg, "param", "**kwargs")
        for stmt in node.body:
            self.visit(stmt)
        self._pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for dec in node.decorator_list:
            self.visit(dec)
        for b in node.bases:
            self.visit(b)
        for kw in node.keywords:
            self.visit(kw.value)
        self._bind(node.name, node, "class-def", f"class {node.name}")
        s = Scope(kind="class", node=node, name=node.name)
        self._push(s)
        for stmt in node.body:
            self.visit(stmt)
        self._pop()

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for d in list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]:
            self.visit(d)
        s = Scope(kind="function", node=node, name="<lambda>")
        self._push(s)
        args = node.args
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            self._bind(a.arg, a, "param")
        if args.vararg:
            self._bind(args.vararg.arg, args.vararg, "param", "*args")
        if args.kwarg:
            self._bind(args.kwarg.arg, args.kwarg, "param", "**kwargs")
        self.visit(node.body)
        self._pop()

    def _visit_comp(self, node: ast.AST) -> None:
        s = Scope(kind="comprehension", node=node, name="<comp>")
        self._push(s)
        for gen in getattr(node, "generators", []):
            self.visit(gen.iter)
            self._bind_target(gen.target, gen, "for-target", "")
            for if_clause in gen.ifs:
                self.visit(if_clause)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self._pop()

    visit_ListComp = _visit_comp
    visit_SetComp = _visit_comp
    visit_GeneratorExp = _visit_comp
    visit_DictComp = _visit_comp

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        detail = _src(self.source, node)
        for tgt in node.targets:
            if isinstance(tgt, (ast.Attribute, ast.Subscript)):
                self.visit(tgt)
            self._bind_target(tgt, node, "assign", detail)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
        self.visit(node.annotation)
        detail = _src(self.source, node)
        self._bind_target(node.target, node, "annassign", detail)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self.scope.uses[node.target.id].append(node.target)
        elif isinstance(node.target, (ast.Attribute, ast.Subscript)):
            self.visit(node.target)
        detail = _src(self.source, node)
        self._bind_target(node.target, node, "augassign", detail)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._bind_target(node.target, node, "for-target", _src(self.source, node.iter))
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._bind_target(item.optional_vars, node, "with-target",
                                  _src(self.source, item.context_expr))
        for stmt in node.body:
            self.visit(stmt)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)

    def visit_Try(self, node: ast.Try) -> None:
        for stmt in node.body:
            self.visit(stmt)
        for h in node.handlers:
            if h.type is not None:
                self.visit(h.type)
            if h.name:
                self._bind(h.name, h, "except-as", "")
            for stmt in h.body:
                self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            detail = f"import {alias.name}"
            if alias.asname:
                detail += f" as {alias.asname}"
            self._bind(local, node, "import", detail)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = ("." * (node.level or 0)) + (node.module or "")
        for alias in node.names:
            local = alias.asname or alias.name
            detail = f"from {mod} import {alias.name}"
            if alias.asname:
                detail += f" as {alias.asname}"
            self._bind(local, node, "from-import", detail)

    def visit_Global(self, node: ast.Global) -> None:
        for n in node.names:
            self.scope.globals_decl.add(n)
            self._bind(n, node, "global-decl", f"global {n}")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        for n in node.names:
            self.scope.nonlocals_decl.add(n)
            self._bind(n, node, "nonlocal-decl", f"nonlocal {n}")

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.scope.uses[node.id].append(node)


# ---------------------------------------------------------------------------
# Name resolution (LEGB)
# ---------------------------------------------------------------------------

def resolve_name(scope: Scope, name: str) -> tuple[Scope, list[Binding]] | None:
    cur = scope
    while cur is not None and name not in cur.globals_decl and name not in cur.nonlocals_decl:
        if name in cur.bindings:
            return cur, cur.bindings[name]
        cur = cur.parent
    if cur is None:
        return None
    if name in cur.globals_decl:
        s = cur
        while s.parent is not None:
            s = s.parent
        if name in s.bindings:
            return s, s.bindings[name]
        return None
    s = cur.parent
    while s is not None:
        if s.kind == "function" and name in s.bindings:
            return s, s.bindings[name]
        s = s.parent
    return None


# ---------------------------------------------------------------------------
# Cross-file project-local resolver
# ---------------------------------------------------------------------------

class Resolver:
    """Owns project root + parsed-module cache. Resolves cross-file references
    only within the project root."""

    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self._cache: dict[Path, tuple[ast.Module, Scope, str] | None] = {}

    # ----- parsing -----

    def parse(self, path: Path) -> tuple[ast.Module, Scope, str] | None:
        key = path.resolve()
        if key in self._cache:
            return self._cache[key]
        try:
            source = key.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(key))
        except (OSError, SyntaxError, UnicodeDecodeError):
            self._cache[key] = None
            return None
        builder = ScopeBuilder(source)
        builder.visit(tree)
        assert builder.module_scope is not None
        result = (tree, builder.module_scope, source)
        self._cache[key] = result
        return result

    # ----- project boundaries -----

    def is_project_local(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root)
            return True
        except ValueError:
            return False

    def display_path(self, path: Path | str) -> str:
        p = Path(path).resolve() if path else Path()
        try:
            return p.relative_to(self.root).as_posix()
        except ValueError:
            return str(p)

    # ----- module file resolution -----

    def resolve_module_file(
        self, module_name: str, from_file: Path, level: int = 0
    ) -> Path | None:
        if level > 0:
            base = from_file.resolve().parent
            for _ in range(level - 1):
                base = base.parent
            search_bases = [base]
        else:
            search_bases = [self.root]
            src = self.root / "src"
            if src.is_dir():
                search_bases.append(src)

        parts = module_name.split(".") if module_name else []
        for base in search_bases:
            if not parts:
                init = base / "__init__.py"
                if init.is_file() and self.is_project_local(init):
                    return init
                continue
            f = base.joinpath(*parts).with_suffix(".py")
            if f.is_file() and self.is_project_local(f):
                return f
            pkg = base.joinpath(*parts) / "__init__.py"
            if pkg.is_file() and self.is_project_local(pkg):
                return pkg
        return None

    # ----- scope lookups -----

    def module_top_binding(self, module_file: Path, name: str) -> Binding | None:
        parsed = self.parse(module_file)
        if parsed is None:
            return None
        _, scope, _ = parsed
        if name in scope.bindings:
            return sorted(scope.bindings[name], key=lambda b: b.lineno)[0]
        return None

    def find_scope_at(self, root: Scope, kind: str, lineno: int) -> Scope | None:
        for ch in root.children:
            if ch.kind == kind and ch.lineno == lineno:
                return ch
            r = self.find_scope_at(ch, kind, lineno)
            if r is not None:
                return r
        return None


# ---------------------------------------------------------------------------
# Resolution chain
# ---------------------------------------------------------------------------

@dataclass
class Step:
    kind: str            # binding | module-file | instance | external | unresolved |
                         # star-import | cycle | depth-limit | builtin
    file: str = ""       # absolute path; converted to display at render time
    lineno: int | None = None
    name: str = ""
    binding_kind: str = ""
    detail: str = ""

    def to_dict(self, resolver: Resolver) -> dict[str, Any]:
        d: dict[str, Any] = {"kind": self.kind}
        if self.file:
            d["file"] = resolver.display_path(self.file)
        if self.lineno is not None:
            d["lineno"] = self.lineno
        if self.name:
            d["name"] = self.name
        if self.binding_kind:
            d["binding_kind"] = self.binding_kind
        if self.detail:
            d["detail"] = self.detail
        return d


_BUILTIN_NAMES = frozenset(dir(_builtins))
_MAX_DEPTH = 12


def _class_base_paths(class_scope: Scope, source: str) -> list[list[str]]:
    """Extract dotted name paths for a class's bases (best-effort)."""
    node = class_scope.node
    if not isinstance(node, ast.ClassDef):
        return []
    out: list[list[str]] = []
    for b in node.bases:
        p = _attr_path(b)
        if p is not None:
            out.append(p)
    return out


def _lookup_in_class_chain(
    class_scope: Scope,
    class_file: Path,
    attr: str,
    resolver: Resolver,
    visited: set[tuple[str, int]] | None = None,
) -> tuple[Path, Scope, Binding] | None:
    """Find `attr` in class scope; fall back to direct bases. Cycle-protected."""
    visited = visited if visited is not None else set()
    key = (str(class_file.resolve()), class_scope.lineno)
    if key in visited:
        return None
    visited.add(key)

    if attr in class_scope.bindings:
        return class_file, class_scope, sorted(
            class_scope.bindings[attr], key=lambda x: x.lineno
        )[0]

    parsed = resolver.parse(class_file)
    if parsed is None:
        return None
    _, mod_scope, source = parsed
    for base_parts in _class_base_paths(class_scope, source):
        # Resolve the base from the class's enclosing module scope
        base_steps = resolve_path(mod_scope, class_file, base_parts, resolver)
        # Find the deepest binding that is a class-def
        base_def: Step | None = None
        for s in base_steps:
            if s.kind == "binding" and s.binding_kind == "class-def" and s.file:
                base_def = s
        if base_def is None:
            continue
        base_file = Path(base_def.file)
        base_parsed = resolver.parse(base_file)
        if base_parsed is None:
            continue
        _, base_mod, _ = base_parsed
        base_class = resolver.find_scope_at(base_mod, "class", base_def.lineno)
        if base_class is None:
            continue
        found = _lookup_in_class_chain(base_class, base_file, attr, resolver, visited)
        if found is not None:
            return found
    return None


def resolve_path(
    scope: Scope,
    file: Path,
    parts: list[str],
    resolver: Resolver,
    max_depth: int = _MAX_DEPTH,
) -> list[Step]:
    """Resolve a dotted name path. Follows imports cross-file (project-local),
    class instantiations to class definitions, and class attributes to methods."""
    if not parts:
        return []

    steps: list[Step] = []

    root_name = parts[0]
    remaining = list(parts[1:])

    res = resolve_name(scope, root_name)
    if res is None:
        if root_name in _BUILTIN_NAMES:
            steps.append(Step(kind="builtin", name=root_name))
        else:
            steps.append(Step(kind="unresolved", name=root_name))
        return steps

    owning_scope, binds = res
    cur_binding = sorted(binds, key=lambda x: x.lineno)[0]
    cur_file = file.resolve()
    cur_scope = owning_scope

    visited: set[tuple[str, int, str]] = set()

    for _ in range(max_depth):
        steps.append(Step(
            kind="binding",
            file=str(cur_file),
            lineno=cur_binding.lineno,
            name=cur_binding.name,
            binding_kind=cur_binding.kind,
            detail=cur_binding.detail,
        ))
        key = (str(cur_file), cur_binding.lineno, cur_binding.name)
        if key in visited:
            steps.append(Step(kind="cycle"))
            return steps
        visited.add(key)

        bk = cur_binding.kind

        if bk == "import":
            node = cur_binding.node
            assert isinstance(node, ast.Import)
            alias_full = next(
                (a.name for a in node.names
                 if (a.asname or a.name.split(".")[0]) == cur_binding.name),
                None,
            )
            if alias_full is None:
                return steps
            top = alias_full.split(".")[0]
            mf = resolver.resolve_module_file(top, cur_file)
            if mf is None:
                steps.append(Step(kind="external", name=alias_full))
                return steps
            steps.append(Step(kind="module-file", file=str(mf.resolve()), name=top))
            if not remaining:
                return steps
            attr = remaining.pop(0)
            ab = resolver.module_top_binding(mf, attr)
            if ab is None:
                steps.append(Step(kind="unresolved", file=str(mf.resolve()), name=attr))
                return steps
            cur_file = mf.resolve()
            cur_binding = ab
            mod_parsed = resolver.parse(cur_file)
            if mod_parsed is None:
                return steps
            _, cur_scope, _ = mod_parsed
            continue

        if bk == "from-import":
            node = cur_binding.node
            assert isinstance(node, ast.ImportFrom)
            mod = node.module or ""
            mf = resolver.resolve_module_file(mod, cur_file, node.level or 0)
            if mf is None:
                full = f"{'.' * (node.level or 0)}{mod}.{cur_binding.name}".lstrip(".")
                steps.append(Step(kind="external", name=full))
                return steps
            steps.append(Step(
                kind="module-file",
                file=str(mf.resolve()),
                name=mod or f"<relative level {node.level}>",
            ))
            target_name = cur_binding.name
            for alias in node.names:
                local = alias.asname or alias.name
                if local == cur_binding.name:
                    target_name = alias.name
                    break
            if target_name == "*":
                steps.append(Step(kind="star-import", file=str(mf.resolve())))
                return steps
            ab = resolver.module_top_binding(mf, target_name)
            if ab is None:
                # Could itself be a sub-module: `from pkg import submod`
                sub_mf = resolver.resolve_module_file(
                    (mod + "." if mod else "") + target_name, cur_file, node.level or 0
                )
                if sub_mf is not None:
                    steps.append(Step(
                        kind="module-file",
                        file=str(sub_mf.resolve()),
                        name=target_name,
                    ))
                    if not remaining:
                        return steps
                    attr = remaining.pop(0)
                    sb = resolver.module_top_binding(sub_mf, attr)
                    if sb is None:
                        steps.append(Step(
                            kind="unresolved",
                            file=str(sub_mf.resolve()),
                            name=attr,
                        ))
                        return steps
                    cur_file = sub_mf.resolve()
                    cur_binding = sb
                    mod_parsed = resolver.parse(cur_file)
                    if mod_parsed is None:
                        return steps
                    _, cur_scope, _ = mod_parsed
                    continue
                steps.append(Step(
                    kind="unresolved",
                    file=str(mf.resolve()),
                    name=target_name,
                ))
                return steps
            cur_file = mf.resolve()
            cur_binding = ab
            mod_parsed = resolver.parse(cur_file)
            if mod_parsed is None:
                return steps
            _, cur_scope, _ = mod_parsed
            continue

        if bk == "assign":
            node = cur_binding.node
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                call_parts = _attr_path(node.value.func)
                if call_parts is not None:
                    callee_steps = resolve_path(
                        cur_scope, cur_file, call_parts, resolver,
                        max_depth=max(2, max_depth - 2),
                    )
                    class_def: Step | None = None
                    for s in callee_steps:
                        if s.kind == "binding" and s.binding_kind == "class-def":
                            class_def = s
                    if class_def is not None and class_def.file:
                        steps.append(Step(
                            kind="instance",
                            file=class_def.file,
                            lineno=class_def.lineno,
                            name=class_def.name,
                            detail=f"instance of class `{class_def.name}`",
                        ))
                        if not remaining:
                            return steps
                        cls_file = Path(class_def.file)
                        cls_parsed = resolver.parse(cls_file)
                        if cls_parsed is None:
                            return steps
                        _, cls_mod, _ = cls_parsed
                        cls_scope = resolver.find_scope_at(
                            cls_mod, "class", class_def.lineno or 0
                        )
                        if cls_scope is None:
                            return steps
                        attr = remaining.pop(0)
                        looked = _lookup_in_class_chain(
                            cls_scope, cls_file, attr, resolver
                        )
                        if looked is None:
                            steps.append(Step(
                                kind="unresolved",
                                file=str(cls_file),
                                name=f"{class_def.name}.{attr}",
                            ))
                            return steps
                        nf, nscope, nb = looked
                        cur_file = nf.resolve()
                        cur_scope = nscope
                        cur_binding = nb
                        continue
            return steps

        if bk == "class-def":
            if not remaining:
                return steps
            mod_parsed = resolver.parse(cur_file)
            if mod_parsed is None:
                return steps
            _, mod_scope, _ = mod_parsed
            cls_scope = resolver.find_scope_at(mod_scope, "class", cur_binding.lineno)
            if cls_scope is None:
                return steps
            attr = remaining.pop(0)
            looked = _lookup_in_class_chain(cls_scope, cur_file, attr, resolver)
            if looked is None:
                steps.append(Step(
                    kind="unresolved",
                    file=str(cur_file),
                    name=f"{cur_binding.name}.{attr}",
                ))
                return steps
            nf, nscope, nb = looked
            cur_file = nf.resolve()
            cur_scope = nscope
            cur_binding = nb
            continue

        # function-def, param, annassign, augassign, for-target, with-target,
        # except-as, global-decl, nonlocal-decl — chain terminates here.
        return steps

    steps.append(Step(kind="depth-limit"))
    return steps


# ---------------------------------------------------------------------------
# Implicit-invariant collectors
# ---------------------------------------------------------------------------

_RESOURCE_ACQUIRE = {
    "open": "close",
    "connect": "close",
    "acquire": "release",
    "start": "stop",
    "lock": "unlock",
}

_IO_HINTS = {
    "print", "input", "open",
    "read", "readline", "readlines", "write", "writelines",
    "send", "recv", "sendall",
}

_IO_ATTR_HINTS = {
    "get", "post", "put", "delete", "patch", "head", "request",
    "read_text", "write_text", "read_bytes", "write_bytes",
    "load", "dump", "loads", "dumps",
    "execute", "executemany", "fetchone", "fetchall", "commit",
}


def _callee_name(call: ast.Call) -> str:
    fn = call.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return ""


def _callee_full(call: ast.Call) -> str:
    p = _attr_path(call.func)
    return ".".join(p) if p else "<expr>"


def _is_mutable_default(node: ast.AST) -> bool:
    return isinstance(node, (ast.List, ast.Dict, ast.Set,
                             ast.ListComp, ast.DictComp, ast.SetComp))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@dataclass
class _VarReport:
    name: str
    uses: list[int]
    origin_bindings: list[Binding]
    later_rebinds: list[Binding]
    annotation: tuple[str, int] | None
    scope_name: str
    scope_kind: str
    resolution_kind: str
    chain: list[Step]


def _build_var_reports(
    range_uses: dict[str, list[ast.Name]],
    target_scope: Scope,
    target_file: Path,
    resolver: Resolver,
) -> list[_VarReport]:
    reports: list[_VarReport] = []
    for name, use_nodes in sorted(range_uses.items()):
        chain = resolve_path(target_scope, target_file, [name], resolver)
        resolved = resolve_name(target_scope, name)
        if resolved is None:
            reports.append(_VarReport(
                name=name,
                uses=sorted({_line(u) for u in use_nodes}),
                origin_bindings=[],
                later_rebinds=[],
                annotation=None,
                scope_name="?",
                scope_kind="?",
                resolution_kind=(
                    "builtin" if name in _BUILTIN_NAMES else "unresolved"
                ),
                chain=chain,
            ))
            continue
        owning_scope, binds = resolved
        binds_sorted = sorted(binds, key=lambda b: b.lineno)
        origin = [binds_sorted[0]] if binds_sorted else []
        later = binds_sorted[1:]
        ann = None
        for b in binds_sorted:
            if b.kind == "annassign" and isinstance(b.node, ast.AnnAssign):
                ann = (_src(resolver.parse(target_file)[2], b.node.annotation), b.lineno)
                break
        if owning_scope is target_scope:
            res_kind = "local"
        elif owning_scope.kind == "module":
            res_kind = "global"
        else:
            res_kind = "enclosing"
        reports.append(_VarReport(
            name=name,
            uses=sorted({_line(u) for u in use_nodes}),
            origin_bindings=origin,
            later_rebinds=later,
            annotation=ann,
            scope_name=owning_scope.name,
            scope_kind=owning_scope.kind,
            resolution_kind=res_kind,
            chain=chain,
        ))
    return reports


def _build_call_reports(
    range_calls: list[ast.Call],
    target_scope: Scope,
    target_file: Path,
    resolver: Resolver,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in range_calls:
        full = _callee_full(c)
        parts = _attr_path(c.func)
        if parts is None:
            out.append({
                "lineno": _line(c),
                "callee": full,
                "chain": [Step(kind="unresolved", name="<computed-callee>")],
            })
            continue
        chain = resolve_path(target_scope, target_file, parts, resolver)
        out.append({
            "lineno": _line(c),
            "callee": full,
            "chain": chain,
        })
    return out


# ---------------------------------------------------------------------------
# Trace driver
# ---------------------------------------------------------------------------

def trace_file(
    path: Path,
    l1: int,
    l2: int,
    as_json: bool = False,
    project_root: Path | None = None,
) -> str:
    path = Path(path).resolve()
    if project_root is None:
        project_root = find_project_root(path)
    else:
        project_root = Path(project_root).resolve()

    resolver = Resolver(project_root)
    parsed = resolver.parse(path)
    if parsed is None:
        raise RuntimeError(f"failed to parse {path}")
    tree, module_scope, source = parsed

    target_scope = module_scope.innermost_at(l1)

    range_uses: dict[str, list[ast.Name]] = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if l1 <= _line(node) <= l2:
                range_uses[node.id].append(node)

    var_reports = _build_var_reports(range_uses, target_scope, path, resolver)

    range_calls: list[ast.Call] = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and l1 <= _line(n) <= l2
    ]
    call_reports = _build_call_reports(range_calls, target_scope, path, resolver)

    # ---- Implicit invariants ----

    withs: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)) and _contains(node, l1, l2):
            items_desc = []
            for it in node.items:
                expr_src = _src(source, it.context_expr)
                var = ""
                if it.optional_vars is not None and isinstance(it.optional_vars, ast.Name):
                    var = it.optional_vars.id
                items_desc.append({"expr": expr_src, "as": var})
            withs.append({
                "lineno": _line(node),
                "end_lineno": _end(node),
                "is_async": isinstance(node, ast.AsyncWith),
                "items": items_desc,
            })
    withs.sort(key=lambda w: w["lineno"])

    trys: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and _contains(node, l1, l2):
            handlers = []
            for h in node.handlers:
                exc = _src(source, h.type) if h.type is not None else "<bare>"
                handlers.append({
                    "lineno": _line(h),
                    "exception": exc,
                    "as_name": h.name or "",
                    "bare": h.type is None,
                })
            trys.append({
                "lineno": _line(node),
                "end_lineno": _end(node),
                "handlers": handlers,
                "has_finally": bool(node.finalbody),
                "finally_lineno": _line(node.finalbody[0]) if node.finalbody else None,
                "has_else": bool(node.orelse),
            })
    trys.sort(key=lambda t: t["lineno"])

    asserts: list[dict[str, Any]] = []
    target_fn = next((s for s in target_scope.chain() if s.kind == "function"), None)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            if _line(node) > l2:
                continue
            if target_fn is not None and not (
                target_fn.lineno <= _line(node) <= target_fn.end_lineno
            ):
                continue
            asserts.append({
                "lineno": _line(node),
                "expr": _src(source, node.test),
                "msg": _src(source, node.msg) if node.msg is not None else "",
                "position": "in-range" if l1 <= _line(node) <= l2 else "precondition",
            })
    asserts.sort(key=lambda a: a["lineno"])

    decorators: list[dict[str, Any]] = []
    for s in target_scope.chain():
        if s.kind in ("function", "class") and isinstance(
            s.node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            for dec in s.node.decorator_list:
                dec_chain: list[Step] = []
                p = _attr_path(dec if not isinstance(dec, ast.Call) else dec.func)
                if p is not None:
                    dec_chain = resolve_path(module_scope, path, p, resolver)
                decorators.append({
                    "owner_kind": s.kind,
                    "owner_name": s.name,
                    "owner_lineno": _line(s.node),
                    "expr": _src(source, dec),
                    "lineno": _line(dec),
                    "chain": dec_chain,
                })

    annotations: list[dict[str, Any]] = []
    involved = set(range_uses.keys())
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in involved:
                annotations.append({
                    "name": node.target.id,
                    "annotation": _src(source, node.annotation),
                    "lineno": _line(node),
                    "site": "var",
                })
    if target_fn is not None and isinstance(
        target_fn.node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        fn = target_fn.node
        args = fn.args
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            if a.annotation is not None:
                annotations.append({
                    "name": a.arg,
                    "annotation": _src(source, a.annotation),
                    "lineno": _line(a),
                    "site": f"param of `{fn.name}`",
                })
        if fn.returns is not None:
            annotations.append({
                "name": f"return of `{fn.name}`",
                "annotation": _src(source, fn.returns),
                "lineno": _line(fn.returns),
                "site": "return",
            })

    # Resource pairings: include with-managed (auto) and manual; flag only manual
    # unpaired ones as hazards.
    pairings: list[dict[str, Any]] = []

    # With-managed acquires (entire `with` block guarantees release)
    for w in withs:
        for it in w["items"]:
            expr = it["expr"]
            # Heuristic: detect `func(...)` at start of expression where func name
            # matches a known acquire
            try:
                expr_ast = ast.parse(expr, mode="eval").body
            except SyntaxError:
                continue
            if isinstance(expr_ast, ast.Call):
                cn = _callee_name(expr_ast)
                if cn in _RESOURCE_ACQUIRE:
                    pairings.append({
                        "var": it["as"],
                        "acquire": cn,
                        "acquire_lineno": w["lineno"],
                        "release_lineno": w["end_lineno"],
                        "paired": True,
                        "expected_release": _RESOURCE_ACQUIRE[cn],
                        "managed_by": "with-block",
                    })

    # Manual acquires inside range
    acquire_sites: list[tuple[str, str, int]] = []
    release_sites: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if not _intersects(node, l1, l2):
            continue
        # Skip nodes that are inside a `with item.context_expr` (already managed)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fname = _callee_name(node.value)
            if fname in _RESOURCE_ACQUIRE and len(node.targets) == 1 and isinstance(
                node.targets[0], ast.Name
            ):
                acquire_sites.append((node.targets[0].id, fname, _line(node)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in _RESOURCE_ACQUIRE.values() and isinstance(node.func.value, ast.Name):
                release_sites.append((node.func.value.id, attr, _line(node)))
    matched_release_idx: set[int] = set()
    for var, acq, ln in acquire_sites:
        expected_rel = _RESOURCE_ACQUIRE[acq]
        match_line = None
        for i, (rvar, rname, rln) in enumerate(release_sites):
            if i in matched_release_idx:
                continue
            if rvar == var and rname == expected_rel and rln >= ln:
                match_line = rln
                matched_release_idx.add(i)
                break
        pairings.append({
            "var": var,
            "acquire": acq,
            "acquire_lineno": ln,
            "release_lineno": match_line,
            "paired": match_line is not None,
            "expected_release": expected_rel,
            "managed_by": "manual",
        })

    hazards: list[dict[str, Any]] = []
    if target_fn is not None and isinstance(
        target_fn.node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        fn = target_fn.node
        args = fn.args
        positional = list(args.posonlyargs) + list(args.args)
        defaults = list(args.defaults)
        offset = len(positional) - len(defaults)
        for i, d in enumerate(defaults):
            if _is_mutable_default(d):
                a = positional[offset + i]
                hazards.append({
                    "kind": "mutable-default",
                    "detail": f"param `{a.arg}` has mutable default `{_src(source, d)}`",
                    "lineno": _line(d),
                    "owner": f"def {fn.name}",
                })
        for a, d in zip(args.kwonlyargs, args.kw_defaults):
            if d is not None and _is_mutable_default(d):
                hazards.append({
                    "kind": "mutable-default",
                    "detail": f"kw-only param `{a.arg}` has mutable default `{_src(source, d)}`",
                    "lineno": _line(d),
                    "owner": f"def {fn.name}",
                })
    if target_scope.globals_decl:
        for name in target_scope.globals_decl:
            for b in target_scope.bindings.get(name, []):
                if b.kind == "global-decl":
                    continue
                if l1 <= b.lineno <= l2:
                    hazards.append({
                        "kind": "global-write",
                        "detail": f"writes to global `{name}` (declared via `global`)",
                        "lineno": b.lineno,
                        "owner": f"{target_scope.kind} {target_scope.name}",
                    })
    for t in trys:
        for h in t["handlers"]:
            if h["bare"]:
                hazards.append({
                    "kind": "bare-except",
                    "detail": "catches everything including SystemExit / KeyboardInterrupt",
                    "lineno": h["lineno"],
                    "owner": "",
                })
    for r in pairings:
        if not r["paired"] and r["managed_by"] == "manual":
            hazards.append({
                "kind": "unpaired-resource",
                "detail": (
                    f"`{r['var']} = {r['acquire']}(...)` at L{r['acquire_lineno']} "
                    f"has no matching `{r['expected_release']}()`"
                ),
                "lineno": r["acquire_lineno"],
                "owner": "",
            })

    side_effects: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not _intersects(node, l1, l2):
            continue
        if isinstance(node, ast.Call) and l1 <= _line(node) <= l2:
            cn = _callee_name(node)
            full = _callee_full(node)
            io_like = False
            if isinstance(node.func, ast.Name) and cn in _IO_HINTS:
                io_like = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr in _IO_ATTR_HINTS:
                io_like = True
            if io_like:
                side_effects.append({
                    "kind": "io-like-call",
                    "detail": f"`{full}(...)`",
                    "lineno": _line(node),
                })
        if isinstance(node, ast.Assign) and l1 <= _line(node) <= l2:
            for t in node.targets:
                if isinstance(t, ast.Attribute):
                    side_effects.append({
                        "kind": "attribute-write",
                        "detail": _src(source, t),
                        "lineno": _line(node),
                    })
                elif isinstance(t, ast.Subscript):
                    side_effects.append({
                        "kind": "subscript-write",
                        "detail": _src(source, t),
                        "lineno": _line(node),
                    })
        if isinstance(node, ast.AugAssign) and l1 <= _line(node) <= l2:
            if isinstance(node.target, ast.Attribute):
                side_effects.append({
                    "kind": "attribute-augwrite",
                    "detail": _src(source, node.target),
                    "lineno": _line(node),
                })
            elif isinstance(node.target, ast.Subscript):
                side_effects.append({
                    "kind": "subscript-augwrite",
                    "detail": _src(source, node.target),
                    "lineno": _line(node),
                })

    # ---- Assemble structured payload ----

    payload: dict[str, Any] = {
        "file": resolver.display_path(path),
        "project_root": str(resolver.root),
        "range": [l1, l2],
        "scope_chain": [
            {"kind": s.kind, "name": s.name, "lineno": s.lineno}
            for s in reversed(target_scope.chain())
        ],
        "source_lines": _extract_source_lines(source, l1, l2),
        "variable_origins": [
            _vr_to_dict(v, resolver) for v in var_reports
        ],
        "call_bindings": [
            {
                "lineno": c["lineno"],
                "callee": c["callee"],
                "chain": [s.to_dict(resolver) for s in c["chain"]],
            }
            for c in call_reports
        ],
        "implicit_invariants": {
            "context_managers": withs,
            "try_blocks": trys,
            "asserts": asserts,
            "decorators": [
                {
                    **{k: v for k, v in d.items() if k != "chain"},
                    "chain": [s.to_dict(resolver) for s in d["chain"]],
                }
                for d in decorators
            ],
            "annotations": annotations,
            "resource_pairings": pairings,
            "hazards": hazards,
            "side_effects": side_effects,
        },
    }

    if as_json:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return _render_markdown(payload, resolver)


def _extract_source_lines(source: str, l1: int, l2: int) -> list[tuple[int, str]]:
    lines = source.splitlines()
    out = []
    for i in range(l1, l2 + 1):
        if 1 <= i <= len(lines):
            out.append((i, lines[i - 1]))
    return out


def _vr_to_dict(v: _VarReport, resolver: Resolver) -> dict[str, Any]:
    return {
        "name": v.name,
        "uses": v.uses,
        "scope": {"kind": v.scope_kind, "name": v.scope_name},
        "resolution": v.resolution_kind,
        "origin": [
            {"lineno": b.lineno, "kind": b.kind, "detail": b.detail}
            for b in v.origin_bindings
        ],
        "later_rebinds": [
            {"lineno": b.lineno, "kind": b.kind, "detail": b.detail}
            for b in v.later_rebinds
        ],
        "annotation": (
            {"text": v.annotation[0], "lineno": v.annotation[1]}
            if v.annotation else None
        ),
        "chain": [s.to_dict(resolver) for s in v.chain],
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def _fmt_step(s: dict[str, Any]) -> str:
    k = s["kind"]
    file = s.get("file", "")
    ln = s.get("lineno")
    name = s.get("name", "")
    bk = s.get("binding_kind", "")
    detail = s.get("detail", "")
    loc = f"{file}:L{ln}" if file and ln else file
    if k == "binding":
        line = f"`{name}` ({bk}) at {loc}"
        if detail:
            line += f" — `{detail}`"
        return line
    if k == "module-file":
        return f"→ module `{name}` at {file}"
    if k == "instance":
        return f"→ {detail} (class def at {loc})"
    if k == "external":
        return f"→ external `{name}`"
    if k == "builtin":
        return f"→ builtin `{name}`"
    if k == "unresolved":
        return f"→ unresolved `{name}`" + (f" in {file}" if file else "")
    if k == "star-import":
        return f"→ `from {file} import *` (not followed)"
    if k == "cycle":
        return "→ (cycle detected)"
    if k == "depth-limit":
        return "→ (max depth)"
    return f"→ {k} {name}"


def _render_chain(chain: list[dict[str, Any]], indent: str = "  ") -> str:
    return "\n".join(f"{indent}- {_fmt_step(s)}" for s in chain)


def _render_markdown(p: dict[str, Any], resolver: Resolver) -> str:
    out = io.StringIO()
    w = out.write

    l1, l2 = p["range"]
    w(f"# Trace: {p['file']}:L{l1}-L{l2}\n\n")
    w(f"> Project root: `{p['project_root']}`\n")
    chain = " > ".join(f"{s['kind']} `{s['name']}`" for s in p["scope_chain"])
    w(f"> Scope chain (outer → inner): {chain}\n\n")

    src_lines = p["source_lines"]
    if src_lines:
        w("## Source\n\n```py\n")
        width = len(str(src_lines[-1][0]))
        for n, line in src_lines:
            w(f"{str(n).rjust(width)} | {line}\n")
        w("```\n\n")

    vrs = p["variable_origins"]
    if vrs:
        w("## Variable origins\n\n")
        for v in vrs:
            uses_str = ", ".join(f"L{u}" for u in v["uses"])
            w(f"- `{v['name']}` — used at {uses_str}\n")
            w(f"  - scope: {v['scope']['kind']} `{v['scope']['name']}` ({v['resolution']})\n")
            if v["origin"]:
                for b in v["origin"]:
                    detail = b["detail"] or ""
                    detail_s = f" — `{detail}`" if detail else ""
                    w(f"  - origin: L{b['lineno']} ({b['kind']}){detail_s}\n")
            else:
                w("  - origin: (unresolved — builtin / external / undefined)\n")
            for b in v["later_rebinds"]:
                detail = b["detail"] or ""
                detail_s = f" — `{detail}`" if detail else ""
                w(f"  - rebind: L{b['lineno']} ({b['kind']}){detail_s}\n")
            if v["annotation"]:
                a = v["annotation"]
                w(f"  - annotation: `{a['text']}` at L{a['lineno']}\n")
            # Cross-file chain (only show if non-trivial: depth >= 2)
            if len(v["chain"]) >= 2:
                w("  - resolution chain:\n")
                w(_render_chain(v["chain"], indent="    "))
                w("\n")
        w("\n")

    cbs = p["call_bindings"]
    if cbs:
        w("## Call bindings\n\n")
        for c in cbs:
            w(f"- `{c['callee']}(...)` at L{c['lineno']}\n")
            if c["chain"]:
                w(_render_chain(c["chain"], indent="  "))
                w("\n")
            else:
                w("  - (no resolution)\n")
        w("\n")

    inv = p["implicit_invariants"]

    if inv["context_managers"]:
        w("## Enclosing context managers\n\n")
        for cm in inv["context_managers"]:
            tag = "async with" if cm["is_async"] else "with"
            items = ", ".join(
                f"`{it['expr']}`" + (f" as `{it['as']}`" if it["as"] else "")
                for it in cm["items"]
            )
            w(f"- L{cm['lineno']}-L{cm['end_lineno']}: `{tag}` {items}\n")
        w("\n")

    if inv["try_blocks"]:
        w("## Enclosing try blocks\n\n")
        for t in inv["try_blocks"]:
            w(f"- L{t['lineno']}-L{t['end_lineno']}: `try`\n")
            for h in t["handlers"]:
                aname = f" as `{h['as_name']}`" if h["as_name"] else ""
                bare = " (BARE — hazard)" if h["bare"] else ""
                w(f"  - except `{h['exception']}`{aname} at L{h['lineno']}{bare}\n")
            if t["has_else"]:
                w("  - has `else:` clause\n")
            if t["has_finally"]:
                w(f"  - `finally:` at L{t['finally_lineno']}\n")
        w("\n")

    if inv["asserts"]:
        w("## Asserts (preconditions and in-range checks)\n\n")
        for a in inv["asserts"]:
            msg = f", msg `{a['msg']}`" if a["msg"] else ""
            w(f"- L{a['lineno']} ({a['position']}): `assert {a['expr']}`{msg}\n")
        w("\n")

    if inv["decorators"]:
        w("## Decorators on enclosing scopes\n\n")
        for d in inv["decorators"]:
            w(f"- `@{d['expr']}` at L{d['lineno']} on {d['owner_kind']} "
              f"`{d['owner_name']}` (L{d['owner_lineno']})\n")
            if len(d.get("chain") or []) >= 2:
                w(_render_chain(d["chain"], indent="  "))
                w("\n")
        w("\n")

    if inv["annotations"]:
        w("## Type annotations (explicit invariants)\n\n")
        for a in inv["annotations"]:
            w(f"- `{a['name']}: {a['annotation']}` at L{a['lineno']} — {a['site']}\n")
        w("\n")

    if inv["resource_pairings"]:
        w("## Resource acquire/release pairings\n\n")
        for r in inv["resource_pairings"]:
            mgmt = r["managed_by"]
            var_s = f"`{r['var']}`" if r["var"] else "(anonymous)"
            if r["paired"]:
                if mgmt == "with-block":
                    w(f"- {var_s} = `{r['acquire']}(...)` at L{r['acquire_lineno']}"
                      f" — auto-managed by `with` until L{r['release_lineno']}\n")
                else:
                    w(f"- {var_s} = `{r['acquire']}(...)` at L{r['acquire_lineno']}"
                      f" — paired `{r['expected_release']}` at L{r['release_lineno']}\n")
            else:
                w(f"- {var_s} = `{r['acquire']}(...)` at L{r['acquire_lineno']}"
                  f" — UNPAIRED (expected `{r['expected_release']}`) — hazard\n")
        w("\n")

    if inv["hazards"]:
        w("## Hazards\n\n")
        for h in inv["hazards"]:
            owner = f" in {h['owner']}" if h.get("owner") else ""
            w(f"- L{h['lineno']} ({h['kind']}): {h['detail']}{owner}\n")
        w("\n")

    if inv["side_effects"]:
        w("## Side effects in range\n\n")
        for s in inv["side_effects"]:
            w(f"- L{s['lineno']} ({s['kind']}): `{s['detail']}`\n")
        w("\n")

    return out.getvalue()
