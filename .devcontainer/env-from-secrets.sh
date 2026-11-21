#!/usr/bin/env bash
# Codespaces secrets reach a Codespace as environment variables (repository secrets only for
# collaborators with write access, injected when the Codespace starts). Copy every key of
# .env.example that the environment provides into .env, so notebooks, `uv run` and ssh sessions
# all read the same values. Values are never printed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

[ -f .env ] || cp .env.example .env

copied=0
for name in $(sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env.example); do
  [ -n "${!name:-}" ] || continue
  tmp="$(mktemp)"
  NAME="$name" awk '
    BEGIN { name = ENVIRON["NAME"]; line = name "=" ENVIRON[name] }
    index($0, name "=") == 1 { if (!done) print line; done = 1; next }
    { print }
    END { if (!done) print line }
  ' .env >"$tmp"
  mv "$tmp" .env
  copied=$((copied + 1))
done
echo "Codespaces secrets copied into .env: ${copied}"
