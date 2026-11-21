"""Utilities for the Agentic Memory Management workshop attendee package."""

import sys

__all__ = ["__version__"]
__version__ = "0.1.0"


def use_utf8_output() -> None:
    """On Windows, redirected output defaults to the ANSI code page, where ✓ raises UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
