"""Oracle connection helpers shared by the workshop notebooks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OracleSettings:
    user: str
    password: str
    dsn: str


def load_env(path: str | Path = ".env") -> None:
    """Load a local .env file if python-dotenv is installed and the file exists."""

    env_path = Path(path)
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path)


def oracle_settings() -> OracleSettings:
    """Return Oracle connection settings from environment variables."""

    return OracleSettings(
        user=os.environ.get("DB_USER", "VECTOR"),
        password=os.environ.get("DB_PASSWORD", "VectorPwd_2025"),
        dsn=os.environ.get("DB_CONNECT_STRING", "localhost:1526/FREEPDB1"),
    )


def connect():
    """Open a python-oracledb connection using workshop environment variables."""

    import oracledb

    settings = oracle_settings()
    return oracledb.connect(user=settings.user, password=settings.password, dsn=settings.dsn)
