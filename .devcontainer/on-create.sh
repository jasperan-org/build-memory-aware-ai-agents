#!/usr/bin/env bash
# Codespaces onCreateCommand: everything that does not need Docker, so prebuilds can cache it.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v uv >/dev/null 2>&1; then
  python -m pip install --quiet --no-cache-dir uv
fi
uv sync --all-extras
uv run workshop-kernel
# Also in the user's Jupyter directory: VS Code then finds a kernel that matches the notebooks'
# kernelspec exactly and selects it on its own, so Run All needs no kernel prompt.
uv run workshop-kernel --user

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example (shared workshop LLM keys included)."
fi

uv run workshop-smoke-check --offline
