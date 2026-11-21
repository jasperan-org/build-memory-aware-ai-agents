#!/usr/bin/env bash
# Codespaces postCreateCommand: copy Codespaces secrets into .env, install the VS Code notebook
# extensions, start Oracle, size the vector pool, load the ONNX model, verify.
# Every step is idempotent; rerun by hand with: bash .devcontainer/post-create.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash .devcontainer/env-from-secrets.sh
bash .devcontainer/vscode-extensions.sh
bash .devcontainer/wait-for-docker.sh
scripts/setup_oracle.sh
uv run python scripts/load_onnx_model.py
if uv run workshop-smoke-check --require-onnx; then
  echo
  echo "Workshop environment ready. Open a notebook in notebooks/ and Run All; its kernel is"
  echo "'Python (agentic-memory workshop)'. Jupyter Lab instead: uv run jupyter lab --no-browser --ip 0.0.0.0"
else
  echo
  echo "Readiness check failed; see TROUBLESHOOTING.md, then rerun: bash .devcontainer/post-create.sh"
fi
