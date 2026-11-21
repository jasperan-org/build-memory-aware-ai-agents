"""Oracle AI Database release validation helpers."""

from __future__ import annotations

from typing import Any

EXPECTED_RELEASE_MARKER = "26ai"


def database_banner(conn: Any) -> str:
    """Return the most descriptive Oracle version banner available."""

    cur = conn.cursor()
    try:
        cur.execute("SELECT banner_full FROM v$version WHERE banner_full LIKE 'Oracle%' FETCH FIRST 1 ROW ONLY")
        row = cur.fetchone()
        if row and row[0]:
            return str(row[0])
    except Exception:
        pass
    cur.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%' FETCH FIRST 1 ROW ONLY")
    row = cur.fetchone()
    return str(row[0]) if row else ""


def is_expected_release(conn: Any) -> tuple[bool, str]:
    """Return whether the connected DB banner identifies the release-26 product line."""

    banner = database_banner(conn)
    return EXPECTED_RELEASE_MARKER.lower() in banner.lower(), banner
