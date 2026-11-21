# Live-Tested Setup Guardrails

This file captures the exact failure modes found while validating the workshop environment, so future instructors and attendees do not repeat them. Most evidence was collected with Docker; the Podman rows are marked as detection-verified or runtime-verified.

## Non-negotiables

| Guardrail | Why it exists |
|---|---|
| Use the pinned release-26 image digest in `docker-compose.yml`. | A previous run accidentally used a different image family. `setup_oracle.sh` fails if the running container image does not match the pinned digest. |
| Let the scripts detect the engine, or pin it with `CONTAINER_ENGINE`. | Attendees arrive with Docker **or** Podman. Hardcoding `docker` breaks half the room; the shared `scripts/container_engine.sh` keeps one implementation for preflight, setup, and the one-command run. |
| Use the term **Oracle AI Database** in prose. | Workshop and book language should stay aligned with current product naming instead of tying the narrative to old database-version wording. |
| Use host port `1526` by default. | Port `1521` is commonly already occupied by another Oracle container. The container still listens on `1521`; the host maps `1526 -> 1521`. |
| Use `ORACLE_PWD`, not `ORACLE_PASSWORD`, for the official container. | The official container reads `ORACLE_PWD`. Using the wrong environment variable silently breaks first-boot credentials. |
| Mount setup SQL at `/opt/oracle/scripts/setup`. | The official container runs setup scripts from that path. Other image families use different init directories. |
| Install `oracleagentmemory` and `litellm` as separate packages. | The published OAMP package used in validation does not expose a `litellm` extra. |
| Keep `onnx2oracle>=0.1.1` unless PyPI publishes a newer compatible release. | The attempted `>=0.2.0` constraint was unsatisfiable during validation. |
| Install `uv` with the official installer when system Python is externally managed. | Some Linux systems reject `python -m pip install --upgrade uv` under PEP 668. |
| Use `uv sync --all-extras`, not plain `uv sync`. | Jupyter Lab, `ipykernel`, `pandas`, and `matplotlib` live in the `notebooks` extra; plain `uv sync` leaves `uv run jupyter lab` broken. |
| Run the notebooks on the `agentic-memory` kernel (`uv run workshop-kernel`), not `python3`. | A `python3` kernelspec in the user's Jupyter directory (`~/Library/Jupyter/kernels` on macOS, `~/.local/share/jupyter/kernels` on Linux) outranks the one inside `.venv`. In the dry run it pointed at a deleted virtualenv and `nbconvert` failed with `No such file or directory: .../bin/python`. The notebooks now name `agentic-memory`, registered inside `.venv`, and the smoke check verifies it runs the `.venv` Python. |
| Use `OAMP_EMBEDDER=oracle-db` for base labs. | The base workshop should not require an external embedding API. Embeddings run through Oracle `VECTOR_EMBEDDING` after ONNX load. |
| Cap what goes into `VECTOR_EMBEDDING`. | `ALL_MINILM_L12_V2` accepts at most 512 tokens and fails with `ORA-54401: ONNX runtime error ... core_/embeddings/Add_1` instead of truncating. `get_context_card()` searches with the recent messages, so a long LLM reply in Lab 1 tripped it after the two-turn demo. `OracleVectorEmbedder` keeps the first 2,000 characters and halves again on `ORA-54401`. |
| Verify the LLM with a live call, not by looking for a `*_API_KEY`. | An unrelated key (another provider, another project) used to turn the readiness check green while Lab 1 skipped its LLM cells. `workshop-smoke-check` now calls `OAMP_LLM` once through `agentic_memory_workshop.llm`, the same path the notebooks use. |
| Keep the shared OCI Generative AI keys out of the repository: Codespaces secrets plus `.devcontainer/env-from-secrets.sh`, collaborators only. | `.env.example` leaves the six `OCI_GENAI_*API_KEY*` values blank. Collaborators' Codespaces receive them as Codespaces secrets, copied into `.env` on create and on start; secrets are injected only when a Codespace starts, so a Codespace created before accepting the invitation needs a stop and restart. Three keys on Phoenix, three on Chicago; `llm.py` shuffles them per process and fails over on 401/403/404/429/5xx and network errors. |
| Size the vector memory pool before any HNSW index. | Oracle AI Database Free ships with `vector_memory_size=0`, so `CREATE VECTOR INDEX ... INMEMORY NEIGHBOR GRAPH` fails with `ORA-51962`. `setup_oracle.sh` sets 512 MB in the SPFILE and restarts once; the smoke check builds a throwaway HNSW index to prove it. `skillbox.py` and `toolbox.py` keep their exact-scan fallback only as a last resort. |
| Never recreate a running container from `setup_oracle.sh`. | With Podman and the docker-compose provider, every `compose up -d` recreated the container and open notebook connections died with `DPY-4011`. The script now runs compose only when the container does not exist, starts a stopped one, and leaves a running one alone. |
| Keep `requires-python = ">=3.11,<3.14"`. | `onnxruntime` 1.24.3 has no cp310 wheels and `onnxruntime-extensions` has no cp314 wheels. uv skips such interpreters and downloads a matching Python, so attendees need no particular system Python. |
| Keep the `[tool.uv] required-environments` entry for Windows x64. | It makes uv lock `onnxruntime-extensions` 0.15.0 on Windows, because 0.15.2 ships no Windows wheels (same Python code); everywhere else it locks 0.15.2. |
| Do not rely on `python3`/`python` on a Windows `PATH`. | They are often Microsoft Store aliases that only print "Python was not found". Preflight no longer checks `python3`; it prints what `uv python find` picks. |
| Force UTF-8 output in the Python CLIs. | On Windows, redirected output used cp1252 and the check marks raised `UnicodeEncodeError`. `workshop-smoke-check`, `workshop-kernel`, `synthesize-memory` and `scripts/load_onnx_model.py` reconfigure their streams. |
| Keep the `onnx2oracle` temp-file workaround in `scripts/load_onnx_model.py`. | On Windows with `onnx2oracle` 0.1.1 the ONNX build ended with `PermissionError` (WinError 32): the library deletes its temp file while it is still open. The script runs `onnx2oracle` in-process and works around it on Windows. |
| Keep `.gitattributes` (`*.sh`, `*.sql` stay LF). | A CRLF checkout breaks bash scripts and the init SQL. `setup_oracle.sh` also strips CR from the init SQL before piping it to `sqlplus`. |
| Stop any kernel running from `.venv` before `uv sync` on Windows. | A running Jupyter kernel (for example a notebook open in VS Code) locks its `.pyd` files; `uv sync` then fails with "Access is denied" and leaves the venv partial. Stop the kernel, rerun `uv sync --all-extras`. |
| Require about 20 GB free disk before the session. | The pinned image is about a 4 GB download and about 14 GB on disk after extraction, plus database files and the Python environment. `scripts/preflight.sh` warns below 20 GB; Podman on macOS/Windows also needs the machine disk to fit it (`--disk-size 40`). |

## Correct startup path

```bash
test -f .env || cp .env.example .env
scripts/preflight.sh
scripts/setup_oracle.sh
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras
uv run workshop-kernel
uv run python scripts/load_onnx_model.py
uv run workshop-smoke-check --require-onnx
```

`scripts/install_all.sh` runs the same sequence. In the live session a coding agent runs it from [`AGENTS.md`](AGENTS.md).

## Engine selection

`scripts/container_engine.sh`:

- honors `CONTAINER_ENGINE=docker|podman`;
- otherwise prefers Docker when `docker info` succeeds, then Podman when `podman info` succeeds;
- resolves compose as `docker compose`, then `podman compose`, then `podman-compose`;
- routes `compose up/ps`, `inspect`, `exec`, `logs`, and `image inspect` through the chosen engine.

The pinned-digest guard reads `.Config.Image` on Docker and `.ImageName` on Podman, with an image-ID comparison as a fallback, so both engines pass the same check.

Podman notes verified during validation:

| Case | Evidence |
|---|---|
| Linux rootless Podman and compose resolution | Verified: with Docker unusable on `PATH`, preflight selects podman; when the `podman compose` provider is unavailable the shared library falls back to `podman-compose` (stubbed-engine branch test). |
| Podman compose file parsing | Verified: both `podman compose config` and `podman-compose config` parse `docker-compose.yml`. |
| Docker present but unusable, Podman healthy | Verified: with a broken `docker` on `PATH`, preflight selects `podman` and `podman compose` and completes without hard failures. |
| Linux Podman without the API socket | Verified failure then fix: `podman compose up` delegating to docker-compose failed with `dial unix /run/user/.../podman.sock`. The scripts now prefer `podman compose` only when `podman info` reports `RemoteSocket.Exists=true`, and otherwise fall back to `podman-compose`, which needs no socket. |
| Port override precedence | Verified: `podman-compose config` resolves `ORACLE_HOST_PORT` from `.env` even when the shell exports a different value, while `docker compose config` prefers the shell value. To move the host port, change it in `.env`. |
| macOS Podman | Not verified here; documented requirement is `podman machine init --memory 8192` then `podman machine start` (Oracle AI Database Free needs the RAM). |
| Windows 11 + Git Bash: Python side | Verified: `uv sync` (Windows locks `onnxruntime-extensions` 0.15.0; without conda uv picked Python 3.11 rather than 3.14), `workshop-kernel`, the smoke check's file, import and kernel checks plus a live LLM call, and the ONNX build (graph output matches the Hugging Face reference, cosine 1.00000). |
| Windows 11 + Git Bash: Podman detection | Verified with a real Podman 5.4.2 WSL machine: preflight and `setup_oracle.sh` detected it, and its start failed because virtualization was off in the firmware; the error was surfaced. Stubbed-engine branch tests passed for: stopped machine started, Docker preferred with the Podman machine untouched, pinned Podman, no machine, start failure. |
| Windows: Oracle container | **Not run on Windows**: the validation PC has virtualization disabled. Compose up, the CRLF-stripped init SQL and the ONNX upload to Oracle were not exercised on Windows. On Linux (GitHub Codespaces, Docker) the same `setup_oracle.sh` and the in-process `load_onnx_model.py` ran end to end, followed by all three labs. |
| SELinux hosts | A rootless Podman container cannot read the bind-mounted `sql/init` until the files are labeled `container_file_t`: `chcon -Rt container_file_t sql`. |

## Correct image

The workshop image is pinned in `docker-compose.yml`:

```text
container-registry.oracle.com/database/free@sha256:8a8084193724b95bc62247e3af4218b357e4f172c78925551b2181dbe2566232
```

Do not replace it with a convenience tag or a different image family for the live workshop.

## Correct readiness evidence

A ready environment shows:

- The selected container engine is reachable (`docker info` or `podman info`).
- A compose command resolves.
- Oracle container healthy.
- Setup script confirms the pinned image digest.
- `uv sync --all-extras` resolves.
- `ALL_MINILM_L12_V2` registered in Oracle.
- `VECTOR_EMBEDDING` returns a sample vector.
- OAMP can add/search memory with `OAMP_EMBEDDER=oracle-db`.
- Lab 1 sends the context card to the LLM, and turn 2 books the first of the three restaurants turn 1 suggested.
- Toolbox/skillbox can upsert and retrieve rows.
- Synthetic memory can generate and load into OAMP plus toolbox/skillbox.

## If something looks wrong

1. Stop and remove the local workshop volume. This deletes the container database, including memories written during the session, so confirm before running it.

   ```bash
   docker compose down -v     # or: podman compose down -v
   ```

2. Start over with the pinned image:

   ```bash
   scripts/setup_oracle.sh
   ```

3. Re-run the full readiness check:

   ```bash
   uv run workshop-smoke-check --require-onnx
   ```
