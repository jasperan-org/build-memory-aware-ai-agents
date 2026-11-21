# Before the Session

The complete workshop environment is **set up during the live session**, in the first 15 minutes. Two ways in:

- **GitHub Codespaces** (nothing to install, only a GitHub account): ask the instructor to add you as a collaborator of <https://github.com/jasperan-org/build-memory-aware-ai-agents>, accept the invitation, then open <https://codespaces.new/jasperan-org/build-memory-aware-ai-agents>; the Codespace provisions everything itself, shared LLM keys included. See [`CODESPACES.md`](CODESPACES.md).
- **Your machine**: clone the Packt repository (`git clone https://github.com/PacktPublishing/Build_Memory_Aware_AI_Agents.git`, or download the [ZIP](https://github.com/PacktPublishing/Build_Memory_Aware_AI_Agents/archive/refs/heads/main.zip)), open it in Claude Code or Codex, and the coding agent runs the setup described in [`AGENTS.md`](AGENTS.md).

For the local path the pre-session list is short. Install the first three items, check the fourth, and stop there:

| # | Requirement | Check |
|---|---|---|
| 1 | Docker **or** Podman, with 8 GB of memory for containers | `docker info` or `podman info` |
| 2 | Python 3.11-3.13 (3.12 recommended); `uv` downloads one if none matches | `uv python find --show-version` |
| 3 | A coding agent such as Claude Code or Codex | `claude --version` or `codex --version` |
| 4 | At least 20 GB free disk | `df -h .` (the Oracle image is about a 4 GB download, about 14 GB on disk) |

No LLM API key is needed on the Packt repository path: it ships shared OCI Generative AI keys for the session. (In the Codespaces edition the keys are Codespaces secrets for collaborators.) Jupyter is **not** on that list either: `uv sync --all-extras` installs it with the rest of the notebook dependencies. You do not need Oracle DBA experience, and you do not need to install `oracleagentmemory` or `litellm` by hand.

If any of this fails on your machine, use Codespaces so you can still take part.

---

## 1. Install Docker or Podman

The scripts accept either engine. They use Docker when its daemon is reachable, otherwise Podman; you can force one with `CONTAINER_ENGINE=docker` or `CONTAINER_ENGINE=podman`.

### macOS

Docker Desktop: <https://docs.docker.com/desktop/install/mac-install/> — open it once and wait for the whale icon to show **Running**.

```bash
docker --version
docker compose version
docker info
```

Podman runs in a Linux virtual machine on macOS. Oracle AI Database Free needs RAM, and the image needs disk (about 14 GB extracted), so size the machine accordingly:

```bash
brew install podman
podman machine init --memory 8192 --disk-size 40
podman machine start
podman info
podman compose version    # or: podman-compose --version
```

The default machine disk is usually large enough; 40 GB leaves room for the image, the database files, and the Python environment.

### Windows

Run the workshop scripts from **Git Bash** (installed with Git for Windows); a WSL2 terminal also works.

CPU virtualization must be on: Task Manager > Performance > CPU shows "Virtualization: Enabled". If it says Disabled, enable Intel VT-x / AMD SVM Mode in the BIOS/UEFI. Containers get their memory from WSL2 (half of RAM by default); to give them 8 GB put `memory=8GB` under `[wsl2]` in `%UserProfile%\.wslconfig`, then run `wsl --shutdown`.

Docker Desktop (WSL2 backend): install from <https://docs.docker.com/desktop/install/windows-install/>. Start it before the session; the scripts never launch Docker Desktop.

```bash
docker --version
docker compose version
docker info
```

Podman Desktop or the `podman` CLI with a WSL machine works too. Create the machine once (Podman Desktop's onboarding does this for you); after a reboot the scripts start the machine themselves, but never create one:

```bash
podman machine init --memory 8192 --disk-size 40
podman machine start
podman info
```

Compose provider for Podman: Podman Desktop > Settings > Resources > Compose > Setup, or `uv tool install podman-compose`.

### Ubuntu / Debian — Docker Engine

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in after `usermod`, then verify `docker info` without `sudo`.

### Ubuntu / Debian — Podman

```bash
sudo apt-get install -y podman podman-compose
podman info
podman-compose --version
```

Podman is rootless by default. On an SELinux host (Fedora, RHEL, CentOS), the container also needs to read the bind-mounted `sql/init` directory; if the database cannot see its setup script, run `chcon -Rt container_file_t sql` from the repo root. [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) has the details.

---

## 2. Python 3.11-3.13 and uv

Python 3.11 to 3.13 is required; 3.12 is recommended. You do not have to install it: when no matching Python is found, `uv` downloads one. To see which interpreter `uv` would use:

```bash
uv python find --show-version
```

On Windows, `python3`/`python` on `PATH` are often Microsoft Store aliases that only print "Python was not found"; that does not matter, `uv` does not use them.

`uv` can be installed now or by the coding agent during the session:

```bash
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

The same `curl` installer works in Git Bash. PowerShell alternative: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

`uv` manages the project environment, so you do not need a virtualenv or a system-wide `pip install`.

---

## 3. No LLM key needed

The Lab 1 LLM turns and the OAMP extraction cells use `OAMP_LLM=openai/xai.grok-4.3` on OCI Generative AI. The Packt repository's `.env.example` carries shared keys for the session (three on the Phoenix endpoint, three on Chicago as automatic failover); the setup copies it to `.env`, and the keys are rotated after the workshop. In the Codespaces edition `.env.example` has blank keys and collaborators' Codespaces fill them from Codespaces secrets.

To use your own provider instead, blank both `OCI_GENAI_*ENDPOINT` lines in `.env` and set `OAMP_LLM` plus its key:

| `OAMP_LLM` | Key |
|---|---|
| `gpt-4o-mini` | `OPENAI_API_KEY` |
| `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| `ollama/llama3.1` | none (local Ollama server) |

`uv run workshop-smoke-check` makes one live call, so a wrong pair shows up during setup instead of in the lab.

---

## 4. Have a coding agent ready

Install Claude Code (<https://claude.com/claude-code>) or Codex, and sign in once before the session. In the first minutes of the workshop the agent reads [`AGENTS.md`](AGENTS.md) and runs the whole setup: preflight, `.env`, the Oracle container, `uv sync`, the ONNX load, and the readiness check.

---

## What happens in the first 15 minutes

| Clock | Step |
|---|---|
| 11:00 | Clone this repo and open it in Claude Code or Codex |
| 11:02 | The agent runs `scripts/preflight.sh` and creates `.env` |
| 11:05 | The agent starts `scripts/setup_oracle.sh` in the background; the image pull and first boot continue through Modules 1 and 2 |
| 11:10 | The agent runs `uv sync --all-extras` and `uv run workshop-kernel` while Oracle starts |
| 11:15 | Module 1 starts; the database keeps warming up in the background |
| 12:25 (Break 1) | Setup checkpoint: `uv run python scripts/load_onnx_model.py`, then `uv run workshop-smoke-check --require-onnx` |

Readiness evidence at the checkpoint:

- `✓ LLM call: openai/xai.grok-4.3 answered in ...`
- `✓ release-26 Oracle image digest is pinned`
- `✓ VECTOR user can connect`
- `✓ HNSW vector index allocates (vector memory pool is sized)`
- `✓ ONNX model registered: ALL_MINILM_L12_V2`
- `✓ VECTOR_EMBEDDING sample: ...`
- `All requested checks passed.`

---

## Optional: save time before the session

None of this is required. It only moves the biggest download and the slowest first boot out of the live session.

Pre-pull the pinned image (the digest is in `docker-compose.yml`):

```bash
docker pull container-registry.oracle.com/database/free@sha256:8a8084193724b95bc62247e3af4218b357e4f172c78925551b2181dbe2566232
```

or, with Podman:

```bash
podman pull container-registry.oracle.com/database/free@sha256:8a8084193724b95bc62247e3af4218b357e4f172c78925551b2181dbe2566232
```

Then start the database so the first boot (and the one-time vector memory restart) is already done:

```bash
cp .env.example .env
scripts/setup_oracle.sh
```

You can also run the rest of the runbook ahead of time (`uv sync --all-extras`, `uv run workshop-kernel`, `uv run python scripts/load_onnx_model.py`, `uv run workshop-smoke-check --require-onnx`). The live session re-runs the same steps idempotently, and `setup_oracle.sh` never recreates a running container, so arriving with a warm environment is safe.

---

## Fallback: Codespaces

If local setup fails, use the Codespaces path in [`CODESPACES.md`](CODESPACES.md): it provisions Oracle, the ONNX model, the Python environment, and, for collaborators, the LLM keys automatically.
