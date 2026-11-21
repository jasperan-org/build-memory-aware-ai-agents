"""Small readiness check for the Designing and Building Memory for AI Agents attendee package."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from . import use_utf8_output
from .connection import load_env, oracle_settings


def _yes(ok: bool) -> str:
    return "✓" if ok else "✗"


def check_files(root: Path) -> bool:
    required = [
        "pyproject.toml",
        ".env.example",
        "docker-compose.yml",
        "notebooks/01_oamp_memory_agent.ipynb",
        "notebooks/02_skillbox_toolbox.ipynb",
        "notebooks/03_synthetic_memory_bootstrap.ipynb",
        "slides/agentic-memory-management.md",
        "scripts/preflight.sh",
        "scripts/setup_oracle.sh",
        "scripts/load_onnx_model.py",
        "scripts/synthesize_memory.py",
    ]
    ok = True
    for rel in required:
        exists = (root / rel).exists()
        ok = ok and exists
        print(f"{_yes(exists)} {rel}")
    return ok


def check_imports() -> bool:
    modules = ["oracledb", "oracleagentmemory", "dotenv", "onnx2oracle"]
    ok = True
    for name in modules:
        exists = importlib.util.find_spec(name) is not None
        ok = ok and exists
        print(f"{_yes(exists)} import {name}")
    return ok


def check_kernel() -> bool:
    """The notebooks ask for the `agentic-memory` kernel; it must run this environment's Python."""

    import sys

    from .kernel import KERNEL_NAME

    try:
        from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
    except ImportError:
        print("✗ Jupyter is not installed. Run: uv sync --all-extras")
        return False
    try:
        argv0 = KernelSpecManager().get_kernel_spec(KERNEL_NAME).argv[0]
    except NoSuchKernel:
        argv0 = ""
    # Same environment = same bin/ directory (python vs python3 differ by name only). No resolve():
    # every venv's python symlinks to the same base interpreter.
    ok = bool(argv0) and Path(argv0).absolute().parent == Path(sys.executable).absolute().parent
    print(f"{_yes(ok)} Jupyter kernel '{KERNEL_NAME}' runs this environment's Python")
    if not ok:
        print("  Run: uv run workshop-kernel")
    return ok


def check_env() -> bool:
    settings = oracle_settings()
    env_ok = all([settings.user, settings.password, settings.dsn])
    print(f"{_yes(env_ok)} DB_USER/DB_PASSWORD/DB_CONNECT_STRING present")
    return env_ok


def check_llm() -> bool:
    """Make one live call with OAMP_LLM, so a green check means the Lab 1 LLM cells will run."""

    from .llm import ping

    ok, detail = ping()
    print(f"{_yes(ok)} LLM call: {detail}")
    if not ok:
        print("  Fix OAMP_LLM and its key in .env (see .env.example), or pass --skip-llm to check the rest.")
    return ok


def check_vector_pool(conn) -> bool:
    """Build and drop a throwaway HNSW index: proves the vector memory pool can hold one."""

    cur = conn.cursor()

    def drop_probe() -> None:
        try:
            cur.execute("DROP TABLE workshop_hnsw_probe PURGE")
        except Exception:
            pass

    drop_probe()
    try:
        cur.execute("CREATE TABLE workshop_hnsw_probe (v VECTOR(3, FLOAT32))")
        cur.execute("INSERT INTO workshop_hnsw_probe VALUES ('[1,0,0]')")
        cur.execute(
            "CREATE VECTOR INDEX workshop_hnsw_probe_v ON workshop_hnsw_probe(v) "
            "ORGANIZATION INMEMORY NEIGHBOR GRAPH DISTANCE COSINE"
        )
        ok, detail = True, "HNSW vector index allocates (vector memory pool is sized)"
    except Exception as exc:
        ok, detail = False, f"HNSW vector index failed: {str(exc).splitlines()[0]}"
    finally:
        drop_probe()
    print(f"{_yes(ok)} {detail}")
    if not ok:
        print("  Run scripts/setup_oracle.sh: it sizes vector_memory_size and restarts Oracle once.")
    return ok


def check_oracle() -> bool:
    try:
        from .connection import connect
        from .oracle_version import is_expected_release

        with connect() as conn:
            row = conn.cursor().execute("SELECT 1 FROM DUAL").fetchone()
            print("✓ Oracle connection works")
            release_ok, banner = is_expected_release(conn)
            print(f"{_yes(release_ok)} Oracle AI Database release-26 marker present")
            if not release_ok:
                print("  Recreate with scripts/setup_oracle.sh after `docker compose down -v` or `podman compose down -v`.")
            pool_ok = check_vector_pool(conn)
    except Exception as exc:  # pragma: no cover - depends on local services
        print(f"✗ Oracle connection failed: {exc}")
        return False
    return row == (1,) and release_ok and pool_ok


def check_onnx_model() -> bool:
    try:
        from .connection import connect
        from .onnx import configured_model_name, embedding_sample, model_registered

        model_name = configured_model_name()
        with connect() as conn:
            registered = model_registered(conn, model_name)
            print(f"{_yes(registered)} ONNX model registered: {model_name}")
            if not registered:
                print("  Run: uv run python scripts/load_onnx_model.py")
                return False
            sample = embedding_sample(conn, model_name)
            print(f"✓ VECTOR_EMBEDDING sample: {sample}...")
        return True
    except Exception as exc:  # pragma: no cover - depends on local services
        print(f"✗ ONNX model check failed: {exc}")
        return False


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Skip imports and Oracle connection.")
    parser.add_argument("--require-onnx", action="store_true", help="Fail unless the in-database ONNX model is loaded and callable.")
    parser.add_argument("--skip-llm", action="store_true", help="Skip the live OAMP_LLM call.")
    parser.add_argument("--root", default=Path.cwd(), type=Path, help="Attendee repo root.")
    args = parser.parse_args(argv)

    load_env(args.root / ".env")
    print("File checks:")
    ok = check_files(args.root)

    if not args.offline:
        print("\nPython dependency checks:")
        ok = check_imports() and ok
        ok = check_kernel() and ok
        print("\nEnvironment checks:")
        ok = check_env() and ok
        if not args.skip_llm:
            ok = check_llm() and ok
        print("\nOracle checks:")
        oracle_ok = check_oracle()
        ok = oracle_ok and ok
        if args.require_onnx:
            print("\nONNX model checks:")
            ok = check_onnx_model() and ok

    print("\n" + ("All requested checks passed." if ok else "Some checks failed."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
