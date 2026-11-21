#!/usr/bin/env python3
"""Load the workshop embedding ONNX model into Oracle AI Database.

This script runs the `onnx2oracle` CLI in-process because that tool builds the
Oracle-safe augmented ONNX graph: tokenizer + transformer + pooling + normalization
in one model. The workshop's toolbox/skillbox SQL uses this model through
`VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING :text AS DATA)`.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace

from agentic_memory_workshop import use_utf8_output
from agentic_memory_workshop.connection import connect, load_env, oracle_settings
from agentic_memory_workshop.onnx import configured_model_name, embedding_sample, model_registered

ROOT = Path(__file__).resolve().parent.parent


class _ClosedNamedTemporaryFile:
    """Stand-in for `tempfile.NamedTemporaryFile(delete=False)` that holds no open handle.

    onnx2oracle 0.1.0/0.1.1 deletes the file inside the `with` block while it is still open.
    Windows refuses that (WinError 32); onnx2oracle main fixes it, but is unreleased.
    Only installed on Windows with those versions; inert elsewhere.
    """

    def __init__(self, suffix: str | None = None, **_: object) -> None:
        fd, self.name = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

    def __enter__(self) -> "_ClosedNamedTemporaryFile":
        return self

    def __exit__(self, *exc: object) -> None:
        try:
            os.unlink(self.name)
        except FileNotFoundError:
            pass


def patch_onnx2oracle_tempfile() -> None:
    if sys.platform != "win32":
        return
    if importlib.metadata.version("onnx2oracle") not in ("0.1.0", "0.1.1"):
        return
    import onnx2oracle.pipeline as pipeline

    pipeline.tempfile = SimpleNamespace(
        mkdtemp=tempfile.mkdtemp, NamedTemporaryFile=_ClosedNamedTemporaryFile
    )


def run_onnx2oracle(preset: str, dsn: str) -> int:
    print("$ onnx2oracle load", preset, "--dsn", dsn, "--force")
    try:
        patch_onnx2oracle_tempfile()
        from onnx2oracle.cli import app

        app(["load", preset, "--dsn", dsn, "--force"], prog_name="onnx2oracle")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        return exc.code if isinstance(exc.code, int) else 1
    except Exception:
        traceback.print_exc()
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        default=os.environ.get("ORACLE_EMBED_PRESET", "all-MiniLM-L12-v2"),
        help="onnx2oracle preset to load. Default: all-MiniLM-L12-v2.",
    )
    parser.add_argument("--force", action="store_true", help="Reload the model even if it exists.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-load SQL verification.")
    args = parser.parse_args(argv)

    load_env(ROOT / ".env")
    settings = oracle_settings()
    full_dsn = f"{settings.user}/{settings.password}@{settings.dsn}"
    expected_model = configured_model_name()

    if not args.force:
        try:
            with connect() as conn:
                if model_registered(conn, expected_model):
                    print(f"✓ {expected_model} is already registered. Use --force to reload.")
                    if not args.skip_verify:
                        print(f"✓ sample embedding: {embedding_sample(conn, expected_model)}...")
                    return 0
        except Exception as exc:
            print(f"Pre-check could not verify model state yet: {exc}")

    rc = run_onnx2oracle(args.preset, full_dsn)
    if rc != 0:
        print("onnx2oracle load failed. Check Docker/Oracle logs and rerun SETUP.md step 6.", file=sys.stderr)
        return rc

    if args.skip_verify:
        return 0

    with connect() as conn:
        if not model_registered(conn, expected_model):
            print(f"Load finished but {expected_model} was not visible in USER_MINING_MODELS.", file=sys.stderr)
            return 2
        print(f"✓ {expected_model} registered")
        print(f"✓ sample embedding: {embedding_sample(conn, expected_model)}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
