"""Minimal toolbox registry used in the workshop mini-lab.

This mirrors the reference pattern from agent-harness: tools are rows in Oracle,
embeddings are produced inside the database with VECTOR_EMBEDDING, and each turn
retrieves only the top-k relevant tool schemas instead of pasting every schema
into the prompt.
"""

from __future__ import annotations

import json
import os
from typing import Any

EMBED_MODEL = os.environ.get("WORKSHOP_EMBED_MODEL", "ALL_MINILM_L12_V2")


def _read_lob(value: Any) -> Any:
    if hasattr(value, "read"):
        return value.read()
    return value


def ensure_toolbox(conn: Any) -> None:
    """Create the toolbox table and vector index if they do not already exist."""

    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE harness_toolbox (
                name        VARCHAR2(128) PRIMARY KEY,
                description CLOB NOT NULL,
                parameters  CLOB CHECK (parameters IS JSON),
                embedding   VECTOR(384, FLOAT32),
                source      VARCHAR2(512),
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
            CREATE VECTOR INDEX harness_toolbox_emb_v
            ON harness_toolbox(embedding)
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


def upsert_tool(
    conn: Any,
    name: str,
    description: str,
    parameters: dict[str, Any] | list[Any] | str | None = None,
    *,
    source: str = "workshop",
) -> None:
    """Insert or update a tool row and compute its embedding in Oracle."""

    ensure_toolbox(conn)
    params_json = parameters if isinstance(parameters, str) else json.dumps(parameters or {})
    embed_text = f"{name}\n{description}\n{params_json}"
    conn.cursor().execute(
        f"""
        MERGE INTO harness_toolbox t
        USING (SELECT :name AS name FROM dual) s
        ON (t.name = s.name)
        WHEN MATCHED THEN UPDATE SET
            description = :description,
            parameters = :parameters,
            embedding = VECTOR_EMBEDDING({EMBED_MODEL} USING :embed_text AS DATA),
            source = :source,
            updated_at = CURRENT_TIMESTAMP
        WHEN NOT MATCHED THEN INSERT
            (name, description, parameters, embedding, source)
        VALUES
            (:name, :description, :parameters,
             VECTOR_EMBEDDING({EMBED_MODEL} USING :embed_text AS DATA), :source)
        """,
        dict(
            name=name,
            description=description,
            parameters=params_json,
            embed_text=embed_text,
            source=source,
        ),
    )
    conn.commit()


def retrieve_tools(conn: Any, query: str, k: int = 6) -> list[dict[str, Any]]:
    """Return top-k tool records ordered by cosine distance to the query."""

    ensure_toolbox(conn)
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT name, description, parameters,
               VECTOR_DISTANCE(embedding,
                 VECTOR_EMBEDDING({EMBED_MODEL} USING :query AS DATA), COSINE) AS distance
        FROM harness_toolbox
        ORDER BY distance
        FETCH FIRST :k ROWS ONLY
        """,
        dict(query=query, k=k),
    )
    rows = []
    for name, description, parameters, distance in cur:
        raw_params = _read_lob(parameters)
        rows.append(
            {
                "name": name,
                "description": _read_lob(description),
                "parameters": json.loads(raw_params) if raw_params else {},
                "distance": float(distance),
            }
        )
    return rows


def get_tool(conn: Any, name: str) -> dict[str, Any] | None:
    ensure_toolbox(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, description, parameters, source FROM harness_toolbox WHERE name = :name",
        dict(name=name),
    )
    row = cur.fetchone()
    if not row:
        return None
    tool_name, description, parameters, source = row
    raw_params = _read_lob(parameters)
    return {
        "name": tool_name,
        "description": _read_lob(description),
        "parameters": json.loads(raw_params) if raw_params else {},
        "source": source,
    }


def list_tools(conn: Any, limit: int = 200) -> list[dict[str, Any]]:
    ensure_toolbox(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, description, source FROM harness_toolbox ORDER BY name FETCH FIRST :n ROWS ONLY",
        dict(n=limit),
    )
    return [
        {"name": name, "description": _read_lob(description), "source": source}
        for name, description, source in cur
    ]


def count_tools(conn: Any) -> int:
    ensure_toolbox(conn)
    return int(conn.cursor().execute("SELECT COUNT(*) FROM harness_toolbox").fetchone()[0])
