"""Generate and optionally load synthetic memory for Lab 2.

The default generator is deterministic and offline so every attendee can produce
exactly the same artifact before connecting to Oracle or an LLM provider.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import use_utf8_output


@dataclass(frozen=True)
class SyntheticMessage:
    role: str
    content: str
    created_at: str


@dataclass(frozen=True)
class SyntheticThread:
    thread_key: str
    topic: str
    messages: list[SyntheticMessage]


@dataclass(frozen=True)
class SyntheticRecord:
    record_type: str
    subject_key: str
    content: str
    tags: list[str]


@dataclass(frozen=True)
class SyntheticSkill:
    name: str
    description: str
    body: str


@dataclass(frozen=True)
class SyntheticTool:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class SyntheticMemoryBundle:
    user_id: str
    agent_id: str
    domain: str
    generated_at: str
    threads: list[SyntheticThread]
    workflows: list[SyntheticRecord]
    entities: list[SyntheticRecord]
    knowledge: list[SyntheticRecord]
    skills: list[SyntheticSkill]
    tools: list[SyntheticTool]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


DOMAINS = {
    "restaurant concierge": {
        "entities": ["Ava", "Niko", "Jun", "Marta", "Leila", "Sam", "Iris", "Noah"],
        "places": ["Harbor Table", "Juniper Room", "Miso Lane", "Casa Brava", "Northstar Grill"],
        "topics": ["anniversary dinner", "vegan options", "quiet table", "late booking", "refund policy"],
    },
    "support agent": {
        "entities": ["Acme Labs", "Bluebird Health", "Northwind", "Contoso", "Globex"],
        "places": ["billing", "identity", "exports", "analytics", "webhooks"],
        "topics": ["urgent escalation", "past ticket lookup", "SLA policy", "API outage", "refund approval"],
    },
}


def _domain_parts(domain: str) -> dict[str, list[str]]:
    return DOMAINS.get(domain, DOMAINS["restaurant concierge"])


def _timestamp(base: datetime, offset: int) -> str:
    return (base + timedelta(minutes=offset)).isoformat()


def generate_bundle(
    *,
    user_id: str,
    agent_id: str,
    domain: str,
    thread_count: int,
    workflow_count: int,
    entity_count: int,
    knowledge_count: int,
    skill_count: int,
    tool_count: int,
    seed: int,
) -> SyntheticMemoryBundle:
    """Create a deterministic synthetic memory bundle."""

    rng = random.Random(seed)
    parts = _domain_parts(domain)
    base = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)

    threads: list[SyntheticThread] = []
    for idx in range(thread_count):
        topic = rng.choice(parts["topics"])
        place = rng.choice(parts["places"])
        person = rng.choice(parts["entities"])
        messages = [
            SyntheticMessage(
                "user",
                f"For {person}, remember that {topic} matters when recommending {place}.",
                _timestamp(base, idx * 10),
            ),
            SyntheticMessage(
                "assistant",
                f"I will keep {topic} attached to {person}'s preferences and use it before suggesting {place}.",
                _timestamp(base, idx * 10 + 1),
            ),
            SyntheticMessage(
                "user",
                f"If the next request mentions {place}, check prior notes before answering.",
                _timestamp(base, idx * 10 + 2),
            ),
        ]
        threads.append(SyntheticThread(f"synthetic-thread-{idx + 1:02d}", topic, messages))

    workflows = [
        SyntheticRecord(
            "workflow",
            f"workflow-{idx + 1:02d}",
            f"When a request involves {rng.choice(parts['topics'])}, first retrieve entity memory, then run policy lookup, then draft a concise response with next action.",
            ["procedural", "workflow", domain],
        )
        for idx in range(workflow_count)
    ]

    entities = [
        SyntheticRecord(
            "entity",
            f"{rng.choice(parts['entities']).lower()}-{idx + 1:02d}",
            f"{rng.choice(parts['entities'])} prefers {rng.choice(parts['places'])} and has a known constraint around {rng.choice(parts['topics'])}.",
            ["entity", "preference", domain],
        )
        for idx in range(entity_count)
    ]

    knowledge = [
        SyntheticRecord(
            "knowledge",
            f"knowledge-{idx + 1:02d}",
            f"Policy note {idx + 1}: for {domain}, {rng.choice(parts['topics'])} should be resolved with transparent reasoning, source citation, and an explicit uncertainty statement.",
            ["semantic", "policy", domain],
        )
        for idx in range(knowledge_count)
    ]

    skills = [
        SyntheticSkill(
            f"{domain.replace(' ', '-')}-skill-{idx + 1:02d}",
            f"Playbook for handling {rng.choice(parts['topics'])} in the {domain} domain.",
            "\n".join(
                [
                    f"# {domain.title()} Skill {idx + 1}",
                    "",
                    f"Use this playbook when the user asks about {rng.choice(parts['topics'])}.",
                    "",
                    "1. Retrieve entity memory for the user or account.",
                    "2. Retrieve the most relevant workflow or policy note.",
                    "3. Ask one clarifying question only if the action would be irreversible.",
                    "4. Respond with the recommendation, cited memory, and next step.",
                ]
            ),
        )
        for idx in range(skill_count)
    ]

    tools = [
        SyntheticTool(
            f"{domain.replace(' ', '_')}_tool_{idx + 1:02d}",
            f"Retrieve or act on {rng.choice(parts['topics'])} for {domain} scenarios.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language request."},
                    "subject_key": {"type": "string", "description": "User, entity, or account key."},
                },
                "required": ["query"],
            },
        )
        for idx in range(tool_count)
    ]

    return SyntheticMemoryBundle(
        user_id=user_id,
        agent_id=agent_id,
        domain=domain,
        generated_at=datetime.now(timezone.utc).isoformat(),
        threads=threads,
        workflows=workflows,
        entities=entities,
        knowledge=knowledge,
        skills=skills,
        tools=tools,
    )


def write_bundle(bundle: SyntheticMemoryBundle, out_path: Path, *, write_skill_files: bool = False) -> None:
    """Write the JSON bundle and optionally each synthetic skill as Markdown."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle.to_json_dict(), indent=2), encoding="utf-8")
    if write_skill_files:
        skills_dir = out_path.parent / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        for skill in bundle.skills:
            (skills_dir / f"{skill.name}.md").write_text(skill.body + "\n", encoding="utf-8")


def load_into_oamp(bundle: SyntheticMemoryBundle) -> dict[str, int]:
    """Best-effort load into OAMP using the public developer-guide API surface."""

    from oracleagentmemory.apis.thread import Message
    from oracleagentmemory.core import OracleAgentMemory

    from .connection import connect
    from .onnx import oamp_embedder

    conn = connect()
    client = OracleAgentMemory(
        connection=conn,
        embedder=oamp_embedder(conn),
        extract_memories=False,
        schema_policy="create_if_necessary",
    )

    for fn, entity_id, information in [
        (client.add_user, bundle.user_id, f"Synthetic workshop user for {bundle.domain}."),
        (client.add_agent, bundle.agent_id, f"Synthetic workshop agent for {bundle.domain}."),
    ]:
        try:
            fn(entity_id, information)
        except ValueError as exc:
            if "already exists" not in str(exc):
                raise

    loaded = {"threads": 0, "memories": 0}
    for synthetic_thread in bundle.threads:
        thread = client.create_thread(user_id=bundle.user_id, agent_id=bundle.agent_id)
        thread.add_messages(
            [Message(role=m.role, content=m.content) for m in synthetic_thread.messages]
        )
        loaded["threads"] += 1

    for record in [*bundle.workflows, *bundle.entities, *bundle.knowledge]:
        client.add_memory(
            f"[{record.record_type}] {record.subject_key}: {record.content}",
            user_id=bundle.user_id,
            agent_id=bundle.agent_id,
        )
        loaded["memories"] += 1
    return loaded


def load_toolbox_skillbox(bundle: SyntheticMemoryBundle) -> dict[str, int]:
    """Best-effort load of synthetic tools and skills into the workshop registries."""

    from .connection import connect
    from .skillbox import upsert_skill
    from .toolbox import upsert_tool

    with connect() as conn:
        for tool in bundle.tools:
            upsert_tool(conn, tool.name, tool.description, tool.parameters, source="synthetic")
        for skill in bundle.skills:
            upsert_skill(conn, skill.name, skill.body, description=skill.description, metadata='{"source":"synthetic"}')
    return {"tools": len(bundle.tools), "skills": len(bundle.skills)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="restaurant concierge", choices=sorted(DOMAINS))
    parser.add_argument("--user-id", default="workshop_user")
    parser.add_argument("--agent-id", default="memory_agent")
    parser.add_argument("--threads", type=int, default=20)
    parser.add_argument("--workflows", type=int, default=15)
    parser.add_argument("--entities", type=int, default=30)
    parser.add_argument("--knowledge", type=int, default=50)
    parser.add_argument("--skills", type=int, default=5)
    parser.add_argument("--tools", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path("generated/synthetic_memory.json"))
    parser.add_argument("--write-skill-files", action="store_true")
    parser.add_argument("--load-oamp", action="store_true", help="Load threads and records into OAMP.")
    parser.add_argument("--load-toolbox", action="store_true", help="Load tools and skills into Oracle registries.")
    return parser


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    from .connection import load_env

    load_env(Path.cwd() / ".env")
    bundle = generate_bundle(
        user_id=args.user_id,
        agent_id=args.agent_id,
        domain=args.domain,
        thread_count=args.threads,
        workflow_count=args.workflows,
        entity_count=args.entities,
        knowledge_count=args.knowledge,
        skill_count=args.skills,
        tool_count=args.tools,
        seed=args.seed,
    )
    write_bundle(bundle, args.out, write_skill_files=args.write_skill_files)
    print(f"wrote {args.out}")
    print(
        json.dumps(
            {
                "threads": len(bundle.threads),
                "workflows": len(bundle.workflows),
                "entities": len(bundle.entities),
                "knowledge": len(bundle.knowledge),
                "skills": len(bundle.skills),
                "tools": len(bundle.tools),
            },
            indent=2,
        )
    )
    if args.load_oamp:
        print("OAMP load:", json.dumps(load_into_oamp(bundle), indent=2))
    if args.load_toolbox:
        print("toolbox/skillbox load:", json.dumps(load_toolbox_skillbox(bundle), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
