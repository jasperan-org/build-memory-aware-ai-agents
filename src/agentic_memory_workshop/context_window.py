"""Helpers that measure and render an agent's context window for the scale-up demo.

Token counts come from `litellm.token_counter` for the configured model. They are
estimates: the provider's own tokenizer and chat template can differ by a few percent.
"""

from __future__ import annotations

import json
from typing import Any

from .llm import llm_model
from .skillbox import get_skill, list_skills
from .toolbox import ensure_toolbox

SECTIONS = ("system", "tools", "skills", "history", "message")


def count_tokens(text: str) -> int:
    """Estimate the tokens `text` takes for the configured model."""

    import litellm

    return int(litellm.token_counter(model=llm_model(), text=text)) if text else 0


def render_tools(tools: list[dict[str, Any]]) -> str:
    """Render tool schemas the way they are pasted into a prompt: one JSON object per tool."""

    lines = [
        json.dumps(
            {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        )
        for t in tools
    ]
    return "Tools you may use:\n" + "\n".join(lines) if lines else ""


def render_skills(manifest: str, skill: dict[str, Any] | None) -> str:
    """Render the skill manifest plus the full body of the one loaded skill."""

    if skill is None:
        return manifest
    return f"{manifest}\n\nLoaded skill '{skill['name']}':\n{skill['body']}"


def render_history(history: list[dict[str, str]]) -> str:
    """Render earlier turns as plain text."""

    return "\n".join(f"{m['role']}: {m['content']}" for m in history)


def assemble_messages(
    system: str, tools_text: str, skills_text: str, history: list[dict[str, str]], message: str
) -> list[dict[str, str]]:
    """Build the chat messages: one system block (rules, tools, skills), the history, the new user message."""

    system_block = "\n\n".join(part for part in (system, tools_text, skills_text) if part)
    return [
        {"role": "system", "content": system_block},
        *history,
        {"role": "user", "content": message},
    ]


def breakdown(
    system: str, tools_text: str, skills_text: str, history: list[dict[str, str]], message: str
) -> dict[str, int]:
    """Estimated tokens per prompt section, plus the total."""

    parts = dict(
        zip(
            SECTIONS,
            (
                count_tokens(system),
                count_tokens(tools_text),
                count_tokens(skills_text),
                count_tokens(render_history(history)),
                count_tokens(message),
            ),
            strict=True,
        )
    )
    parts["total"] = sum(parts.values())
    return parts


def format_breakdown(parts: dict[str, int]) -> str:
    """One line: system / tools / skills / history / message = total."""

    body = " + ".join(f"{name} {parts[name]:,}" for name in SECTIONS)
    return f"{body} = {parts['total']:,} tokens (estimated)"


def _all_tools(connection: Any) -> list[dict[str, Any]]:
    ensure_toolbox(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT name, description, parameters FROM harness_toolbox ORDER BY name")
    tools = []
    for name, description, parameters in cursor.fetchall():
        description = description.read() if hasattr(description, "read") else description
        parameters = parameters.read() if hasattr(parameters, "read") else parameters
        if isinstance(parameters, str | bytes):
            parameters = json.loads(parameters)
        tools.append({"name": name, "description": description, "parameters": parameters or {}})
    return tools


def registry_snapshot(connection: Any) -> dict[str, Any]:
    """Everything a naive agent would paste: every tool schema and every skill body."""

    tools = _all_tools(connection)
    skills = [get_skill(connection, row["name"]) for row in list_skills(connection, limit=500)]
    tools_text = render_tools(tools)
    skills_text = "\n\n".join(f"Skill '{s['name']}':\n{s['body']}" for s in skills)
    return {
        "tools": tools,
        "skills": skills,
        "tools_text": tools_text,
        "skills_text": skills_text,
        "tools_tokens": count_tokens(tools_text),
        "skills_tokens": count_tokens(skills_text),
    }


def naive_total(
    snapshot: dict[str, Any], system: str, history: list[dict[str, str]], message: str
) -> int:
    """Estimated size of the prompt that pastes the whole registry instead of retrieving."""

    return (
        count_tokens(system)
        + snapshot["tools_tokens"]
        + snapshot["skills_tokens"]
        + count_tokens(render_history(history))
        + count_tokens(message)
    )


def prompt_tokens_reported(response: Any) -> int | None:
    """The provider's own prompt-token count, when the response carries usage."""

    usage = getattr(response, "usage", None)
    value = getattr(usage, "prompt_tokens", None)
    return int(value) if value is not None else None


def changes(previous: list[str], current: list[str]) -> str:
    """Describe what a turn added and dropped compared with the previous turn."""

    added = [n for n in current if n not in previous]
    dropped = [n for n in previous if n not in current]
    if not previous:
        return "first turn: everything is new"
    return f"added: {', '.join(added) or 'none'} | dropped: {', '.join(dropped) or 'none'}"


def offload_pct(focused: int, naive: int) -> float:
    """Share of the naive prompt that retrieval keeps out of the context window."""

    return 100 * (naive - focused) / naive if naive else 0.0


def print_summary(rows: list[dict[str, Any]]) -> None:
    """Per-turn table of focused vs naive prompt size, then conversation totals."""

    print(f"{'turn':>4}  {'focused':>8}  {'naive':>8}  {'offloaded':>10}  {'% offloaded':>11}")
    for row in rows:
        saved = row["naive"] - row["focused"]
        print(
            f"{row['turn']:>4}  {row['focused']:>8,}  {row['naive']:>8,}  {saved:>10,}  {offload_pct(row['focused'], row['naive']):>10.1f}%"
        )
    focused = sum(r["focused"] for r in rows)
    naive = sum(r["naive"] for r in rows)
    print(
        f"{'all':>4}  {focused:>8,}  {naive:>8,}  {naive - focused:>10,}  {offload_pct(focused, naive):>10.1f}%"
    )
    print("Token counts are estimates from litellm.token_counter.")
