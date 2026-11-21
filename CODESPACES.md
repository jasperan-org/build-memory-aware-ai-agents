# GitHub Codespaces

Codespaces runs the whole workshop in the browser: no Docker, Python, or API key on your machine. The devcontainer runs Oracle AI Database Free inside Docker-in-Docker, so the same `scripts/` run unchanged and the engine detection picks Docker.

> **Local setup failing on the day? Use the backup repository** <https://github.com/jasperan-org/build-memory-aware-ai-agents>: the same workshop, ready in GitHub Codespaces, with the shared OCI Generative AI keys already set as Codespaces secrets for collaborators (the workshop organizer pays for their Codespaces).
>
> 1. Ask the instructor to add you as a collaborator (write access) of <https://github.com/jasperan-org/build-memory-aware-ai-agents>.
> 2. Accept the invitation: the email from GitHub, or <https://github.com/jasperan-org/build-memory-aware-ai-agents/invitations>.
> 3. Create the Codespace: [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jasperan-org/build-memory-aware-ai-agents)
> 4. Created it before accepting? Stop the Codespace and start it again: the shared OCI Generative AI keys are injected as Codespaces secrets at start.
>
> Without an invitation you can still use the Packt repository's button below; your own GitHub account pays and you use the keys in `.env.example`.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/PacktPublishing/Build_Memory_Aware_AI_Agents)

## Attendee steps

1. Click the button above (or **Code → Codespaces → Create codespace on main** on the repository page).
2. Keep the default machine type: the devcontainer asks for 4 cores (16 GB RAM, 32 GB disk), which Oracle and the ONNX load need.
3. Wait for creation to finish, about 10 minutes the first time. Follow it in the **Codespaces: creation log** (Command Palette → *Codespaces: View Creation Log*). It is done when it prints `Workshop environment ready.`; an earlier `All requested checks passed.` comes from the offline file check that runs before Oracle starts.
4. In the Codespace terminal, confirm the environment:

   ```bash
   uv run workshop-smoke-check --require-onnx
   ```

5. Open `notebooks/01_oamp_memory_agent.ipynb`. If VS Code asks for a kernel: **Select Kernel → Python Environments → .venv**. Run the cells in order. Notebooks `02` and `03` follow.

Prefer Jupyter Lab? Run `uv run jupyter lab --no-browser --ip 0.0.0.0` in the terminal and open the forwarded port `8888`; the notebooks open on the **Python (agentic-memory workshop)** kernel.

Run Lab 1, the Module 4 mini-lab and Lab 2 end to end from the Codespace terminal (stops at the first failing cell):

```bash
mkdir -p /tmp/labs
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/01_oamp_memory_agent.ipynb
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/02_skillbox_toolbox.ipynb
uv run jupyter nbconvert --to notebook --execute \
  --output-dir /tmp/labs notebooks/03_synthetic_memory_bootstrap.ipynb
```

## What creation does

| Lifecycle step | Script | What it runs |
|---|---|---|
| `onCreateCommand` | `.devcontainer/on-create.sh` | Installs `uv`, `uv sync --all-extras`, registers the `agentic-memory` notebook kernel (`workshop-kernel`), creates `.env` from `.env.example` (shared LLM keys included), offline smoke check |
| `postCreateCommand` | `.devcontainer/post-create.sh` | Copies any environment variable named like a key in `.env.example` (Codespaces secrets arrive that way) into `.env` via `.devcontainer/env-from-secrets.sh`, waits for Docker, `scripts/setup_oracle.sh` (container, vector memory pool, `VECTOR` user), `scripts/load_onnx_model.py`, `workshop-smoke-check --require-onnx` (includes a live LLM call) |
| `postStartCommand` | `.devcontainer/post-start.sh` | Repeats the secrets-to-`.env` copy (secrets are injected at start), then, after a stopped Codespace resumes, starts the Oracle container again; a running one is left untouched |

Every step is idempotent. If something failed, rerun it by hand:

```bash
bash .devcontainer/post-create.sh
```

## LLM keys

`.env.example` carries the shared OCI Generative AI keys for the session (rotated afterwards), so nothing needs to be configured. To use your own provider, edit `.env`: blank both `OCI_GENAI_*ENDPOINT` lines and set `OAMP_LLM` plus its key, then run `uv run workshop-smoke-check --require-onnx`.

## Instructor checks before the event

- Create a fresh Codespace from `main` and confirm the creation log ends with `Workshop environment ready.`; note the creation time. From your own terminal with the GitHub CLI:

  ```bash
  CS=$(gh codespace create -R PacktPublishing/Build_Memory_Aware_AI_Agents \
    -b main -m standardLinux32gb --display-name memory-dryrun)
  gh codespace ssh -c "$CS" -- tail -f /workspaces/.codespaces/.persistedshare/creation.log
  ```

  Stop the `tail` with Ctrl-C after `Workshop environment ready.`, run the notebook check above through `gh codespace ssh -c "$CS"`, then delete it: `gh codespace delete -c "$CS" -f`.
- Optional: enable **Codespaces prebuilds** for `main` (repository **Settings → Codespaces**, needs admin). Prebuilds cache the `on-create` step (Python environment); the Oracle image download and first boot still happen per Codespace.
- Codespaces stop after 30 idle minutes by default; the `postStartCommand` restarts Oracle on resume, and the data volume survives.
