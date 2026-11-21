# Setup Guide

This is the full runbook for the **Designing and Building Memory for AI Agents** workshop (Saturday November 21, 2026, 4 hours).

The environment is set up **during the live session**, in the first 15 minutes, with a coding agent driving this repo's [`AGENTS.md`](AGENTS.md). Read this file when you want to run the steps by hand, when a step fails, or when you want the optional head start described in [`PREWORK.md`](PREWORK.md). The live-tested failure modes are captured in [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

---

## Success state

You are ready when this command passes:

```bash
uv run workshop-smoke-check --require-onnx
```

That proves:

- Docker **or** Podman is working, with a compose command.
- Oracle AI Database Free is running and reachable.
- Python dependencies are installed (Python 3.11-3.13).
- OAMP imports correctly.
- `onnx2oracle` is installed.
- `OAMP_LLM` answers a live call with the configured keys.
- The vector memory pool can hold an HNSW index (no `ORA-51962`).
- The in-database ONNX model `ALL_MINILM_L12_V2` is registered and callable through `VECTOR_EMBEDDING`.

---

## 1. Install a container engine

Either engine works. The scripts use Docker when its daemon is reachable, otherwise Podman, and you can force one with `CONTAINER_ENGINE=docker` or `CONTAINER_ENGINE=podman`.

### macOS — Docker

Install Docker Desktop: <https://docs.docker.com/desktop/install/mac-install/>

```bash
docker --version
docker compose version
docker info
```

### macOS — Podman

Podman runs inside a Linux virtual machine on macOS. Oracle AI Database Free needs RAM, and the image needs disk (about 14 GB extracted), so size the machine for both:

```bash
brew install podman
podman machine init --memory 8192 --disk-size 40
podman machine start
podman info
podman compose version    # falls back to podman-compose if installed
```

`podman machine init` is a one-time step; after a reboot run `podman machine start` before the workshop scripts.

### Windows — prerequisites

Run the workshop scripts from **Git Bash** (installed with Git for Windows); a WSL2 terminal also works.

- CPU virtualization must be on. Task Manager > Performance > CPU shows "Virtualization: Enabled"; if not, enable Intel VT-x / AMD SVM Mode in the BIOS/UEFI.
- Both engines get their memory from WSL2 (half of RAM by default). To give containers 8 GB, put `memory=8GB` under `[wsl2]` in `%UserProfile%\.wslconfig`, then run `wsl --shutdown`.
- `uv`: in Git Bash `curl -LsSf https://astral.sh/uv/install.sh | sh`; in PowerShell `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### Windows — Docker

Use Docker Desktop with the WSL2 backend: <https://docs.docker.com/desktop/install/windows-install/>. Start Docker Desktop before the session (the scripts never launch it). Verify with `docker --version`, `docker compose version`, `docker info`.

### Windows — Podman

Install Podman Desktop or the `podman` CLI with a WSL machine. Create the machine once (Podman Desktop's onboarding does it, or run this) and start it:

```bash
podman machine init --memory 8192 --disk-size 40
podman machine start
podman info
```

After a reboot the scripts start the existing machine themselves; they never run `podman machine init`. Compose provider: Podman Desktop > Settings > Resources > Compose > Setup, or `uv tool install podman-compose`.

### Ubuntu / Debian — Docker Engine

Docker Desktop is acceptable; Docker Engine also works:

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

Log out and back in after the `usermod`, then verify `docker info` without `sudo`.

### Ubuntu / Debian — Podman

```bash
sudo apt-get install -y podman podman-compose
podman info
podman-compose --version
```

Podman is rootless by default, which is fine for this workshop: the container publishes `127.0.0.1:1526`.

On an SELinux host (Fedora, RHEL, CentOS), a rootless container cannot read the bind-mounted init scripts until the host labels them for container use. If Oracle starts but `VECTOR` never appears, run this from the repo root and restart:

```bash
chcon -Rt container_file_t sql
```

---

## 2. Configure environment variables

```bash
cp .env.example .env
```

`scripts/setup_oracle.sh` also creates `.env` from the example when it is missing, and never overwrites an existing one.

The database defaults are workshop-only local credentials:

```text
DB_USER=VECTOR
DB_PASSWORD=VectorPwd_2025
ORACLE_HOST_PORT=1526
DB_CONNECT_STRING=localhost:1526/FREEPDB1
```

The LLM settings ship ready to use. `.env.example` carries shared OCI Generative AI keys for the session (rotated afterwards), served through OCI's OpenAI-compatible API:

```text
OAMP_LLM=openai/xai.grok-4.3
OCI_GENAI_ENDPOINT=https://inference.generativeai.us-phoenix-1.oci.oraclecloud.com/openai/v1
OCI_GENAI_API_KEY=...            # plus OCI_GENAI_API_KEY_2, _3
OCI_GENAI_FALLBACK_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
OCI_GENAI_FALLBACK_API_KEY=...   # plus OCI_GENAI_FALLBACK_API_KEY_2, _3
```

`src/agentic_memory_workshop/llm.py` shuffles the keys per process so a full room spreads its load, and fails over to the next key (Phoenix first, then Chicago) when one is rate limited, rejected, or unreachable. The notebooks use it for the Lab 1 turns (`chat`) and for OAMP extraction and summaries (`oamp_llm()`).

The notebooks also read:

```text
OAMP_EMBEDDER=oracle-db
ORACLE_EMBED_PRESET=all-MiniLM-L12-v2
WORKSHOP_EMBED_MODEL=ALL_MINILM_L12_V2
```

`OAMP_EMBEDDER=oracle-db` makes the base labs use the in-database ONNX model instead of an external embedding API. You can switch it to a LiteLLM model string if your provider is configured, but keep `WORKSHOP_EMBED_MODEL` aligned with the ONNX model loaded into Oracle for the skillbox/toolbox SQL.

To use your own provider instead of the shared keys, blank both `OCI_GENAI_*ENDPOINT` lines in `.env` and set `OAMP_LLM` to a LiteLLM model string plus the key it needs:

| `OAMP_LLM` | Key |
|---|---|
| `gpt-4o-mini` | `OPENAI_API_KEY` |
| `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| `ollama/llama3.1` | none, but a local Ollama server must be running |

`uv run workshop-smoke-check` makes one live call with that pair, so a mismatch fails during setup, not in the middle of Lab 1.

---

## 3. How the scripts pick an engine

`scripts/container_engine.sh` is sourced by `scripts/preflight.sh` and `scripts/setup_oracle.sh`. It:

1. Honors `CONTAINER_ENGINE=docker|podman` when set.
2. Otherwise prefers Docker if `docker info` succeeds, then Podman if `podman info` succeeds.
   If Podman is installed but `podman info` fails, it starts an existing stopped Podman machine
   (the one marked default, else the first listed) and shows the start error if that fails. It
   never creates a machine (`podman machine init` stays a one-time manual step), never launches
   Docker Desktop, and never changes Windows features.
3. Resolves compose as `docker compose`, then `podman compose`, then `podman-compose`.
   `podman compose` normally delegates to docker-compose, which talks to the Podman API
   socket, so the scripts only prefer it when that socket is up; otherwise they fall back
   to `podman-compose`. On Linux, start the socket with
   `systemctl --user start podman.socket`, or install `podman-compose`.
4. Routes every container call (compose up/ps, `inspect`, `exec`, `logs`, `image inspect`) through the selected engine.

Force a choice when both engines are installed:

```bash
CONTAINER_ENGINE=podman scripts/setup_oracle.sh
```

Server port substitution is engine-specific: `docker compose` prefers an exported `ORACLE_HOST_PORT`, while `podman-compose` resolves it from `.env`. To move the host port, change it in `.env`; that works on both.

The pinned-image guard reads `.Config.Image` on Docker and `.ImageName` on Podman, and falls back to comparing image IDs, so the digest check works on both engines.

---

## 4. Run preflight

```bash
scripts/preflight.sh
```

The preflight checks:

| Check | Why it matters |
|---|---|
| Docker and Podman availability, daemon, compose | Required for the local Oracle AI Database |
| Selected engine | Shows which engine and compose command the other scripts will use |
| Python 3.11-3.13 via uv | Prints the interpreter `uv python find` picks, or warns that `uv sync` will download one. No `python3` check: uv provisions the project Python |
| Windows (Git Bash) | Reported as an ok line, not a warning |
| Virtualization (Windows) | When no engine works and Windows reports no hypervisor with virtualization disabled in firmware, says to enable Intel VT-x / AMD SVM Mode in the BIOS/UEFI and points to Codespaces |
| Disk | At least 20 GB free: the 14 GB image on disk plus datafiles and the Python environment. On Windows it checks the user-profile drive (`$HOME`), where Docker Desktop and Podman keep their WSL disks |
| Container engine memory | What Docker Desktop, Colima, or the Podman machine gives containers (not the host RAM); warns below 6 GB, 8 GB recommended. On Windows both engines use WSL2: `memory=8GB` under `[wsl2]` in `%UserProfile%\.wslconfig`, then `wsl --shutdown` |
| `.env` | Keeps DB/model settings consistent |
| `OAMP_LLM` and its credentials | Shared OCI keys present, or a reminder to set your own provider key; the smoke check makes the live call |
| Oracle image presence | Warns if the first startup will need a large download |

Warnings are usually survivable; hard failures should be fixed or routed to Codespaces.

---

## 5. Start Oracle AI Database

```bash
scripts/setup_oracle.sh
```

The script creates the container with the detected compose command (`docker compose up -d oracle-free` or `podman compose up -d oracle-free`) only when it does not exist yet: a stopped container is started, a running one is left untouched, so re-running never drops open notebook connections. It then verifies the pinned release-26 image digest, waits for SQL readiness, sizes the vector memory pool, and applies `sql/init/01-create-vector-user.sql`. First boot takes 3-5 minutes after the image pull, which is about a 4 GB download that extracts to about 14 GB on disk. The init script creates the `VECTOR` user and grants `CREATE MINING MODEL`, which `DBMS_VECTOR.LOAD_ONNX_MODEL` needs.

HNSW vector indexes (OAMP's, the toolbox's, the skillbox's) live in Oracle's vector memory pool, which ships at 0 on the Free image: without it every `CREATE VECTOR INDEX ... INMEMORY NEIGHBOR GRAPH` fails with `ORA-51962`. The pool is a static parameter, so on first setup the script sets `vector_memory_size=512M` in the SPFILE and restarts Oracle once (`WORKSHOP_VECTOR_MEMORY_MB` overrides the size).

Expected success lines:

```text
Using docker with compose command: docker compose
✓ release-26 Oracle image digest is pinned
✓ Oracle SQL is ready
Sizing the vector memory pool to 512 MB (was 0 MB); Oracle restarts once...
✓ Oracle SQL is ready
✓ vector memory pool: 512 MB
✓ VECTOR user can connect
```

Manual equivalent:

```bash
docker compose up -d            # or: podman compose up -d
docker logs -f agentic-memory-oracle   # or: podman logs -f agentic-memory-oracle
```

If the image pull is slow, leave it running: the workshop continues through Module 1 and Module 2 while the database warms up.

---

## 6. Install Python dependencies

```bash
uv sync --all-extras
uv run workshop-kernel
```

`--all-extras` installs the `notebooks` and `dev` extras: Jupyter Lab, `ipykernel`, `pandas`, `matplotlib`, `pytest`, and `ruff`. Plain `uv sync` does not install Jupyter, so `uv run jupyter lab` would fail.

`uv run workshop-kernel` registers the Jupyter kernel the notebooks ask for, `agentic-memory` ("Python (agentic-memory workshop)"), inside `.venv`. Naming it avoids `python3`: a `python3` kernel in your user Jupyter directory, left by another project, outranks the one in `.venv` and would start the labs in the wrong Python (or in a deleted one). The smoke check verifies the kernel.

Manual pip fallback:

```bash
python3 -m pip install -e ".[notebooks,dev]"    # Windows: py -3.12 -m pip install -e ".[notebooks,dev]"
workshop-kernel
```

The Python must be 3.11-3.13.

---

## 7. Load the ONNX embedding model

The skillbox/toolbox mini-lab uses in-database embeddings:

```sql
VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING :text AS DATA)
```

Load that model before Lab 1 (the Break 1 checkpoint):

```bash
uv run python scripts/load_onnx_model.py
```

What happens under the hood:

1. `onnx2oracle` downloads/builds the `all-MiniLM-L12-v2` augmented ONNX pipeline.
2. The tokenizer, transformer, pooling, and normalization are packed into one Oracle-callable graph.
3. The graph is loaded with `DBMS_VECTOR.LOAD_ONNX_MODEL`.
4. The script verifies `USER_MINING_MODELS` and runs a sample `VECTOR_EMBEDDING` query.

Reload if needed:

```bash
uv run python scripts/load_onnx_model.py --force
```

---

## 8. Run final smoke checks

Offline artifact check:

```bash
uv run workshop-smoke-check --offline
```

Full workshop readiness check:

```bash
uv run workshop-smoke-check --require-onnx
```

If this passes, your machine is ready for the live labs. It is the Break 1 checkpoint in the agenda. It includes one live LLM call; pass `--skip-llm` to check everything else when you deliberately run without an LLM.

---

## 9. Start Jupyter

```bash
uv run jupyter lab
```

Run notebooks in order:

1. `notebooks/01_oamp_memory_agent.ipynb` (Lab 1)
2. `notebooks/02_skillbox_toolbox.ipynb` (Module 4 mini-lab)
3. `notebooks/03_synthetic_memory_bootstrap.ipynb` (Lab 2)

The notebooks open on the **Python (agentic-memory workshop)** kernel. Lab 1 ends with two LLM turns: turn 1 asks for three restaurant suggestions, and turn 2, `Book the first one you suggested`, only works because the thread context card carries those suggestions. If the LLM is not configured, that section skips with the reason and the rest of the lab still runs.

To run all three end to end without opening Jupyter (stops at the first failing cell):

```bash
mkdir -p /tmp/labs
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/01_oamp_memory_agent.ipynb
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/02_skillbox_toolbox.ipynb
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/03_synthetic_memory_bootstrap.ipynb
```

---

## One-command run

For a clean machine or throwaway VM:

```bash
scripts/install_all.sh
```

This runs preflight, starts Oracle, installs `uv` if needed, syncs dependencies, loads the ONNX model, and runs the final smoke check.

---

## Codespaces

If local Docker, Podman, or Python setup fails, use [`CODESPACES.md`](CODESPACES.md). The Codespace provisions everything on creation: Python environment, Oracle container, vector memory pool, ONNX model, LLM keys, and the readiness check.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker: command not found` / `podman: command not found` | Install either engine from step 1. |
| `Cannot connect to the Docker daemon` | Start Docker Desktop/Engine; on Linux, ensure your user is in the `docker` group. |
| `docker compose` missing | Upgrade Docker Desktop or install the Compose v2 plugin. |
| `podman info` fails on macOS/Windows | `podman machine init --memory 8192` once, then `podman machine start`. If a machine already exists the scripts start it; if the start fails, the error is shown. |
| Windows: Podman machine start fails, or "CPU virtualization is off" | Enable Intel VT-x / AMD SVM Mode in the BIOS/UEFI (Task Manager > Performance > CPU must show "Virtualization: Enabled"), or use Codespaces. |
| Windows: `python3` prints "Python was not found" | Microsoft Store alias; ignore it. `uv` downloads a matching Python 3.11-3.13. |
| Windows: `uv sync` fails with "Access is denied" and leaves `.venv` partial | A Jupyter kernel from `.venv` (for example a notebook open in VS Code) locks its `.pyd` files. Stop the kernel or close the notebook, then rerun `uv sync --all-extras`. |
| Windows: `$'\r': command not found` when a script runs in WSL or a container | The checkout predates `.gitattributes` and has CRLF line endings (Git Bash itself tolerates them). Clone the repository again: `.gitattributes` keeps `.sh` and `.sql` files LF. |
| `podman compose` missing on Linux | `sudo apt-get install -y podman-compose` (or install the docker-compose provider). |
| `podman compose` fails with `dial unix /run/user/.../podman.sock` | The docker-compose provider needs the Podman API socket: `systemctl --user start podman.socket` (Linux), then rerun. Installing `podman-compose` also works and the scripts then prefer it. |
| Oracle cannot read its init script under Podman on SELinux | `chcon -Rt container_file_t sql` from the repo root, then recreate the container. |
| Oracle never becomes healthy | Check `docker logs agentic-memory-oracle --tail 100` (or `podman logs ...`); first boot can be slow. If credentials are stale, remove the volume and retry. |
| `Wrong Oracle container image` | The container runs a different image. Remove the volume and rerun `scripts/setup_oracle.sh`. |
| `ORA-01017` invalid username/password | Stale volume from an earlier image: remove it with `docker compose down -v` (or `podman compose down -v`), then run `scripts/setup_oracle.sh`. |
| Host port 1526 already taken | Set `ORACLE_HOST_PORT=1527` and `DB_CONNECT_STRING=localhost:1527/FREEPDB1` in `.env`, then rerun. Change it in `.env`: `podman-compose` substitutes from that file even when the shell exports a different value. |
| OAMP import fails | Run `uv sync --all-extras` or `python3 -m pip install -e ".[notebooks,dev]"` (Python 3.11-3.13). |
| `onnx2oracle` command missing | Run `uv sync --all-extras`; it is a project dependency. Current package metadata allows the published embedding-loader release (`>=0.1.1`). |
| `CREATE MINING MODEL` denied | Recreate the container with the provided init SQL or grant `CREATE MINING MODEL` to `VECTOR`. |
| `ALL_MINILM_L12_V2` missing | Run `uv run python scripts/load_onnx_model.py`. |
| `VECTOR_EMBEDDING` fails | Confirm the model exists with `uv run workshop-smoke-check --require-onnx`. |
| `ORA-51962` on HNSW index creation | The vector memory pool is unsized: rerun `scripts/setup_oracle.sh`, which sets `vector_memory_size=512M` and restarts Oracle once. |
| Context card is empty | Add more messages, or run extraction with the LLM configured. |
| `✗ LLM call` in the smoke check, or Lab 1 skips the LLM turns | The message names the cause. Compare the `OAMP_LLM` and `OCI_GENAI_*` lines in `.env` with `.env.example`, or set your own provider key. |
| Notebook cannot see `.env` | Start Jupyter from the attendee repo root and run the notebooks in order. |
| Kernel fails to start: `No such file or directory: .../bin/python`, or `No such kernel named agentic-memory` | Run `uv run workshop-kernel`, then restart Jupyter. |
