# AGENTS.md — live setup runbook for coding agents

This repository is the attendee package for the Packt live workshop
**Designing and Building Memory for AI Agents** (Saturday November 21, 2026, 4 hours).
It runs Oracle AI Database Free in a container, loads an in-database ONNX embedding
model, and ships three Jupyter labs.

You are working next to a human in a live session. Run the steps in order, show what
each one printed, keep every step idempotent (safe to re-run), and ask before anything
that deletes data. Inside a GitHub Codespace, steps 2-7 already ran during creation
(`.devcontainer/post-create.sh`); run step 7 to confirm, then go to step 8.

## 1. Preflight

```bash
scripts/preflight.sh
```

Checks `uv` (and prints the Python it will use: 3.11-3.13, downloaded by `uv` when none is installed), Docker or Podman (daemon plus compose), disk (warns below
20 GB free), the memory the container engine has (warns below 6 GB), the LLM settings in
`.env`, and whether the pinned Oracle image is already pulled. It exits non-zero only on
hard failures; warnings can wait.

## 2. Environment file

```bash
test -f .env || cp .env.example .env
```

Never overwrite an existing `.env`. In this repository the six `OCI_GENAI_*API_KEY*`
values in `.env.example` are blank: collaborators' Codespaces get the shared keys as
Codespaces secrets, copied into `.env` by `.devcontainer/env-from-secrets.sh` on create
and on start. Outside such a Codespace the human must supply a key. The default is
`OAMP_LLM=openai/xai.grok-4.3`, three keys on the Phoenix endpoint, three on Chicago as
failover. If the human wants their own provider instead, they blank both
`OCI_GENAI_*ENDPOINT` lines and set `OAMP_LLM` plus the matching key (`gpt-4o-mini` with
`OPENAI_API_KEY`, `anthropic/claude-...` with `ANTHROPIC_API_KEY`, `ollama/llama3.1`
with a local Ollama server). Step 7 proves the pair with a live call.

## 3. Detect the container engine

The scripts prefer Docker and fall back to Podman; pin one explicitly when both exist:

```bash
CONTAINER_ENGINE=podman scripts/preflight.sh
```

Compose resolution order is `docker compose`, then `podman compose`, then
`podman-compose`. On macOS and Windows, Podman needs a VM: one time
`podman machine init --memory 8192` (a manual step; the scripts never create a
machine). If the machine exists but is stopped, the scripts start it. They never
launch Docker Desktop. On Windows run everything from Git Bash (or WSL2); CPU
virtualization must be enabled in the BIOS/UEFI (Intel VT-x / AMD SVM Mode), and the
engine's memory comes from WSL2 (`memory=8GB` under `[wsl2]` in
`%UserProfile%\.wslconfig`, then `wsl --shutdown`). For Podman, the compose provider is
Podman Desktop > Settings > Resources > Compose > Setup, or `uv tool install podman-compose`.

## 4. Start Oracle AI Database

```bash
scripts/setup_oracle.sh
```

Starts the `agentic-memory-oracle` container from `docker-compose.yml`, verifies it runs
the pinned release-26 digest, waits for SQL readiness, sizes Oracle's vector memory pool
to 512 MB (one automatic restart on first setup; HNSW indexes need it), then applies
`sql/init/01-create-vector-user.sql`. First boot takes 3-5 minutes after the image pull
(about 4 GB download, about 14 GB on disk). Codespaces set `ORACLE_IMAGE` to the pinned
`gvenzl/oracle-free` faststart image instead (1.7 GB download, database pre-built), so it
fits their 32 GB disk. During the live session run it in the
background and let it finish while the session continues:

```bash
scripts/setup_oracle.sh > /tmp/oracle-setup.log 2>&1 &
tail -f /tmp/oracle-setup.log
```

Re-running the script is safe at any time: it never recreates a running container (open
notebook connections survive), starts a stopped one, and only waits for readiness.

## 5. Python dependencies

```bash
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv sync --all-extras
uv run workshop-kernel
```

`--all-extras` installs the `notebooks` and `dev` extras (Jupyter Lab, ipykernel, pandas,
matplotlib, pytest, ruff). Plain `uv sync` does **not** install Jupyter.
`uv run workshop-kernel` registers the `agentic-memory` Jupyter kernel inside `.venv`
("Python (agentic-memory workshop)"); the notebooks ask for it by name, so a `python3`
kernel left in the user's Jupyter directory by another project cannot take over.

## 6. Load the in-database ONNX model

```bash
uv run python scripts/load_onnx_model.py
```

Registers `ALL_MINILM_L12_V2` through `DBMS_VECTOR.LOAD_ONNX_MODEL`. The first run
downloads and augments the ONNX graph, so it takes several minutes. Re-run with
`--force` if the model is registered but broken.

## 7. Verify readiness

```bash
uv run workshop-smoke-check --offline       # files only, no services
uv run workshop-smoke-check --require-onnx  # full workshop readiness
```

`--require-onnx` is the gate: required files, imports, DB env vars, one live LLM call
through `OAMP_LLM`, a live Oracle connection with the release-26 marker, a throwaway HNSW
index (vector memory pool), `ALL_MINILM_L12_V2` in `USER_MINING_MODELS`, and a working
`VECTOR_EMBEDDING` call. Success prints `All requested checks passed.` Add `--skip-llm`
only when the human deliberately runs without an LLM.

## 8. Launch the labs

```bash
uv run jupyter lab
```

Notebooks run in order: `01_oamp_memory_agent.ipynb`, `02_skillbox_toolbox.ipynb`,
`03_synthetic_memory_bootstrap.ipynb`. In a browserless environment add
`--no-browser --ip 0.0.0.0`.

## Known failure modes

| Symptom | Action |
|---|---|
| Windows: "CPU virtualization is off" or Podman machine start fails | Tell the human to enable Intel VT-x / AMD SVM Mode in the BIOS/UEFI, or to use Codespaces (`CODESPACES.md`). |
| Windows: `uv sync` fails with "Access is denied" | A Jupyter kernel from `.venv` (for example a notebook open in VS Code) locks its files. Stop it, rerun `uv sync --all-extras`. |
| Windows: `python3` says "Python was not found" | Microsoft Store alias; ignore, `uv` provisions Python 3.11-3.13. |
| Host port 1526 already taken | Set `ORACLE_HOST_PORT=1527` and `DB_CONNECT_STRING=localhost:1527/FREEPDB1` in `.env`, then re-run step 4. Change it in `.env`: `podman-compose` substitutes from that file even when the shell exports a different value. |
| `Wrong Oracle container image` | The container was created from a different image. Recreate it (see the guardrail on `down -v`). |
| `podman compose` fails with `dial unix /run/user/.../podman.sock` | The docker-compose provider needs the Podman API socket: `systemctl --user start podman.socket` (Linux), or install `podman-compose`; the scripts prefer it when the socket is down. |
| `ORA-01017` invalid username/password | Stale volume from an earlier image. Recreate it (see the guardrail on `down -v`). |
| Container never becomes healthy | `docker logs agentic-memory-oracle --tail 100` or `podman logs agentic-memory-oracle --tail 100`; first boot is slow on cold disks. |
| `ORA-51962` vector-memory error on index creation | The vector memory pool is unsized. Re-run `scripts/setup_oracle.sh`: it sets `vector_memory_size=512M` and restarts Oracle once. |
| `✗ LLM call` with a missing key in a Codespace | The user is not a collaborator yet, or the Codespace started before the invitation was accepted: accept the invitation, then stop and restart the Codespace (secrets are injected at start). Non-collaborators can add a personal Codespaces secret `OCI_GENAI_API_KEY` and restart, or set their own provider in `.env`. |
| `✗ LLM call` in the smoke check | The message names the cause (missing key for `OAMP_LLM`, or every key route failed). Check `.env` against `.env.example`; never print the keys. |
| `externally-managed-environment` / PEP 668 on `pip install` | Install `uv` with the official installer (step 5) instead of `pip`. |
| `jupyter: command not found` | Dependencies came from plain `uv sync`. Run `uv sync --all-extras`. |
| `No such file or directory: .../bin/python` or `No such kernel named agentic-memory` when a notebook starts | The notebook kernel is not registered for this `.venv`. Run `uv run workshop-kernel`, then restart Jupyter. |

Exact fixes and live-tested notes: `TROUBLESHOOTING.md`. Install links per OS:
`SETUP.md`. Container-free path: `CODESPACES.md`.

## Guardrails

- Never change or retag the pinned image digests: the official image in `docker-compose.yml`
  (local installs) and `ORACLE_IMAGE` in `.devcontainer/devcontainer.json` (Codespaces).
- Never commit `.env`, and never echo a key into the terminal or a notebook.
- Ask the human before `docker compose down -v` or `podman compose down -v`: it deletes
  the Oracle data volume and any memories written during the session.
- Keep `OAMP_LLM` and its credentials consistent (see step 2), and keep
  `OAMP_EMBEDDER=oracle-db` so the labs embed inside Oracle.
- Do not rename files, the `agentic-memory-oracle` container, or the
  `agentic_memory_workshop` package: `workshop-smoke-check` asserts those paths.
