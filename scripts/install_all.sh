#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Both scripts detect Docker or Podman themselves (CONTAINER_ENGINE=docker|podman overrides).
scripts/preflight.sh
scripts/setup_oracle.sh

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is missing; installing it for the current user..."
  if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
    echo "official uv installer failed; trying a pip user install..."
    python3 -m pip install --user --upgrade uv
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

uv sync --all-extras
uv run workshop-kernel
uv run python scripts/load_onnx_model.py
uv run workshop-smoke-check --require-onnx

echo "✓ Workshop environment ready. Start notebooks with: uv run jupyter lab"
