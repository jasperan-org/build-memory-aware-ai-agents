#!/usr/bin/env bash
# Codespaces postStartCommand: a stopped Codespace resumes with the Oracle container stopped.
# setup_oracle.sh starts it again and leaves an already running container untouched. Secrets
# are injected when a Codespace starts, so a restart also picks up keys granted since creation.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash .devcontainer/env-from-secrets.sh
bash .devcontainer/wait-for-docker.sh
scripts/setup_oracle.sh
