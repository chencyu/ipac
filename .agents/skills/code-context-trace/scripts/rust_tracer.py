"""Dispatcher to the compiled Rust tracer binary.

Auto-builds the binary on first use via cargo. Requires Rust toolchain
(rustc/cargo) on PATH. MSRV: 1.70+.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUST_DIR = HERE / "rust_tracer"
BIN_NAME = "ctt_rust.exe" if os.name == "nt" else "ctt_rust"
BIN_PATH = RUST_DIR / "target" / "release" / BIN_NAME


def _ensure_binary() -> Path:
    if BIN_PATH.is_file():
        return BIN_PATH
    cargo = shutil.which("cargo")
    if not cargo:
        sys.stderr.write(
            "error: Rust toolchain not found. Install via rustup or scoop "
            "(`scoop install rustup`, then `rustup default stable`), then retry.\n"
        )
        sys.exit(127)
    sys.stderr.write(f"[code-context-trace] building Rust tracer (one-time) in {RUST_DIR} ...\n")
    sys.stderr.flush()
    proc = subprocess.run(
        [cargo, "build", "--release", "--quiet"],
        cwd=str(RUST_DIR),
    )
    if proc.returncode != 0 or not BIN_PATH.is_file():
        sys.stderr.write("error: cargo build failed for ctt_rust.\n")
        sys.exit(proc.returncode or 1)
    sys.stderr.write("[code-context-trace] build OK.\n")
    return BIN_PATH


def trace_file(file_path: str, line_range: tuple[int, int], *, as_json: bool, project_root: str | None) -> str:
    binary = _ensure_binary()
    args = [str(binary), file_path, f"L{line_range[0]}-L{line_range[1]}"]
    if as_json:
        args.append("--json")
    if project_root:
        args.extend(["--project-root", project_root])
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    return proc.stdout
