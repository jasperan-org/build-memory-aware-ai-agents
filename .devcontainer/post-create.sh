#!/usr/bin/env bash
# Codespaces postCreateCommand: copy Codespaces secrets into .env, start Oracle, size the vector
# pool, load the ONNX model, verify.
# Every step is idempotent; rerun by hand with: bash .devcontainer/post-create.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash .devcontainer/env-from-secrets.sh
bash .devcontainer/wait-for-docker.sh
scripts/setup_oracle.sh
uv run python scripts/load_onnx_model.py
if uv run workshop-smoke-check --require-onnx; then
  echo
  echo "Workshop environment ready. Open notebooks/01_oamp_memory_agent.ipynb and pick the .venv kernel,"
  echo "or run: uv run jupyter lab --no-browser --ip 0.0.0.0"
else
  echo
  echo "Readiness check failed; see TROUBLESHOOTING.md, then rerun: bash .devcontainer/post-create.sh"
fi
