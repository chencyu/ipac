// ctt_rust — Rust counterpart of python_tracer.py for the code-context-trace skill.
//
// Given a Rust file path and a line range, emit the full project-local
// resolution chain for every name referenced in the range, plus the implicit
// invariants (unsafe blocks, ? propagation, panic surfaces, mut bindings,
// cfg-gated code, lifetimes, attribute macros, type annotations).
//
// Determinism contract: project-local resolution is exhaustive. External
// crates (anything not under the detected workspace root) are marked but
// not expanded. Macro expansion is not performed; macro-defined items are
// noted as such.

use proc_macro2::LineColumn;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use syn::spanned::Spanned;
use syn::{visit::Visit, Item, UseTree};

// ─────────────────────────────────────────────────────────────────────────────
// CLI

#[derive(Debug)]
struct Args {
    file: PathBuf,
    range: (usize, usize),
    project_root: Option<PathBuf>,
    json: bool,
}

fn parse_args() -> Result<Args, String> {
    let mut args = env::args().skip(1);
    let mut file: Option<PathBuf> = None;
    let mut range_str: Option<String> = None;
    let mut project_root: Option<PathBuf> = None;
    let mut json = false;
    while let Some(a) = args.next() {
        match a.as_str() {
            "--json" => json = true,
            "--project-root" => {
                project_root = Some(PathBuf::from(
                    args.next().ok_or("--project-root needs a value")?,
                ));
            }
            "-h" | "--help" => {
                eprintln!(
                    "usage: ctt_rust <file> <range> [--project-root <path>] [--json]\n\
                     range examples: L10-L25, 10-25, 10:25, L10"
                );
                return Err(String::new());
            }
            s if file.is_none() => file = Some(PathBuf::from(s)),
            s if range_str.is_none() => range_str = Some(s.to_string()),
            other => return Err(format!("unexpected arg: {other}")),
        }
    }
    let file = file.ok_or("missing <file>")?;
    let range_str = range_str.ok_or("missing <range>")?;
    let range = parse_range(&range_str)?;
    Ok(Args { file, range, project_root, json })
}

fn parse_range(s: &str) -> Result<(usize, usize), String> {
    let s = s.trim();
    let s = s.trim_start_matches('L');
    let parts: Vec<&str> = if s.contains('-') {
        s.splitn(2, '-').collect()
    } else if s.contains(':') {
        s.splitn(2, ':').collect()
    } else {
        vec![s, s]
    };
    let lo = parts[0].trim_start_matches('L').parse::<usize>()
        .map_err(|e| format!("bad range start: {e}"))?;
    let hi = parts[1].trim_start_matches('L').parse::<usize>()
        .map_err(|e| format!("bad range end: {e}"))?;
    if lo > hi { return Err("range start > end".into()); }
    Ok((lo, hi))
}

// ─────────────────────────────────────────────────────────────────────────────
// Project root + crate discovery

fn find_project_root(start: &Path, override_: Option<&Path>) -> PathBuf {
    if let Some(p) = override_ {
        return p.canonicalize().unwrap_or_else(|_| p.to_path_buf());
    }
    let abs = start.canonicalize().unwrap_or_else(|_| start.to_path_buf());
    let mut dir: &Path = abs.parent().unwrap_or(&abs);
    let mut last_cargo: Option<PathBuf> = None;
    loop {
        let cargo = dir.join("Cargo.toml");
        if cargo.is_file() {
            // Prefer workspace root: keep walking up to find outermost Cargo.toml
            last_cargo = Some(dir.to_path_buf());
        }
        match dir.parent() {
            Some(p) if p != dir => dir = p,
            _ => break,
        }
    }
    if let Some(p) = last_cargo {
        return p;
    }
    // Fallback: file's directory
    abs.parent().unwrap_or(&abs).to_path_buf()
}

#[derive(Debug, Clone)]
struct CrateInfo {
    name: String,
    root_file: PathBuf, // src/lib.rs or src/main.rs or src/bin/X.rs
    crate_dir: PathBuf, // dir containing Cargo.toml
}

fn discover_crates(project_root: &Path) -> Vec<CrateInfo> {
    let mut out = Vec::new();
    discover_crates_at(project_root, &mut out);
    // Walk workspace members if declared
    if let Ok(toml_text) = fs::read_to_string(project_root.join("Cargo.toml")) {
        if let Ok(parsed) = toml_text.parse::<toml::Value>() {
            if let Some(members) = parsed
                .get("workspace")
                .and_then(|w| w.get("members"))
                .and_then(|m| m.as_array())
            {
                for m in members {
                    if let Some(s) = m.as_str() {
                        // Glob-light: handle direct paths; ignore wildcards beyond simple "*"
                        let p = project_root.join(s);
                        if p.is_dir() {
                            discover_crates_at(&p, &mut out);
                        } else if s.ends_with("/*") {
                            if let Some(parent) = p.parent() {
                                if let Ok(rd) = fs::read_dir(parent) {
                                    for ent in rd.flatten() {
                                        let pp = ent.path();
                                        if pp.is_dir() {
                                            discover_crates_at(&pp, &mut out);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    // dedupe by crate_dir
    let mut seen: BTreeSet<PathBuf> = BTreeSet::new();
    out.retain(|c| seen.insert(c.crate_dir.clone()));
    out
}

fn discover_crates_at(dir: &Path, out: &mut Vec<CrateInfo>) {
    let cargo = dir.join("Cargo.toml");
    if !cargo.is_file() { return; }
    let text = match fs::read_to_string(&cargo) { Ok(t) => t, Err(_) => return };
    let parsed: toml::Value = match text.parse() { Ok(v) => v, Err(_) => return };
    let pkg_name = parsed.get("package")
        .and_then(|p| p.get("name"))
        .and_then(|n| n.as_str())
        .map(|s| s.replace('-', "_"));
    // [lib]
    let lib_path = parsed.get("lib")
        .and_then(|l| l.get("path"))
        .and_then(|p| p.as_str())
        .map(|s| dir.join(s));
    let default_lib = dir.join("src").join("lib.rs");
    if let Some(name) = &pkg_name {
        if let Some(lp) = &lib_path {
            if lp.is_file() {
                out.push(CrateInfo { name: name.clone(), root_file: lp.clone(), crate_dir: dir.to_path_buf() });
            }
        } else if default_lib.is_file() {
            out.push(CrateInfo { name: name.clone(), root_file: default_lib.clone(), crate_dir: dir.to_path_buf() });
        }
    }
    // [[bin]]
    if let Some(bins) = parsed.get("bin").and_then(|b| b.as_array()) {
        for b in bins {
            let name = b.get("name").and_then(|n| n.as_str()).map(|s| s.replace('-', "_"));
            let path = b.get("path").and_then(|p| p.as_str()).map(|s| dir.join(s));
            if let (Some(name), Some(path)) = (name, path) {
                if path.is_file() {
                    out.push(CrateInfo { name, root_file: path, crate_dir: dir.to_path_buf() });
                }
            }
        }
    }
    // default src/main.rs
    let default_main = dir.join("src").join("main.rs");
    if let Some(name) = &pkg_name {
        if default_main.is_file() && !out.iter().any(|c| c.root_file == default_main) {
            out.push(CrateInfo { name: name.clone(), root_file: default_main, crate_dir: dir.to_path_buf() });
        }
    }
    // src/bin/*.rs
    let bin_dir = dir.join("src").join("bin");
    if bin_dir.is_dir() {
        if let Ok(rd) = fs::read_dir(&bin_dir) {
            for ent in rd.flatten() {
                let p = ent.path();
                if p.extension().and_then(|e| e.to_str()) == Some("rs") {
                    let name = p.file_stem().and_then(|s| s.to_str()).unwrap_or("bin").replace('-', "_");
                    out.push(CrateInfo { name, root_file: p, crate_dir: dir.to_path_buf() });
                } else if p.is_dir() {
                    let mainrs = p.join("main.rs");
                    if mainrs.is_file() {
                        let name = p.file_name().and_then(|s| s.to_str()).unwrap_or("bin").replace('-', "_");
                        out.push(CrateInfo { name, root_file: mainrs, crate_dir: dir.to_path_buf() });
                    }
                }
            }
        }
    }
}

/// Find which crate the query file belongs to, plus its module path within that crate.
fn locate_file_in_crates(crates: &[CrateInfo], file: &Path) -> Option<(CrateInfo, Vec<String>)> {
    let file = file.canonicalize().unwrap_or_else(|_| file.to_path_buf());
    // Best crate = one whose root_file is in the deepest enclosing dir of `file`.
    let mut best: Option<(CrateInfo, Vec<String>)> = None;
    for c in crates {
        let root_dir = c.root_file.parent().unwrap_or(&c.crate_dir);
        if let Ok(rel) = file.strip_prefix(root_dir) {
            let comps: Vec<String> = rel.components()
                .map(|c| c.as_os_str().to_string_lossy().to_string())
                .collect();
            // Module path is comps without trailing .rs and without mod.rs marker
            let mut mods: Vec<String> = Vec::new();
            for (i, p) in comps.iter().enumerate() {
                if i == comps.len() - 1 {
                    let stem = p.strip_suffix(".rs").unwrap_or(p);
                    if stem != "mod" && stem != "lib" && stem != "main"
                       && !c.root_file.ends_with(p) // root file maps to crate root
                    {
                        mods.push(stem.to_string());
                    }
                } else {
                    mods.push(p.clone());
                }
            }
            let candidate = (c.clone(), mods);
            best = match best {
                None => Some(candidate),
                Some(prev) => {
                    if candidate.1.len() <= prev.1.len()
                       && candidate.0.crate_dir.starts_with(&prev.0.crate_dir) {
                        Some(candidate)
                    } else { Some(prev) }
                }
            };
        }
    }
    best
}

// ─────────────────────────────────────────────────────────────────────────────
// Module tree (mod foo; resolution)

fn module_file_candidates(parent_file: &Path, mod_name: &str) -> Vec<PathBuf> {
    let parent_dir = parent_file.parent().unwrap_or(parent_file);
    let is_root_like = matches!(
        parent_file.file_name().and_then(|s| s.to_str()),
        Some("lib.rs") | Some("main.rs") | Some("mod.rs")
    );
    let mut out = Vec::new();
    if is_root_like {
        out.push(parent_dir.join(format!("{mod_name}.rs")));
        out.push(parent_dir.join(mod_name).join("mod.rs"));
    } else {
        // sibling module under a directory named after parent stem
        let stem = parent_file.file_stem().and_then(|s| s.to_str()).unwrap_or("");
        let sub = parent_dir.join(stem);
        out.push(sub.join(format!("{mod_name}.rs")));
        out.push(sub.join(mod_name).join("mod.rs"));
        // Also allow the rust 2018 implicit (sibling)
        out.push(parent_dir.join(format!("{mod_name}.rs")));
        out.push(parent_dir.join(mod_name).join("mod.rs"));
    }
    out
}

// ─────────────────────────────────────────────────────────────────────────────
// Parse cache + module item index

struct ParseCache {
    files: HashMap<PathBuf, Result<syn::File, String>>,
}

impl ParseCache {
    fn new() -> Self { Self { files: HashMap::new() } }
    fn get(&mut self, path: &Path) -> Result<&syn::File, String> {
        let path = path.to_path_buf();
        if !self.files.contains_key(&path) {
            let parsed = fs::read_to_string(&path)
                .map_err(|e| format!("read {}: {}", path.display(), e))
                .and_then(|src| syn::parse_file(&src)
                    .map_err(|e| format!("parse {}: {}", path.display(), e)));
            self.files.insert(path.clone(), parsed);
        }
        match self.files.get(&path).unwrap() {
            Ok(f) => Ok(f),
            Err(e) => Err(e.clone()),
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Scope + binding

#[derive(Debug, Clone, Serialize)]
struct Binding {
    name: String,
    kind: String,    // "let", "param", "for-pat", "if-let", "while-let", "match-pat", "closure-param", "fn", "struct", "enum", "trait", "impl-method", "const", "static", "type-alias", "mod", "use", "use-as", "use-glob"
    line: usize,
    detail: String,
    annotation: Option<String>,
    is_mut: bool,
    // For uses: the resolved path segments
    use_path: Option<Vec<String>>,
}

#[derive(Debug, Default)]
struct ScopeCollection {
    bindings_by_line: BTreeMap<usize, Vec<Binding>>,
    enclosing_kind: String,
    enclosing_name: String,
    enclosing_line: usize,
}

// ─────────────────────────────────────────────────────────────────────────────
// Reference collection in range

#[derive(Debug, Clone, Serialize)]
struct Reference {
    name: String,
    line: usize,
    column: usize,
    full_path: Vec<String>, // for Path expressions: a::b::c
    is_call: bool,
    method_receiver: Option<Box<Reference>>, // for method calls
    method_name: Option<String>,
}

#[derive(Default)]
struct ReferenceCollector {
    range: (usize, usize),
    refs: Vec<Reference>,
}

impl<'ast> Visit<'ast> for ReferenceCollector {
    fn visit_expr(&mut self, node: &'ast syn::Expr) {
        let span = node.span();
        let LineColumn { line, column } = span.start();
        let in_range = line >= self.range.0 && line <= self.range.1;
        match node {
            syn::Expr::Path(ep) if in_range => {
                let segs: Vec<String> = ep.path.segments.iter()
                    .map(|s| s.ident.to_string()).collect();
                if let Some(name) = segs.first() {
                    self.refs.push(Reference {
                        name: name.clone(),
                        line, column,
                        full_path: segs.clone(),
                        is_call: false,
                        method_receiver: None,
                        method_name: None,
                    });
                }
            }
            syn::Expr::Call(c) if in_range => {
                if let syn::Expr::Path(ep) = &*c.func {
                    let segs: Vec<String> = ep.path.segments.iter()
                        .map(|s| s.ident.to_string()).collect();
                    if let Some(name) = segs.first() {
                        self.refs.push(Reference {
                            name: name.clone(),
                            line, column,
                            full_path: segs.clone(),
                            is_call: true,
                            method_receiver: None,
                            method_name: None,
                        });
                    }
                }
            }
            syn::Expr::MethodCall(m) if in_range => {
                // Try to capture receiver as a simple Path for resolution
                let recv_ref = simple_path_of(&m.receiver).map(|(name, segs, l, c)| Box::new(Reference {
                    name, line: l, column: c, full_path: segs,
                    is_call: false, method_receiver: None, method_name: None,
                }));
                self.refs.push(Reference {
                    name: m.method.to_string(),
                    line, column,
                    full_path: vec![m.method.to_string()],
                    is_call: true,
                    method_receiver: recv_ref,
                    method_name: Some(m.method.to_string()),
                });
            }
            _ => {}
        }
        syn::visit::visit_expr(self, node);
    }
}

fn simple_path_of(expr: &syn::Expr) -> Option<(String, Vec<String>, usize, usize)> {
    if let syn::Expr::Path(ep) = expr {
        let segs: Vec<String> = ep.path.segments.iter().map(|s| s.ident.to_string()).collect();
        let name = segs.first()?.clone();
        let lc = ep.span().start();
        return Some((name, segs, lc.line, lc.column));
    }
    None
}

// ─────────────────────────────────────────────────────────────────────────────
// Local scope visitor (collect bindings inside the enclosing item)

struct LocalScopeVisitor {
    range: (usize, usize),
    bindings: Vec<Binding>,
    invariants: Invariants,
}

#[derive(Default, Debug, Serialize, Clone)]
struct Invariants {
    unsafe_blocks: Vec<(usize, String)>,
    try_propagations: Vec<(usize, String)>,
    panic_surfaces: Vec<(usize, String)>,
    mut_bindings: Vec<(usize, String)>,
    type_annotations: Vec<(usize, String)>,
    lifetimes: Vec<(usize, String)>,
    cfg_gates: Vec<(usize, String)>,
    attribute_macros: Vec<(usize, String)>,
    side_effects: Vec<(usize, String)>,
}

impl LocalScopeVisitor {
    fn in_range(&self, line: usize) -> bool {
        line >= self.range.0 && line <= self.range.1
    }
    fn track_pat(&mut self, pat: &syn::Pat, ty: Option<&syn::Type>, kind: &str, detail: String) {
        let _ = kind; let _ = detail;
        collect_pat_bindings(pat, ty, &mut self.bindings, "let");
    }
}

fn pretty_type(ty: &syn::Type) -> String {
    let toks = quote::quote!(#ty).to_string();
    // collapse whitespace
    toks.split_whitespace().collect::<Vec<_>>().join(" ")
}
fn pretty_pat(pat: &syn::Pat) -> String {
    let toks = quote::quote!(#pat).to_string();
    toks.split_whitespace().collect::<Vec<_>>().join(" ")
}
fn pretty_expr(expr: &syn::Expr) -> String {
    let toks = quote::quote!(#expr).to_string();
    let s = toks.split_whitespace().collect::<Vec<_>>().join(" ");
    if s.len() > 120 { format!("{}…", &s[..120]) } else { s }
}

fn collect_pat_bindings(pat: &syn::Pat, ty: Option<&syn::Type>, out: &mut Vec<Binding>, kind: &str) {
    match pat {
        syn::Pat::Ident(pi) => {
            let line = pi.span().start().line;
            out.push(Binding {
                name: pi.ident.to_string(),
                kind: kind.to_string(),
                line,
                detail: pretty_pat(pat),
                annotation: ty.map(pretty_type),
                is_mut: pi.mutability.is_some(),
                use_path: None,
            });
            if let Some((_, sub)) = &pi.subpat {
                collect_pat_bindings(sub, ty, out, kind);
            }
        }
        syn::Pat::Type(pt) => {
            collect_pat_bindings(&pt.pat, Some(&pt.ty), out, kind);
        }
        syn::Pat::Tuple(t) => {
            for p in &t.elems { collect_pat_bindings(p, None, out, kind); }
        }
        syn::Pat::TupleStruct(ts) => {
            for p in &ts.elems { collect_pat_bindings(p, None, out, kind); }
        }
        syn::Pat::Struct(s) => {
            for f in &s.fields { collect_pat_bindings(&f.pat, None, out, kind); }
        }
        syn::Pat::Reference(r) => collect_pat_bindings(&r.pat, ty, out, kind),
        syn::Pat::Or(o) => {
            for p in &o.cases { collect_pat_bindings(p, ty, out, kind); }
        }
        syn::Pat::Slice(s) => {
            for p in &s.elems { collect_pat_bindings(p, None, out, kind); }
        }
        syn::Pat::Paren(p) => collect_pat_bindings(&p.pat, ty, out, kind),
        _ => {}
    }
}

impl<'ast> Visit<'ast> for LocalScopeVisitor {
    fn visit_local(&mut self, node: &'ast syn::Local) {
        let init_detail = node.init.as_ref().map(|i| pretty_expr(&i.expr)).unwrap_or_default();
        let ty = match &node.pat {
            syn::Pat::Type(pt) => Some(&*pt.ty),
            _ => None,
        };
        let mut new_bindings = Vec::new();
        collect_pat_bindings(&node.pat, ty, &mut new_bindings, "let");
        for b in &mut new_bindings {
            if !init_detail.is_empty() {
                b.detail = format!("let {} = {}", pretty_pat(&node.pat), init_detail);
            } else {
                b.detail = format!("let {}", pretty_pat(&node.pat));
            }
            if b.is_mut {
                self.invariants.mut_bindings.push((b.line, b.detail.clone()));
            }
            if let Some(ann) = &b.annotation {
                self.invariants.type_annotations.push((b.line, format!("let {}: {}", b.name, ann)));
            }
        }
        self.bindings.extend(new_bindings);
        syn::visit::visit_local(self, node);
    }

    fn visit_expr_for_loop(&mut self, node: &'ast syn::ExprForLoop) {
        let mut new_bindings = Vec::new();
        collect_pat_bindings(&node.pat, None, &mut new_bindings, "for-pat");
        for b in &mut new_bindings {
            b.detail = format!("for {} in {}", pretty_pat(&node.pat), pretty_expr(&node.expr));
        }
        self.bindings.extend(new_bindings);
        syn::visit::visit_expr_for_loop(self, node);
    }

    fn visit_expr_let(&mut self, node: &'ast syn::ExprLet) {
        let mut new_bindings = Vec::new();
        collect_pat_bindings(&node.pat, None, &mut new_bindings, "if-let");
        for b in &mut new_bindings {
            b.detail = format!("if let {} = {}", pretty_pat(&node.pat), pretty_expr(&node.expr));
        }
        self.bindings.extend(new_bindings);
        syn::visit::visit_expr_let(self, node);
    }

    fn visit_arm(&mut self, node: &'ast syn::Arm) {
        let mut new_bindings = Vec::new();
        collect_pat_bindings(&node.pat, None, &mut new_bindings, "match-pat");
        for b in &mut new_bindings {
            b.detail = format!("match arm: {}", pretty_pat(&node.pat));
        }
        self.bindings.extend(new_bindings);
        syn::visit::visit_arm(self, node);
    }

    fn visit_expr_closure(&mut self, node: &'ast syn::ExprClosure) {
        for input in &node.inputs {
            let mut new_bindings = Vec::new();
            collect_pat_bindings(input, None, &mut new_bindings, "closure-param");
            for b in &mut new_bindings {
                b.detail = format!("closure |{}|", pretty_pat(input));
            }
            self.bindings.extend(new_bindings);
        }
        syn::visit::visit_expr_closure(self, node);
    }

    fn visit_expr_unsafe(&mut self, node: &'ast syn::ExprUnsafe) {
        let line = node.span().start().line;
        if self.in_range(line) {
            self.invariants.unsafe_blocks.push((line, "unsafe { ... }".into()));
        }
        syn::visit::visit_expr_unsafe(self, node);
    }

    fn visit_expr_try(&mut self, node: &'ast syn::ExprTry) {
        let line = node.span().start().line;
        if self.in_range(line) {
            self.invariants.try_propagations.push((line, format!("{}?", pretty_expr(&node.expr))));
        }
        syn::visit::visit_expr_try(self, node);
    }

    fn visit_expr_method_call(&mut self, node: &'ast syn::ExprMethodCall) {
        let line = node.span().start().line;
        let m = node.method.to_string();
        if self.in_range(line) && PANIC_METHODS.contains(&m.as_str()) {
            self.invariants.panic_surfaces.push((line, format!(".{}()  on {}", m, pretty_expr(&node.receiver))));
        }
        if self.in_range(line) && SIDE_EFFECT_METHODS.contains(&m.as_str()) {
            self.invariants.side_effects.push((line, format!("call .{}() — likely I/O or mutation", m)));
        }
        syn::visit::visit_expr_method_call(self, node);
    }

    fn visit_expr_macro(&mut self, node: &'ast syn::ExprMacro) {
        let line = node.span().start().line;
        if self.in_range(line) {
            if let Some(seg) = node.mac.path.segments.last() {
                let name = seg.ident.to_string();
                if PANIC_MACROS.contains(&name.as_str()) {
                    self.invariants.panic_surfaces.push((line, format!("{}!(...)", name)));
                }
                if IO_MACROS.contains(&name.as_str()) {
                    self.invariants.side_effects.push((line, format!("{}!(...) — I/O macro", name)));
                }
            }
        }
        syn::visit::visit_expr_macro(self, node);
    }

    fn visit_expr_assign(&mut self, node: &'ast syn::ExprAssign) {
        let line = node.span().start().line;
        if self.in_range(line) {
            self.invariants.side_effects.push((line, format!("assign: {} = ...", pretty_expr(&node.left))));
        }
        syn::visit::visit_expr_assign(self, node);
    }
}

const PANIC_METHODS: &[&str] = &[
    "unwrap", "expect", "unwrap_err", "expect_err", "unwrap_unchecked",
];
const PANIC_MACROS: &[&str] = &[
    "panic", "unreachable", "todo", "unimplemented", "assert", "assert_eq", "assert_ne", "debug_assert", "debug_assert_eq", "debug_assert_ne",
];
const SIDE_EFFECT_METHODS: &[&str] = &[
    "write", "write_all", "write_fmt", "flush", "send", "recv",
    "lock", "borrow_mut", "set", "insert", "remove", "push", "pop", "clear", "extend",
    "spawn", "spawn_blocking",
];
const IO_MACROS: &[&str] = &[
    "println", "eprintln", "print", "eprint", "write", "writeln", "dbg",
];

const STD_PRELUDE: &[&str] = &[
    // types
    "Option", "Result", "Vec", "String", "Box", "Rc", "Arc", "Cell", "RefCell",
    "HashMap", "HashSet", "BTreeMap", "BTreeSet", "VecDeque", "PathBuf", "Path",
    // variants
    "Some", "None", "Ok", "Err",
    // traits commonly used by name
    "Default", "Clone", "Copy", "Drop", "From", "Into", "TryFrom", "TryInto",
    "Iterator", "IntoIterator", "FromIterator", "AsRef", "AsMut", "Deref", "DerefMut",
    "Send", "Sync", "Sized", "Display", "Debug",
];

// ─────────────────────────────────────────────────────────────────────────────
// File-level item indexing (for resolution)

#[derive(Debug, Clone, Serialize)]
struct ItemEntry {
    name: String,
    kind: String,      // "fn", "struct", "enum", "trait", "const", "static", "type-alias", "mod", "macro"
    line: usize,
    has_body: bool,
}

#[derive(Debug, Default, Clone)]
struct ModuleIndex {
    items: HashMap<String, ItemEntry>,
    /// Inline modules: name -> child syn::File equivalent (kept as items list of original file)
    inline_mods: HashMap<String, usize>, // value: index into outer items array, used only as marker
    /// `mod foo;` declarations referencing external files
    mod_decls: Vec<String>,
    /// `use a::b::C [as D];` entries, by introduced binding name -> path segments
    uses: HashMap<String, Vec<String>>,
    /// pub use (re-exports), used when resolving from outside this module
    pub_uses: HashMap<String, Vec<String>>,
    /// glob uses `use a::*;`
    glob_uses: Vec<Vec<String>>,
    /// All impl blocks in this file (collected separately by Resolver)
    /// Stored as raw lookups later
    /// Lifetime/cfg/attr captured for invariants
    lifetimes: Vec<(usize, String)>,
    cfgs: Vec<(usize, String)>,
    attr_macros: Vec<(usize, String)>,
}

fn index_items(items: &[Item], idx: &mut ModuleIndex) {
    for item in items {
        match item {
            Item::Fn(f) => {
                let line = f.span().start().line;
                idx.items.insert(f.sig.ident.to_string(), ItemEntry {
                    name: f.sig.ident.to_string(),
                    kind: "fn".into(), line, has_body: true,
                });
                collect_attrs(&f.attrs, line, idx);
                collect_lifetimes(&f.sig.generics, line, idx);
            }
            Item::Struct(s) => {
                let line = s.span().start().line;
                idx.items.insert(s.ident.to_string(), ItemEntry {
                    name: s.ident.to_string(), kind: "struct".into(), line, has_body: true,
                });
                collect_attrs(&s.attrs, line, idx);
                collect_lifetimes(&s.generics, line, idx);
            }
            Item::Enum(e) => {
                let line = e.span().start().line;
                idx.items.insert(e.ident.to_string(), ItemEntry {
                    name: e.ident.to_string(), kind: "enum".into(), line, has_body: true,
                });
                collect_attrs(&e.attrs, line, idx);
            }
            Item::Trait(t) => {
                let line = t.span().start().line;
                idx.items.insert(t.ident.to_string(), ItemEntry {
                    name: t.ident.to_string(), kind: "trait".into(), line, has_body: true,
                });
            }
            Item::Const(c) => {
                let line = c.span().start().line;
                idx.items.insert(c.ident.to_string(), ItemEntry {
                    name: c.ident.to_string(), kind: "const".into(), line, has_body: true,
                });
            }
            Item::Static(s) => {
                let line = s.span().start().line;
                idx.items.insert(s.ident.to_string(), ItemEntry {
                    name: s.ident.to_string(), kind: "static".into(), line, has_body: true,
                });
            }
            Item::Type(t) => {
                let line = t.span().start().line;
                idx.items.insert(t.ident.to_string(), ItemEntry {
                    name: t.ident.to_string(), kind: "type-alias".into(), line, has_body: true,
                });
            }
            Item::Mod(m) => {
                let line = m.span().start().line;
                idx.items.insert(m.ident.to_string(), ItemEntry {
                    name: m.ident.to_string(), kind: "mod".into(), line,
                    has_body: m.content.is_some(),
                });
                if m.content.is_none() {
                    idx.mod_decls.push(m.ident.to_string());
                }
            }
            Item::Use(u) => {
                let is_pub = matches!(u.vis, syn::Visibility::Public(_));
                let mut acc = Vec::new();
                walk_use_tree(&u.tree, &mut acc, idx, is_pub);
            }
            Item::Macro(_) | Item::ExternCrate(_) | Item::ForeignMod(_) | Item::Verbatim(_) | Item::Union(_) | Item::Impl(_) | Item::TraitAlias(_) => {}
            _ => {}
        }
    }
}

fn collect_attrs(attrs: &[syn::Attribute], line: usize, idx: &mut ModuleIndex) {
    for a in attrs {
        let path = a.path();
        let toks = quote::quote!(#a).to_string();
        let s = toks.split_whitespace().collect::<Vec<_>>().join(" ");
        if path.is_ident("cfg") || path.is_ident("cfg_attr") {
            idx.cfgs.push((line, s));
        } else {
            idx.attr_macros.push((line, s));
        }
    }
}
fn collect_lifetimes(g: &syn::Generics, line: usize, idx: &mut ModuleIndex) {
    for p in &g.params {
        if let syn::GenericParam::Lifetime(_) = p {
            idx.lifetimes.push((line, quote::quote!(#g).to_string().split_whitespace().collect::<Vec<_>>().join(" ")));
            break;
        }
    }
}

fn walk_use_tree(tree: &UseTree, prefix: &mut Vec<String>, idx: &mut ModuleIndex, is_pub: bool) {
    match tree {
        UseTree::Path(p) => {
            prefix.push(p.ident.to_string());
            walk_use_tree(&p.tree, prefix, idx, is_pub);
            prefix.pop();
        }
        UseTree::Name(n) => {
            let name = n.ident.to_string();
            let mut path = prefix.clone();
            path.push(name.clone());
            idx.uses.insert(name.clone(), path.clone());
            if is_pub { idx.pub_uses.insert(name, path); }
        }
        UseTree::Rename(r) => {
            let alias = r.rename.to_string();
            let mut path = prefix.clone();
            path.push(r.ident.to_string());
            idx.uses.insert(alias.clone(), path.clone());
            if is_pub { idx.pub_uses.insert(alias, path); }
        }
        UseTree::Glob(_) => {
            idx.glob_uses.push(prefix.clone());
        }
        UseTree::Group(g) => {
            for t in &g.items { walk_use_tree(t, prefix, idx, is_pub); }
        }
    }
}

// Impl block index: per file
#[derive(Debug, Clone)]
struct ImplEntry {
    type_name: String,
    trait_name: Option<String>,
    methods: HashMap<String, (usize, String)>, // name -> (line, signature)
    line: usize,
}

fn index_impls(items: &[Item]) -> Vec<ImplEntry> {
    let mut out = Vec::new();
    for item in items {
        if let Item::Impl(im) = item {
            let type_name = type_path_last(&im.self_ty);
            let trait_name = im.trait_.as_ref().map(|(_, p, _)| {
                p.segments.last().map(|s| s.ident.to_string()).unwrap_or_default()
            });
            let mut methods = HashMap::new();
            for ii in &im.items {
                if let syn::ImplItem::Fn(f) = ii {
                    let line = f.span().start().line;
                    let sig = quote::quote!(#(&f.sig)).to_string();
                    let sig = sig.split_whitespace().collect::<Vec<_>>().join(" ");
                    methods.insert(f.sig.ident.to_string(), (line, sig));
                }
            }
            let line = im.span().start().line;
            if let Some(tn) = type_name {
                out.push(ImplEntry { type_name: tn, trait_name, methods, line });
            }
        }
    }
    out
}

fn type_path_last(ty: &syn::Type) -> Option<String> {
    match ty {
        syn::Type::Path(tp) => tp.path.segments.last().map(|s| s.ident.to_string()),
        syn::Type::Reference(r) => type_path_last(&r.elem),
        syn::Type::Paren(p) => type_path_last(&p.elem),
        _ => None,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Resolver: across files within project root

struct Resolver {
    project_root: PathBuf,
    crates: Vec<CrateInfo>,
    cache: ParseCache,
    /// (file_path) -> ModuleIndex (top-level only; inline mods walked on demand)
    indices: HashMap<PathBuf, ModuleIndex>,
    impls_by_file: HashMap<PathBuf, Vec<ImplEntry>>,
}

impl Resolver {
    fn new(project_root: PathBuf, crates: Vec<CrateInfo>) -> Self {
        Self {
            project_root, crates,
            cache: ParseCache::new(),
            indices: HashMap::new(),
            impls_by_file: HashMap::new(),
        }
    }

    fn display_path(&self, p: &Path) -> String {
        let abs = p.canonicalize().unwrap_or_else(|_| p.to_path_buf());
        match abs.strip_prefix(&self.project_root) {
            Ok(rel) => rel.to_string_lossy().replace('\\', "/"),
            Err(_) => abs.to_string_lossy().replace('\\', "/"),
        }
    }

    fn is_project_local(&self, p: &Path) -> bool {
        let abs = p.canonicalize().unwrap_or_else(|_| p.to_path_buf());
        abs.starts_with(&self.project_root)
    }

    fn index_file(&mut self, file: &Path) -> Result<(), String> {
        let key = file.canonicalize().unwrap_or_else(|_| file.to_path_buf());
        if self.indices.contains_key(&key) { return Ok(()); }
        let f = self.cache.get(file)?.clone();
        let mut idx = ModuleIndex::default();
        index_items(&f.items, &mut idx);
        let impls = index_impls(&f.items);
        self.indices.insert(key.clone(), idx);
        self.impls_by_file.insert(key, impls);
        Ok(())
    }

    /// Resolve `mod foo;` referenced from `parent_file` to a file path.
    fn resolve_mod_file(&self, parent_file: &Path, mod_name: &str) -> Option<PathBuf> {
        for cand in module_file_candidates(parent_file, mod_name) {
            if cand.is_file() {
                return cand.canonicalize().ok();
            }
        }
        None
    }

    /// Find the crate this file belongs to.
    fn crate_of(&self, file: &Path) -> Option<&CrateInfo> {
        let abs = file.canonicalize().unwrap_or_else(|_| file.to_path_buf());
        let mut best: Option<&CrateInfo> = None;
        let mut best_depth: usize = 0;
        for c in &self.crates {
            let root_dir = c.root_file.parent().unwrap_or(&c.crate_dir);
            if abs.starts_with(root_dir) {
                let depth = root_dir.components().count();
                if best.is_none() || depth > best_depth {
                    best = Some(c); best_depth = depth;
                }
            }
        }
        best
    }

    /// Walk a module path (from crate root) to its file, following `mod foo;` declarations.
    fn module_path_to_file(&mut self, crate_info: &CrateInfo, path: &[String]) -> Option<PathBuf> {
        let mut current = crate_info.root_file.clone();
        for seg in path {
            // Ensure current is indexed and we can see its mod_decls
            self.index_file(&current).ok()?;
            let key = current.canonicalize().unwrap_or_else(|_| current.clone());
            let has_decl = self.indices.get(&key)
                .map(|i| i.mod_decls.iter().any(|m| m == seg))
                .unwrap_or(false);
            // try external file
            if has_decl {
                if let Some(child) = self.resolve_mod_file(&current, seg) {
                    current = child;
                    continue;
                }
            }
            // inline mod: not directly supported by file lookup; fall back to "still current file, scoped"
            // We'll mark unresolved for now.
            return None;
        }
        Some(current)
    }

    /// Resolve a path like ["crate", "a", "b", "C"] or ["self", "x"] or ["a", "b"] relative to
    /// the given `from_file`.
    fn resolve_path(
        &mut self,
        from_file: &Path,
        path: &[String],
        visited: &mut BTreeSet<(PathBuf, String)>,
    ) -> ResolveResult {
        if path.is_empty() {
            return ResolveResult { kind: "unresolved".into(), steps: vec![], reason: "empty path".into() };
        }
        let crate_info = match self.crate_of(from_file) {
            Some(c) => c.clone(),
            None => {
                return ResolveResult {
                    kind: "external".into(), steps: vec![],
                    reason: "file not in any known crate".into(),
                };
            }
        };
        let mut working: Vec<String> = path.to_vec();
        let from_module_path = self.module_path_for_file(&crate_info, from_file);
        // Decide start file based on path prefix.
        let start_file: PathBuf = match working[0].as_str() {
            "crate" => { working.remove(0); crate_info.root_file.clone() }
            "self" => {
                working.remove(0);
                self.module_path_to_file(&crate_info, &from_module_path)
                    .unwrap_or_else(|| from_file.to_path_buf())
            }
            "super" => {
                let mut mp = from_module_path.clone();
                while !working.is_empty() && working[0] == "super" {
                    working.remove(0);
                    if mp.is_empty() {
                        return ResolveResult { kind: "external".into(), steps: vec![],
                            reason: "super beyond crate root".into() };
                    }
                    mp.pop();
                }
                self.module_path_to_file(&crate_info, &mp).unwrap_or_else(|| crate_info.root_file.clone())
            }
            other if other == crate_info.name => { working.remove(0); crate_info.root_file.clone() }
            other => {
                // sibling crate?
                let sibling = self.crates.iter().find(|c| c.name == *other).cloned();
                if let Some(sib) = sibling {
                    working.remove(0);
                    return self.walk_from(sib.root_file.clone(), &working,
                        vec![Step {
                            kind: "module-file".into(),
                            file: self.display_path(&sib.root_file),
                            line: 0,
                            name: sib.name.clone(),
                            detail: format!("crate `{}` root", sib.name),
                        }],
                        visited);
                }
                // Not a crate prefix; treat as a name to look up starting from from_file.
                from_file.to_path_buf()
            }
        };
        self.walk_from(start_file, &working, vec![], visited)
    }

    fn resolve_path_in_crate(
        &mut self,
        crate_info: &CrateInfo,
        path: &[String],
        mut steps: Vec<Step>,
        visited: &mut BTreeSet<(PathBuf, String)>,
    ) -> ResolveResult {
        steps.push(Step {
            kind: "module-file".into(),
            file: self.display_path(&crate_info.root_file),
            line: 0,
            name: crate_info.name.clone(),
            detail: format!("crate `{}` root", crate_info.name),
        });
        self.walk_from(crate_info.root_file.clone(), path, steps, visited)
    }

    /// Generic per-segment walker starting from `start_file`. Decides per segment:
    /// child mod → descend; item → record (treat remaining as method); pub-use/use → recurse;
    /// glob-use → best-effort.
    fn walk_from(
        &mut self,
        start_file: PathBuf,
        path: &[String],
        mut steps: Vec<Step>,
        visited: &mut BTreeSet<(PathBuf, String)>,
    ) -> ResolveResult {
        if path.is_empty() {
            return ResolveResult { kind: "unresolved".into(), steps, reason: "empty".into() };
        }
        let mut current_file = start_file;
        let mut i = 0;
        while i < path.len() {
            let seg = path[i].clone();
            if self.index_file(&current_file).is_err() {
                steps.push(Step {
                    kind: "parse-error".into(),
                    file: self.display_path(&current_file),
                    line: 0, name: seg.clone(),
                    detail: "parse failed".into(),
                });
                return ResolveResult { kind: "parse-error".into(), steps, reason: "parse failed".into() };
            }
            let key = current_file.canonicalize().unwrap_or_else(|_| current_file.clone());
            if !visited.insert((key.clone(), seg.clone())) {
                steps.push(Step {
                    kind: "cycle".into(),
                    file: self.display_path(&current_file), line: 0, name: seg.clone(),
                    detail: "cycle in resolution".into(),
                });
                return ResolveResult { kind: "cycle".into(), steps, reason: "cycle".into() };
            }
            let idx = self.indices.get(&key).cloned().unwrap_or_default();

            // (1) item in this module?
            if let Some(it) = idx.items.get(&seg).cloned() {
                if it.kind == "mod" {
                    // mod declaration: descend to its file (if external) or note inline
                    if let Some(child) = self.resolve_mod_file(&current_file, &seg) {
                        steps.push(Step {
                            kind: "module-file".into(),
                            file: self.display_path(&child),
                            line: 0, name: seg.clone(),
                            detail: format!("module `{}`", seg),
                        });
                        current_file = child;
                        i += 1;
                        continue;
                    } else {
                        // inline mod — cannot easily walk further by file path
                        steps.push(Step {
                            kind: "inline-mod".into(),
                            file: self.display_path(&current_file),
                            line: it.line, name: seg.clone(),
                            detail: format!("inline module `{}` (cannot recurse by file)", seg),
                        });
                        return ResolveResult { kind: "inline-mod".into(), steps, reason: "inline mod".into() };
                    }
                }
                // non-mod item
                steps.push(Step {
                    kind: format!("{}-def", it.kind),
                    file: self.display_path(&current_file),
                    line: it.line, name: it.name.clone(),
                    detail: format!("{} `{}`", it.kind, it.name),
                });
                if i + 1 < path.len() {
                    let method = path[i + 1].clone();
                    let cur = current_file.clone();
                    return self.resolve_method_on_type(&cur, &seg, &method, steps, visited);
                }
                return ResolveResult { kind: format!("{}-def", it.kind), steps, reason: String::new() };
            }
            // (2) pub use re-export
            if let Some(u) = idx.pub_uses.get(&seg).cloned() {
                steps.push(Step {
                    kind: "pub-use".into(),
                    file: self.display_path(&current_file),
                    line: 0, name: seg.clone(),
                    detail: format!("pub use {}", u.join("::")),
                });
                let mut combined = u;
                combined.extend(path[i + 1..].iter().cloned());
                let cur = current_file.clone();
                return self.resolve_path(&cur, &combined, visited).extend_with(steps);
            }
            // (3) use
            if let Some(u) = idx.uses.get(&seg).cloned() {
                steps.push(Step {
                    kind: "use".into(),
                    file: self.display_path(&current_file),
                    line: 0, name: seg.clone(),
                    detail: format!("use {}", u.join("::")),
                });
                let mut combined = u;
                combined.extend(path[i + 1..].iter().cloned());
                let cur = current_file.clone();
                return self.resolve_path(&cur, &combined, visited).extend_with(steps);
            }
            // (4) glob use — try each
            let mut tried = false;
            for gp in idx.glob_uses.clone() {
                tried = true;
                let mut try_path = gp.clone();
                try_path.push(seg.clone());
                try_path.extend(path[i + 1..].iter().cloned());
                let cur = current_file.clone();
                let r = self.resolve_path(&cur, &try_path, visited);
                if !matches!(r.kind.as_str(), "unresolved" | "external" | "parse-error") {
                    return r.extend_with(steps);
                }
            }
            let _ = tried;
            steps.push(Step {
                kind: "unresolved".into(),
                file: self.display_path(&current_file),
                line: 0, name: seg.clone(),
                detail: format!("`{}` not found in module", seg),
            });
            return ResolveResult { kind: "unresolved".into(), steps, reason: "not found".into() };
        }
        ResolveResult { kind: "unresolved".into(), steps, reason: "empty after walk".into() }
    }

    /// Map a file back to its module path within its crate.
    fn module_path_for_file(&self, crate_info: &CrateInfo, file: &Path) -> Vec<String> {
        let abs = file.canonicalize().unwrap_or_else(|_| file.to_path_buf());
        let root_dir = crate_info.root_file.parent().unwrap_or(&crate_info.crate_dir);
        let rel = match abs.strip_prefix(root_dir) { Ok(r) => r, Err(_) => return vec![] };
        let mut comps: Vec<String> = rel.components()
            .map(|c| c.as_os_str().to_string_lossy().to_string()).collect();
        if comps.is_empty() { return vec![]; }
        // Map terminal file part
        let last = comps.pop().unwrap();
        let last_stem = last.strip_suffix(".rs").unwrap_or(&last).to_string();
        if last_stem != "mod" && last_stem != "lib" && last_stem != "main" {
            comps.push(last_stem);
        }
        comps
    }

    /// Find impl-method by walking impls in same file as `class-defining` file.
    fn resolve_method_on_type(
        &mut self,
        type_def_file: &Path,
        type_name: &str,
        method: &str,
        mut steps: Vec<Step>,
        visited: &mut BTreeSet<(PathBuf, String)>,
    ) -> ResolveResult {
        let key = type_def_file.canonicalize().unwrap_or_else(|_| type_def_file.to_path_buf());
        if self.index_file(type_def_file).is_err() {
            return ResolveResult { kind: "parse-error".into(), steps, reason: "parse failed".into() };
        }
        let impls = self.impls_by_file.get(&key).cloned().unwrap_or_default();
        // Search inherent impls first
        for im in impls.iter().filter(|i| i.type_name == type_name && i.trait_name.is_none()) {
            if let Some((line, sig)) = im.methods.get(method) {
                steps.push(Step {
                    kind: "impl-method".into(),
                    file: self.display_path(type_def_file),
                    line: *line,
                    name: method.into(),
                    detail: format!("impl {} {{ fn {}{} }}", type_name, method,
                        sig.strip_prefix(&format!("fn {method}")).unwrap_or("")),
                });
                return ResolveResult { kind: "impl-method".into(), steps, reason: String::new() };
            }
        }
        // Then trait impls
        for im in impls.iter().filter(|i| i.type_name == type_name && i.trait_name.is_some()) {
            if let Some((line, sig)) = im.methods.get(method) {
                let tn = im.trait_name.clone().unwrap_or_default();
                steps.push(Step {
                    kind: "trait-method".into(),
                    file: self.display_path(type_def_file),
                    line: *line,
                    name: method.into(),
                    detail: format!("impl {} for {} {{ fn {}{} }}", tn, type_name, method,
                        sig.strip_prefix(&format!("fn {method}")).unwrap_or("")),
                });
                return ResolveResult { kind: "trait-method".into(), steps, reason: String::new() };
            }
        }
        // Not found in same file; also search throughout known indexed files for `impl <Type>`
        // (rare but useful for orphan-impl patterns within the same crate).
        let candidate_files: Vec<PathBuf> = self.impls_by_file.keys().cloned().collect();
        for f in candidate_files {
            if f == key { continue; }
            let impls = self.impls_by_file.get(&f).cloned().unwrap_or_default();
            for im in impls.iter().filter(|i| i.type_name == type_name) {
                if let Some((line, sig)) = im.methods.get(method) {
                    let kind = if im.trait_name.is_some() { "trait-method" } else { "impl-method" };
                    let tn = im.trait_name.clone().unwrap_or_default();
                    let detail = if tn.is_empty() {
                        format!("impl {} {{ fn {}{} }}", type_name, method,
                            sig.strip_prefix(&format!("fn {method}")).unwrap_or(""))
                    } else {
                        format!("impl {} for {} {{ fn {}{} }}", tn, type_name, method,
                            sig.strip_prefix(&format!("fn {method}")).unwrap_or(""))
                    };
                    steps.push(Step {
                        kind: kind.into(),
                        file: self.display_path(&f),
                        line: *line,
                        name: method.into(),
                        detail,
                    });
                    return ResolveResult { kind: kind.into(), steps, reason: String::new() };
                }
            }
        }
        steps.push(Step {
            kind: "unresolved".into(),
            file: self.display_path(type_def_file),
            line: 0,
            name: method.into(),
            detail: format!("method `{}` not found in any impl of `{}`", method, type_name),
        });
        let _ = visited;
        ResolveResult { kind: "unresolved".into(), steps, reason: "method not found".into() }
    }
}

#[derive(Debug, Clone, Serialize)]
struct Step {
    kind: String,
    file: String,
    line: usize,
    name: String,
    detail: String,
}

#[derive(Debug, Clone, Serialize)]
struct ResolveResult {
    kind: String,
    steps: Vec<Step>,
    reason: String,
}
impl ResolveResult {
    fn extend_with(mut self, mut earlier: Vec<Step>) -> Self {
        earlier.append(&mut self.steps);
        self.steps = earlier;
        self
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Find enclosing item (fn/method) at a line

#[derive(Debug, Clone, Serialize)]
struct EnclosingItem {
    kind: String,
    name: String,
    line: usize,
    body_start: usize,
    body_end: usize,
}

fn find_enclosing_item(file: &syn::File, line: usize) -> Option<EnclosingItem> {
    fn check_fn(f: &syn::ItemFn, line: usize) -> Option<EnclosingItem> {
        let s = f.span();
        if line >= s.start().line && line <= s.end().line {
            Some(EnclosingItem {
                kind: "fn".into(),
                name: f.sig.ident.to_string(),
                line: s.start().line,
                body_start: f.block.span().start().line,
                body_end: f.block.span().end().line,
            })
        } else { None }
    }
    fn check_impl_fn(f: &syn::ImplItemFn, ty_name: &str, line: usize) -> Option<EnclosingItem> {
        let s = f.span();
        if line >= s.start().line && line <= s.end().line {
            Some(EnclosingItem {
                kind: "impl-method".into(),
                name: format!("{}::{}", ty_name, f.sig.ident),
                line: s.start().line,
                body_start: f.block.span().start().line,
                body_end: f.block.span().end().line,
            })
        } else { None }
    }
    let mut best: Option<EnclosingItem> = None;
    fn smaller(a: &EnclosingItem, b: &EnclosingItem) -> bool {
        (a.body_end - a.body_start) < (b.body_end - b.body_start)
    }
    for it in &file.items {
        match it {
            Item::Fn(f) => {
                if let Some(ei) = check_fn(f, line) {
                    if best.as_ref().map(|b| smaller(&ei, b)).unwrap_or(true) {
                        best = Some(ei);
                    }
                }
            }
            Item::Impl(im) => {
                let ty_name = type_path_last(&im.self_ty).unwrap_or_default();
                for ii in &im.items {
                    if let syn::ImplItem::Fn(f) = ii {
                        if let Some(ei) = check_impl_fn(f, &ty_name, line) {
                            if best.as_ref().map(|b| smaller(&ei, b)).unwrap_or(true) {
                                best = Some(ei);
                            }
                        }
                    }
                }
            }
            Item::Mod(m) => {
                if let Some((_, items)) = &m.content {
                    for it in items {
                        if let Item::Fn(f) = it {
                            if let Some(ei) = check_fn(f, line) {
                                if best.as_ref().map(|b| smaller(&ei, b)).unwrap_or(true) {
                                    best = Some(ei);
                                }
                            }
                        }
                    }
                }
            }
            _ => {}
        }
    }
    best
}

// ─────────────────────────────────────────────────────────────────────────────
// Payload

#[derive(Debug, Serialize)]
struct VarReport {
    name: String,
    uses: Vec<usize>,
    origin: Vec<OriginEntry>,
    chain: Vec<Step>,
    annotation: Option<String>,
    resolution: String,
}

#[derive(Debug, Serialize)]
struct OriginEntry {
    line: usize,
    kind: String,
    detail: String,
}

#[derive(Debug, Serialize)]
struct CallReport {
    callee: String,
    line: usize,
    chain: Vec<Step>,
    kind: String,
}

#[derive(Debug, Serialize)]
struct Payload {
    file: String,
    project_root: String,
    range: (usize, usize),
    crate_name: Option<String>,
    enclosing: Option<EnclosingItem>,
    source_lines: Vec<(usize, String)>,
    variable_origins: Vec<VarReport>,
    call_bindings: Vec<CallReport>,
    invariants: Invariants,
    notes: Vec<String>,
}

// ─────────────────────────────────────────────────────────────────────────────
// Driver

fn run(args: Args) -> Result<String, String> {
    let file_abs = args.file.canonicalize().map_err(|e| format!("file not found: {e}"))?;
    let project_root = find_project_root(&file_abs, args.project_root.as_deref());
    let project_root = project_root.canonicalize().unwrap_or(project_root);
    let crates = discover_crates(&project_root);
    let crate_for_file = crates.iter().find(|c| {
        let root_dir = c.root_file.parent().unwrap_or(&c.crate_dir);
        file_abs.starts_with(root_dir)
    }).cloned();

    let mut resolver = Resolver::new(project_root.clone(), crates.clone());
    resolver.index_file(&file_abs)?;

    let src = fs::read_to_string(&file_abs).map_err(|e| format!("read: {e}"))?;
    let parsed = resolver.cache.get(&file_abs)?.clone();
    let enclosing = find_enclosing_item(&parsed, args.range.0);

    // Source lines slice
    let source_lines: Vec<(usize, String)> = src.lines().enumerate()
        .filter(|(i, _)| {
            let ln = i + 1;
            ln >= args.range.0 && ln <= args.range.1
        })
        .map(|(i, l)| (i + 1, l.to_string()))
        .collect();

    // Collect references in range
    let mut rc = ReferenceCollector { range: args.range, refs: vec![] };
    rc.visit_file(&parsed);

    // Collect local bindings + invariants by walking enclosing item only
    let mut scope = LocalScopeVisitor {
        range: args.range,
        bindings: vec![],
        invariants: Invariants::default(),
    };
    // Function-level params
    if let Some(enc) = &enclosing {
        // Walk again to find that exact fn and collect its params
        struct Locate<'a> {
            target: &'a EnclosingItem,
            collector: &'a mut LocalScopeVisitor,
        }
        impl<'ast, 'a> Visit<'ast> for Locate<'a> {
            fn visit_item_fn(&mut self, n: &'ast syn::ItemFn) {
                if n.sig.ident == self.target.name.as_str() && n.span().start().line == self.target.line {
                    for input in &n.sig.inputs {
                        if let syn::FnArg::Typed(pt) = input {
                            let mut new_bindings = Vec::new();
                            collect_pat_bindings(&pt.pat, Some(&pt.ty), &mut new_bindings, "param");
                            for b in &mut new_bindings {
                                b.detail = format!("param of `{}`", self.target.name);
                                self.collector.invariants.type_annotations.push((b.line, format!("param {}: {}", b.name, pretty_type(&pt.ty))));
                                if b.is_mut {
                                    self.collector.invariants.mut_bindings.push((b.line, format!("mut param `{}`", b.name)));
                                }
                            }
                            self.collector.bindings.extend(new_bindings);
                        } else if let syn::FnArg::Receiver(r) = input {
                            let line = r.span().start().line;
                            self.collector.bindings.push(Binding {
                                name: "self".into(),
                                kind: "param".into(), line,
                                detail: "self receiver".into(),
                                annotation: r.colon_token.is_some()
                                    .then(|| pretty_type(&r.ty)),
                                is_mut: r.mutability.is_some(),
                                use_path: None,
                            });
                        }
                    }
                    // return type
                    if let syn::ReturnType::Type(_, ty) = &n.sig.output {
                        self.collector.invariants.type_annotations.push((n.sig.span().start().line, format!("return of `{}`: {}", self.target.name, pretty_type(ty))));
                    }
                    // lifetimes
                    if n.sig.generics.params.iter().any(|p| matches!(p, syn::GenericParam::Lifetime(_))) {
                        self.collector.invariants.lifetimes.push((n.sig.span().start().line,
                            format!("fn `{}` has lifetime params", self.target.name)));
                    }
                    // attrs
                    for a in &n.attrs {
                        let s = quote::quote!(#a).to_string().split_whitespace().collect::<Vec<_>>().join(" ");
                        if a.path().is_ident("cfg") || a.path().is_ident("cfg_attr") {
                            self.collector.invariants.cfg_gates.push((n.sig.span().start().line, s));
                        } else {
                            self.collector.invariants.attribute_macros.push((n.sig.span().start().line, s));
                        }
                    }
                    syn::visit::visit_block(self.collector, &n.block);
                } else {
                    syn::visit::visit_item_fn(self, n);
                }
            }
            fn visit_impl_item_fn(&mut self, n: &'ast syn::ImplItemFn) {
                let span_line = n.span().start().line;
                let want = self.target.name.rsplit("::").next().unwrap_or("");
                if span_line == self.target.line && n.sig.ident == want {
                    // similar to ItemFn handling
                    for input in &n.sig.inputs {
                        if let syn::FnArg::Typed(pt) = input {
                            let mut new_bindings = Vec::new();
                            collect_pat_bindings(&pt.pat, Some(&pt.ty), &mut new_bindings, "param");
                            for b in &mut new_bindings {
                                b.detail = format!("param of `{}`", self.target.name);
                                self.collector.invariants.type_annotations.push((b.line, format!("param {}: {}", b.name, pretty_type(&pt.ty))));
                                if b.is_mut { self.collector.invariants.mut_bindings.push((b.line, format!("mut param `{}`", b.name))); }
                            }
                            self.collector.bindings.extend(new_bindings);
                        } else if let syn::FnArg::Receiver(r) = input {
                            let line = r.span().start().line;
                            self.collector.bindings.push(Binding {
                                name: "self".into(), kind: "param".into(), line,
                                detail: "self receiver".into(),
                                annotation: None,
                                is_mut: r.mutability.is_some(),
                                use_path: None,
                            });
                        }
                    }
                    if let syn::ReturnType::Type(_, ty) = &n.sig.output {
                        self.collector.invariants.type_annotations.push((n.sig.span().start().line,
                            format!("return of `{}`: {}", self.target.name, pretty_type(ty))));
                    }
                    syn::visit::visit_block(self.collector, &n.block);
                } else {
                    syn::visit::visit_impl_item_fn(self, n);
                }
            }
        }
        let mut loc = Locate { target: enc, collector: &mut scope };
        loc.visit_file(&parsed);
    } else {
        // Top-level: walk whole file for invariants but no params
        scope.visit_file(&parsed);
    }

    // Reduce references to unique names (with full_path) — keep first occurrence
    let mut variable_origins: Vec<VarReport> = Vec::new();
    let mut call_bindings: Vec<CallReport> = Vec::new();

    // Group references by (name, full_path)
    let mut grouped: BTreeMap<(String, Vec<String>, bool), Vec<&Reference>> = BTreeMap::new();
    for r in &rc.refs {
        // skip method `name` themselves (we record receiver+method separately below)
        if r.method_receiver.is_some() { continue; }
        grouped.entry((r.name.clone(), r.full_path.clone(), r.is_call)).or_default().push(r);
    }
    let file_idx_key = file_abs.canonicalize().unwrap_or(file_abs.clone());
    let file_idx = resolver.indices.get(&file_idx_key).cloned().unwrap_or_default();

    // Resolve grouped names
    for ((name, full_path, is_call), refs) in &grouped {
        // Local binding?
        let local = scope.bindings.iter().rev().find(|b| b.name == *name);
        let uses: Vec<usize> = refs.iter().map(|r| r.line).collect();
        if let Some(b) = local {
            if !is_call {
                variable_origins.push(VarReport {
                    name: name.clone(), uses,
                    origin: vec![OriginEntry { line: b.line, kind: b.kind.clone(), detail: b.detail.clone() }],
                    chain: vec![Step {
                        kind: format!("binding-{}", b.kind),
                        file: resolver.display_path(&file_abs),
                        line: b.line,
                        name: b.name.clone(),
                        detail: b.detail.clone(),
                    }],
                    annotation: b.annotation.clone(),
                    resolution: "local".into(),
                });
            } else {
                call_bindings.push(CallReport {
                    callee: name.clone(),
                    line: refs[0].line,
                    chain: vec![Step {
                        kind: format!("binding-{}", b.kind),
                        file: resolver.display_path(&file_abs),
                        line: b.line,
                        name: b.name.clone(),
                        detail: b.detail.clone(),
                    }],
                    kind: "local-call".into(),
                });
            }
            continue;
        }
        // Resolve via file's use / module items
        let mut chain: Vec<Step> = vec![];
        let mut path_to_resolve: Vec<String> = full_path.clone();
        if full_path.len() == 1 {
            if let Some(u) = file_idx.uses.get(name).cloned() {
                chain.push(Step {
                    kind: "use".into(),
                    file: resolver.display_path(&file_abs),
                    line: 0,
                    name: name.clone(),
                    detail: format!("use {}", u.join("::")),
                });
                path_to_resolve = u;
            } else if let Some(_it) = file_idx.items.get(name) {
                // defined in this file
                let it = file_idx.items.get(name).unwrap().clone();
                chain.push(Step {
                    kind: format!("{}-def", it.kind),
                    file: resolver.display_path(&file_abs),
                    line: it.line,
                    name: it.name.clone(),
                    detail: format!("{} `{}`", it.kind, it.name),
                });
                if *is_call {
                    call_bindings.push(CallReport {
                        callee: name.clone(), line: refs[0].line,
                        chain, kind: format!("{}-call", it.kind),
                    });
                } else {
                    variable_origins.push(VarReport {
                        name: name.clone(), uses,
                        origin: vec![OriginEntry { line: it.line, kind: it.kind.clone(), detail: format!("{} `{}`", it.kind, it.name) }],
                        chain, annotation: None, resolution: "module".into(),
                    });
                }
                continue;
            } else {
                // Could be a sibling crate name, std, builtin, or unresolved
                if STD_PRELUDE.contains(&name.as_str()) {
                    let chain = vec![Step {
                        kind: "std-prelude".into(),
                        file: "<std prelude>".into(),
                        line: 0, name: name.clone(),
                        detail: "item from Rust standard prelude".into(),
                    }];
                    if *is_call {
                        call_bindings.push(CallReport { callee: name.clone(), line: refs[0].line, chain, kind: "std-prelude".into() });
                    } else {
                        variable_origins.push(VarReport {
                            name: name.clone(), uses, origin: vec![],
                            chain, annotation: None, resolution: "std-prelude".into(),
                        });
                    }
                    continue;
                }
                let mut visited = BTreeSet::new();
                let r = resolver.resolve_path(&file_abs, &[name.clone()], &mut visited);
                if matches!(r.kind.as_str(), "external" | "unresolved") {
                    // mark external/unresolved
                    let chain = r.steps;
                    if *is_call {
                        call_bindings.push(CallReport {
                            callee: name.clone(), line: refs[0].line,
                            chain, kind: "external-or-unresolved".into(),
                        });
                    } else {
                        variable_origins.push(VarReport {
                            name: name.clone(), uses,
                            origin: vec![],
                            chain, annotation: None,
                            resolution: "external-or-unresolved".into(),
                        });
                    }
                    continue;
                } else {
                    let chain = r.steps;
                    if *is_call {
                        call_bindings.push(CallReport {
                            callee: name.clone(), line: refs[0].line,
                            chain, kind: r.kind.clone(),
                        });
                    } else {
                        variable_origins.push(VarReport {
                            name: name.clone(), uses, origin: vec![],
                            chain, annotation: None, resolution: r.kind.clone(),
                        });
                    }
                    continue;
                }
            }
        }
        // multi-segment path: expand head if it's a `use` alias
        let mut visited = BTreeSet::new();
        if let Some(head) = path_to_resolve.first().cloned() {
            if let Some(u) = file_idx.uses.get(&head).cloned() {
                let tail = path_to_resolve[1..].to_vec();
                let mut full = u;
                full.extend(tail);
                path_to_resolve = full;
            }
        }
        let r = resolver.resolve_path(&file_abs, &path_to_resolve, &mut visited);
        for s in r.steps { chain.push(s); }
        if *is_call {
            call_bindings.push(CallReport {
                callee: full_path.join("::"),
                line: refs[0].line,
                chain, kind: r.kind.clone(),
            });
        } else {
            variable_origins.push(VarReport {
                name: name.clone(), uses, origin: vec![],
                chain, annotation: None, resolution: r.kind.clone(),
            });
        }
    }

    // Method calls — resolve method on receiver's type if discoverable
    for r in &rc.refs {
        if r.method_receiver.is_none() { continue; }
        let recv = r.method_receiver.as_ref().unwrap();
        let method = r.method_name.clone().unwrap_or_default();
        let mut chain: Vec<Step> = vec![];
        // 1) find receiver binding
        let local = scope.bindings.iter().rev().find(|b| b.name == recv.name);
        let mut type_def_file: Option<PathBuf> = None;
        let mut type_name: Option<String> = None;
        if let Some(b) = local {
            chain.push(Step {
                kind: format!("binding-{}", b.kind),
                file: resolver.display_path(&file_abs),
                line: b.line, name: b.name.clone(), detail: b.detail.clone(),
            });
            // a) explicit annotation
            if let Some(ann) = &b.annotation {
                // parse type's last segment as name
                if let Ok(ty) = syn::parse_str::<syn::Type>(ann) {
                    if let Some(tn) = type_path_last(&ty) { type_name = Some(tn); }
                }
            }
            // b) detail like "let x = T::new(...)" or "let x = T { ... }"
            if type_name.is_none() {
                // crude heuristic on detail
                let det = &b.detail;
                if let Some(eq) = det.find('=') {
                    let rhs = det[eq+1..].trim();
                    // T::new(...) or T(...)
                    let first_tok: String = rhs.chars().take_while(|c| c.is_alphanumeric() || *c == '_' || *c == ':').collect();
                    let head = first_tok.split("::").next().unwrap_or("").to_string();
                    if !head.is_empty() && head.chars().next().map_or(false, |c| c.is_uppercase()) {
                        type_name = Some(head);
                    }
                }
            }
            // c) resolve type_name → file (and capture the real underlying name)
            if let Some(tn) = &type_name {
                let mut visited = BTreeSet::new();
                let mut path = vec![tn.clone()];
                if let Some(u) = file_idx.uses.get(tn).cloned() { path = u; }
                let rr = resolver.resolve_path(&file_abs, &path, &mut visited);
                // Update type_name to the actual resolved type (e.g. alias `Service` -> `UserService`)
                for s in &rr.steps {
                    if s.kind.ends_with("-def") && s.line > 0
                       && matches!(s.kind.as_str(), "struct-def" | "enum-def" | "trait-def" | "type-alias-def")
                    {
                        type_name = Some(s.name.clone());
                        type_def_file = Some(resolver.project_root.join(s.file.replace('/', std::path::MAIN_SEPARATOR_STR)));
                    }
                }
                for s in rr.steps { chain.push(s); }
            }
        }
        // 2) lookup method on type
        let mut kind = "unresolved-method".to_string();
        if let (Some(tdf), Some(tn)) = (type_def_file.clone(), type_name.clone()) {
            if tdf.is_file() {
                let mut visited = BTreeSet::new();
                let mr = resolver.resolve_method_on_type(&tdf, &tn, &method, vec![], &mut visited);
                kind = mr.kind.clone();
                for s in mr.steps { chain.push(s); }
            }
        }
        // If we couldn't resolve a type, still report the call with what we have
        call_bindings.push(CallReport {
            callee: format!("{}.{}", recv.name, method),
            line: r.line, chain, kind,
        });
    }

    // Walk full file for `mod` decls' lifetimes/cfg/attrs at item level near range
    let mut notes: Vec<String> = vec![];
    if let Some(c) = &crate_for_file {
        scope.invariants.lifetimes.extend(file_idx.lifetimes.iter().filter(|(l, _)| *l >= args.range.0 && *l <= args.range.1).cloned());
        scope.invariants.cfg_gates.extend(file_idx.cfgs.iter().filter(|(l, _)| *l >= args.range.0 && *l <= args.range.1).cloned());
        scope.invariants.attribute_macros.extend(file_idx.attr_macros.iter().filter(|(l, _)| *l >= args.range.0 && *l <= args.range.1).cloned());
        notes.push(format!("crate: `{}`", c.name));
    } else {
        notes.push("file not inside a known crate; resolution limited to single-file".into());
    }

    let payload = Payload {
        file: resolver.display_path(&file_abs),
        project_root: project_root.display().to_string(),
        range: args.range,
        crate_name: crate_for_file.map(|c| c.name),
        enclosing,
        source_lines,
        variable_origins,
        call_bindings,
        invariants: scope.invariants,
        notes,
    };

    if args.json {
        Ok(serde_json::to_string_pretty(&payload).map_err(|e| e.to_string())?)
    } else {
        Ok(render_markdown(&payload))
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Markdown rendering

fn render_markdown(p: &Payload) -> String {
    let mut o = String::new();
    let push = |o: &mut String, s: &str| { o.push_str(s); o.push('\n'); };
    push(&mut o, &format!("# Trace: {}:L{}-L{} (Rust)", p.file, p.range.0, p.range.1));
    push(&mut o, "");
    push(&mut o, &format!("> Project root: `{}`", p.project_root));
    if let Some(cn) = &p.crate_name {
        push(&mut o, &format!("> Crate: `{}`", cn));
    }
    if let Some(enc) = &p.enclosing {
        push(&mut o, &format!("> Enclosing: {} `{}` (L{}-L{})", enc.kind, enc.name, enc.body_start, enc.body_end));
    }
    push(&mut o, "");
    push(&mut o, "## Source");
    push(&mut o, "");
    push(&mut o, "```rust");
    for (ln, line) in &p.source_lines {
        push(&mut o, &format!("{} | {}", ln, line));
    }
    push(&mut o, "```");
    push(&mut o, "");

    if !p.variable_origins.is_empty() {
        push(&mut o, "## Variable origins");
        push(&mut o, "");
        for v in &p.variable_origins {
            let uses = v.uses.iter().map(|u| format!("L{u}")).collect::<Vec<_>>().join(", ");
            push(&mut o, &format!("- `{}` — used at {}", v.name, uses));
            push(&mut o, &format!("  - resolution: {}", v.resolution));
            if let Some(o2) = v.origin.first() {
                push(&mut o, &format!("  - origin: L{} ({}) — `{}`", o2.line, o2.kind, o2.detail));
            }
            if let Some(ann) = &v.annotation {
                push(&mut o, &format!("  - annotation: `{}`", ann));
            }
            if v.chain.len() >= 2 || (v.chain.len() == 1 && v.resolution != "local") {
                push(&mut o, "  - resolution chain:");
                render_chain(&mut o, &v.chain);
            }
        }
        push(&mut o, "");
    }

    if !p.call_bindings.is_empty() {
        push(&mut o, "## Call bindings");
        push(&mut o, "");
        for c in &p.call_bindings {
            push(&mut o, &format!("- `{}(...)` at L{} — {}", c.callee, c.line, c.kind));
            render_chain(&mut o, &c.chain);
        }
        push(&mut o, "");
    }

    let inv = &p.invariants;
    let mut section = |title: &str, items: &[(usize, String)], o: &mut String| {
        if items.is_empty() { return; }
        o.push_str("## ");
        o.push_str(title);
        o.push('\n');
        o.push('\n');
        for (line, det) in items {
            o.push_str(&format!("- L{}: {}\n", line, det));
        }
        o.push('\n');
    };
    section("Unsafe blocks", &inv.unsafe_blocks, &mut o);
    section("Error propagation (?)", &inv.try_propagations, &mut o);
    section("Panic surfaces", &inv.panic_surfaces, &mut o);
    section("Mutable bindings", &inv.mut_bindings, &mut o);
    section("Type annotations", &inv.type_annotations, &mut o);
    section("Lifetimes", &inv.lifetimes, &mut o);
    section("cfg gates", &inv.cfg_gates, &mut o);
    section("Attribute macros", &inv.attribute_macros, &mut o);
    section("Side effects", &inv.side_effects, &mut o);

    if !p.notes.is_empty() {
        o.push_str("## Notes\n\n");
        for n in &p.notes { o.push_str(&format!("- {}\n", n)); }
    }
    o
}

fn render_chain(o: &mut String, chain: &[Step]) {
    for (i, s) in chain.iter().enumerate() {
        let arrow = if i == 0 { "    -" } else { "    →" };
        if s.line > 0 {
            o.push_str(&format!("{} `{}` ({}) at {}:L{} — {}\n",
                arrow, s.name, s.kind, s.file, s.line, s.detail));
        } else {
            o.push_str(&format!("{} `{}` ({}) at {} — {}\n",
                arrow, s.name, s.kind, s.file, s.detail));
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────

fn main() -> ExitCode {
    let args = match parse_args() {
        Ok(a) => a,
        Err(e) => {
            if !e.is_empty() { eprintln!("error: {e}"); }
            return ExitCode::from(2);
        }
    };
    match run(args) {
        Ok(out) => { print!("{out}"); ExitCode::SUCCESS }
        Err(e) => { eprintln!("error: {e}"); ExitCode::from(1) }
    }
}
