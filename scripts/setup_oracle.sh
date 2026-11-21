#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/container_engine.sh
. "$ROOT/scripts/container_engine.sh"

# Same reference as docker-compose.yml: the official image locally, ORACLE_IMAGE in Codespaces.
EXPECTED_ORACLE_IMAGE="${ORACLE_IMAGE:-container-registry.oracle.com/database/free@sha256:8a8084193724b95bc62247e3af4218b357e4f172c78925551b2181dbe2566232}"
CONTAINER_NAME="agentic-memory-oracle"
ORACLE_PASSWORD_VALUE="VectorPwd_2025"
# HNSW pool for OAMP, toolbox, and skillbox indexes; carved out of the 1.5 GB SGA of the Free image.
VECTOR_MEMORY_MB="${WORKSHOP_VECTOR_MEMORY_MB:-512}"

requested_engine="${CONTAINER_ENGINE:-}"
if ! container_engine_detect; then
  echo "No usable container engine found. Install Docker or Podman, then rerun." >&2
  case "$requested_engine" in
    docker | podman)
      container_engine_hint "$requested_engine" >&2
      ;;
    *)
      if ce_installed docker; then
        echo "Docker is installed but its daemon or compose plugin is not usable." >&2
      fi
      if ce_installed podman; then
        echo "Podman is installed but its machine/service or compose provider is not usable." >&2
      fi
      container_engine_hint docker >&2
      container_engine_hint podman >&2
      if ce_windows_virtualization_off; then
        ce_virtualization_message >&2
      fi
      ;;
  esac
  echo "See SETUP.md step 2 and TROUBLESHOOTING.md." >&2
  exit 1
fi

echo "Using ${CONTAINER_ENGINE} with compose command: ${COMPOSE_CMD[*]}"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example (it carries the shared workshop LLM keys)."
fi

# Never recreate a running container: open notebook connections would drop (DPY-4011).
# `compose up` can decide to recreate even when nothing changed (seen with podman + the
# docker-compose provider), so compose only creates a container that does not exist yet.
container_state="$("$CONTAINER_ENGINE" inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null || true)"
case "$container_state" in
  true)
    echo "✓ $CONTAINER_NAME is already running; leaving it untouched"
    ;;
  false)
    echo "Starting the existing $CONTAINER_NAME container..."
    "$CONTAINER_ENGINE" start "$CONTAINER_NAME" >/dev/null
    ;;
  *)
    echo "Creating the Oracle AI Database release-26 workshop container..."
    if ! "${COMPOSE_CMD[@]}" up -d oracle-free; then
      echo "✗ compose could not start the Oracle container." >&2
      if [ "$CONTAINER_ENGINE" = podman ] && [ "${COMPOSE_CMD[0]}" = podman ]; then
        echo "  'podman compose' usually delegates to docker-compose, which needs the Podman API socket." >&2
        echo "  Start it with: systemctl --user start podman.socket    # Linux" >&2
        echo "  Installing podman-compose also works; the scripts then prefer it." >&2
      fi
      echo "  See TROUBLESHOOTING.md." >&2
      exit 4
    fi
    ;;
esac

actual_image="$(container_image_reference "$CONTAINER_NAME")"
if [ "$actual_image" != "$EXPECTED_ORACLE_IMAGE" ]; then
  # Engines and image transports report the reference differently (a digest-pinned
  # pull can surface as a name or as a local image ID). Accept an ID match too.
  actual_id="$(container_image_id "$CONTAINER_NAME")"
  expected_id="$("$CONTAINER_ENGINE" image inspect --format='{{.Id}}' "$EXPECTED_ORACLE_IMAGE" 2>/dev/null || true)"
  if [ -z "$actual_id" ] || [ "$actual_id" != "$expected_id" ]; then
    echo "✗ Wrong Oracle container image: $actual_image" >&2
    echo "  Expected: $EXPECTED_ORACLE_IMAGE" >&2
    echo "  Run: ${COMPOSE_CMD[*]} down -v && scripts/setup_oracle.sh" >&2
    exit 2
  fi
fi
echo "✓ release-26 Oracle image digest is pinned"

sql_ready() {
  "$CONTAINER_ENGINE" exec "$CONTAINER_NAME" \
    bash -lc "echo 'select 1 from dual;' | sqlplus -s $1/${ORACLE_PASSWORD_VALUE}@localhost/FREEPDB1 | grep -q '^[[:space:]]*1'" >/dev/null 2>&1
}

wait_for_sql() {
  echo "Waiting for Oracle SQL readiness (first boot can take several minutes)..."
  for _ in $(seq 1 90); do
    if sql_ready system; then
      echo "✓ Oracle SQL is ready"
      return 0
    fi
    printf '.'
    sleep 10
  done
  echo
  echo "Oracle SQL did not become ready in time. Last logs:"
  "$CONTAINER_ENGINE" logs "$CONTAINER_NAME" --tail 100 || true
  exit 1
}

cdb_sql() {
  "$CONTAINER_ENGINE" exec -i "$CONTAINER_NAME" bash -lc "sqlplus -s / as sysdba"
}

wait_for_sql

# HNSW vector indexes live in the vector memory pool, which ships at 0 on Oracle AI Database
# Free: every CREATE VECTOR INDEX ... INMEMORY NEIGHBOR GRAPH then fails with ORA-51962. The
# pool is static, so it is set in the SPFILE and Oracle restarts once, on first setup only.
vector_mb="$(printf "set heading off feedback off pagesize 0\nselect round(value/1048576) from v\$parameter where name = 'vector_memory_size';\nexit\n" | cdb_sql | tr -d '[:space:]')"
if [ "${vector_mb:-0}" -ge "$VECTOR_MEMORY_MB" ] 2>/dev/null; then
  echo "✓ vector memory pool: ${vector_mb} MB"
else
  echo "Sizing the vector memory pool to ${VECTOR_MEMORY_MB} MB (was ${vector_mb:-0} MB); Oracle restarts once..."
  printf "whenever sqlerror exit failure\nalter system set vector_memory_size = %sM scope = spfile;\nexit\n" "$VECTOR_MEMORY_MB" | cdb_sql >/dev/null
  "$CONTAINER_ENGINE" restart -t 120 "$CONTAINER_NAME" >/dev/null
  wait_for_sql
  echo "✓ vector memory pool: ${VECTOR_MEMORY_MB} MB"
fi

echo "Applying workshop VECTOR user/grants..."
# Windows checkouts are CRLF; sqlplus runs in Linux, so hand it LF only.
tr -d '\r' < sql/init/01-create-vector-user.sql | "$CONTAINER_ENGINE" exec -i "$CONTAINER_NAME" \
  bash -lc "sqlplus -s sys/${ORACLE_PASSWORD_VALUE}@localhost/FREEPDB1 as sysdba"
if sql_ready VECTOR; then
  echo "✓ VECTOR user can connect"
  "${COMPOSE_CMD[@]}" ps
  exit 0
fi
echo "✗ VECTOR user was not able to connect after setup" >&2
exit 3
