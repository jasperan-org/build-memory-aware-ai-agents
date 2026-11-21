"""ONNX model checks for the workshop setup path."""

from __future__ import annotations

import os
import re
from typing import Any

import numpy as np
import oracledb

MODEL_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")

# ALL_MINILM_L12_V2 takes at most 512 tokens (510 plus CLS/SEP); a longer input fails
# with ORA-54401 instead of being truncated. English runs about four characters per
# token, so most text under this cap fits; denser text is halved until it does.
MAX_EMBED_CHARS = 2000


def oracle_model_name_from_preset(preset: str) -> str:
    """Return the Oracle model name used by onnx2oracle for common presets."""

    explicit = os.environ.get("WORKSHOP_EMBED_MODEL")
    if explicit:
        return explicit.upper()
    return preset.replace("-", "_").replace(".", "_").upper()


def configured_model_name() -> str:
    preset = os.environ.get("ORACLE_EMBED_PRESET", "all-MiniLM-L12-v2")
    return oracle_model_name_from_preset(preset)


def validate_model_name(name: str) -> str:
    model_name = name.upper()
    if not MODEL_NAME_RE.fullmatch(model_name):
        raise ValueError(f"Unsafe Oracle model name: {name!r}")
    return model_name


def model_registered(conn: Any, model_name: str | None = None) -> bool:
    """Return True when the configured ONNX model exists in USER_MINING_MODELS."""

    model = validate_model_name(model_name or configured_model_name())
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_mining_models WHERE model_name = :name", {"name": model})
    return int(cur.fetchone()[0]) > 0


def embedding_sample(conn: Any, model_name: str | None = None) -> str:
    """Run a tiny VECTOR_EMBEDDING query and return a printable sample."""

    model = validate_model_name(model_name or configured_model_name())
    cur = conn.cursor()
    cur.execute(f"SELECT VECTOR_EMBEDDING({model} USING 'hello world' AS DATA) FROM dual")
    value = cur.fetchone()[0]
    return str(value)[:120]


class OracleVectorEmbedder:
    """OAMP-compatible embedder backed by Oracle VECTOR_EMBEDDING.

    OAMP accepts an object with `embed` / `embed_async`. Returning a 2D numpy
    array lets Lab 1 run without an external embedding API key once the ONNX
    model is loaded into Oracle.
    """

    def __init__(self, conn: Any, model_name: str | None = None) -> None:
        self.conn = conn
        self.model_name = validate_model_name(model_name or configured_model_name())

    def _embed_one(self, text: str) -> np.ndarray:
        # OAMP embeds long inputs too: get_context_card() searches with the recent
        # messages, which include whole LLM replies. Keep the leading part, as
        # sentence-transformers does when it truncates.
        text = str(text)[:MAX_EMBED_CHARS]
        cur = self.conn.cursor()
        while True:
            try:
                cur.execute(
                    f"SELECT VECTOR_EMBEDDING({self.model_name} USING :text AS DATA) FROM dual",
                    {"text": text},
                )
                break
            except oracledb.DatabaseError as exc:
                if "ORA-54401" not in str(exc) or len(text) < 64:
                    raise
                text = text[: len(text) // 2]
        value = cur.fetchone()[0]
        return np.asarray(list(value), dtype=np.float32)

    def embed(self, texts: str | list[str] | tuple[str, ...]) -> np.ndarray:
        if isinstance(texts, (list, tuple)):
            return np.vstack([self._embed_one(text) for text in texts])
        return np.vstack([self._embed_one(texts)])

    async def embed_async(self, texts: str | list[str] | tuple[str, ...]) -> np.ndarray:
        return self.embed(texts)


def oamp_embedder(conn: Any) -> Any:
    """Return the configured OAMP embedder.

    `OAMP_EMBEDDER=oracle-db` means use the in-database ONNX model. Any other
    value is passed through to OAMP/LiteLLM as a model string.
    """

    configured = os.environ.get("OAMP_EMBEDDER", "oracle-db")
    if configured.lower() in {"oracle", "oracle-db", "oracle_vector", "in-database"}:
        return OracleVectorEmbedder(conn)
    return configured
