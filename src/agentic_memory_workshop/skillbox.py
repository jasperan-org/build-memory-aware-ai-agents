"""Minimal skillbox registry used in the workshop mini-lab.

A skill is a prose playbook. The agent sees a compact manifest retrieved by
vector search, then loads the full body only when it needs that skill.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

EMBED_MODEL = os.environ.get("WORKSHOP_EMBED_MODEL", "ALL_MINILM_L12_V2")


def _read_lob(value: Any) -> Any:
    if hasattr(value, "read"):
        return value.read()
    return value


def ensure_skillbox(conn: Any) -> None:
    """Create the skillbox table and vector index if they do not already exist."""

    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE harness_skillbox (
                name        VARCHAR2(128) PRIMARY KEY,
                description VARCHAR2(1000),
                body        CLOB NOT NULL,
                metadata    CLOB CHECK (metadata IS JSON),
                embedding   VECTOR(384, FLOAT32),
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    except Exception as exc:
        if "ORA-00955" not in str(exc):
            raise
    try:
        cur.execute(
            """
            CREATE VECTOR INDEX harness_skillbox_emb_v
            ON harness_skillbox(embedding)
            ORGANIZATION INMEMORY NEIGHBOR GRAPH
            DISTANCE COSINE
            """
        )
    except Exception as exc:
        message = str(exc)
        # Oracle AI Database Free containers can have a small VECTOR_MEMORY_SIZE. The lab only
        # stores a few rows, so exact VECTOR_DISTANCE scans are fine if the HNSW
        # index cannot be allocated.
        if "ORA-00955" not in message and "ORA-51962" not in message:
            raise
    conn.commit()


def _description_from_body(body: str, fallback: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:1000]
    return fallback[:1000]


def upsert_skill(
    conn: Any,
    name: str,
    body: str,
    *,
    description: str | None = None,
    metadata: str = "{}",
) -> None:
    """Insert or update a skill and compute its embedding in Oracle."""

    ensure_skillbox(conn)
    desc = description or _description_from_body(body, name)
    embed_text = f"{name}\n{desc}\n{body[:4000]}"
    conn.cursor().execute(
        f"""
        MERGE INTO harness_skillbox t
        USING (SELECT :name AS name FROM dual) s
        ON (t.name = s.name)
        WHEN MATCHED THEN UPDATE SET
            description = :description,
            body = :body,
            metadata = :metadata,
            embedding = VECTOR_EMBEDDING({EMBED_MODEL} USING :embed_text AS DATA),
            updated_at = CURRENT_TIMESTAMP
        WHEN NOT MATCHED THEN INSERT
            (name, description, body, metadata, embedding)
        VALUES
            (:name, :description, :body, :metadata,
             VECTOR_EMBEDDING({EMBED_MODEL} USING :embed_text AS DATA))
        """,
        dict(name=name, description=desc, body=body, metadata=metadata, embed_text=embed_text),
    )
    conn.commit()


def ingest_markdown_file(conn: Any, path: str | Path, *, name: str | None = None) -> dict[str, Any]:
    """Read a Markdown skill file and upsert it into the skillbox."""

    p = Path(path)
    body = p.read_text(encoding="utf-8")
    skill_name = name or p.stem.replace("_", "-")
    upsert_skill(conn, skill_name, body, metadata=f'{{"path": "{p.as_posix()}"}}')
    return {"name": skill_name, "path": p.as_posix()}


def retrieve_skills(conn: Any, query: str, k: int = 3) -> list[dict[str, Any]]:
    """Return top-k skills ordered by cosine distance to the query."""

    ensure_skillbox(conn)
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT name, description,
               VECTOR_DISTANCE(embedding,
                 VECTOR_EMBEDDING({EMBED_MODEL} USING :query AS DATA), COSINE) AS distance
        FROM harness_skillbox
        ORDER BY distance
        FETCH FIRST :k ROWS ONLY
        """,
        dict(query=query, k=k),
    )
    return [
        {"name": name, "description": description, "distance": float(distance)}
        for name, description, distance in cur
    ]


def build_skill_manifest(conn: Any, query: str, k: int = 3) -> str:
    """Return the compact text manifest that goes into the agent prompt."""

    skills = retrieve_skills(conn, query, k=k)
    if not skills:
        return "Available skills: none"
    lines = ["Available skills (call load_skill(name) to read the full guide):"]
    for skill in skills:
        lines.append(f"- {skill['name']}: {skill['description']}")
    return "\n".join(lines)


def get_skill(conn: Any, name: str) -> dict[str, Any] | None:
    ensure_skillbox(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, description, body, metadata FROM harness_skillbox WHERE name = :name",
        dict(name=name),
    )
    row = cur.fetchone()
    if not row:
        return None
    skill_name, description, body, metadata = row
    return {
        "name": skill_name,
        "description": description,
        "body": _read_lob(body),
        "metadata": _read_lob(metadata),
    }


def list_skills(conn: Any, limit: int = 50) -> list[dict[str, Any]]:
    ensure_skillbox(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, description FROM harness_skillbox ORDER BY name FETCH FIRST :n ROWS ONLY",
        dict(n=limit),
    )
    return [{"name": name, "description": description} for name, description in cur]


def count_skills(conn: Any) -> int:
    ensure_skillbox(conn)
    return int(conn.cursor().execute("SELECT COUNT(*) FROM harness_skillbox").fetchone()[0])
