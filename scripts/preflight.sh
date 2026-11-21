#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/container_engine.sh
. "$ROOT/scripts/container_engine.sh"

WORKSHOP_ORACLE_IMAGE="container-registry.oracle.com/database/free@sha256:8a8084193724b95bc62247e3af4218b357e4f172c78925551b2181dbe2566232"

fail=0
ok() { printf '✓ %s\n' "$1"; }
warn() { printf '⚠ %s\n' "$1"; }
bad() { printf '✗ %s\n' "$1"; fail=1; }

printf '\nDesigning and Building Memory for AI Agents - preflight\n'
printf '========================================================\n\n'

case "$(uname -s)" in
  Darwin) ok "macOS detected (Docker Desktop or Podman machine)" ;;
  Linux) ok "Linux detected" ;;
  MINGW*|MSYS*|CYGWIN*) ok "Windows detected (Git Bash); containers run in Docker Desktop or a Podman machine on WSL2" ;;
  *) warn "Unknown OS: $(uname -s)" ;;
esac

if command -v uv >/dev/null 2>&1; then
  ok "uv installed: $(uv --version | tr -d '\r')"
  # uv installs and runs the project's Python (requires-python in pyproject.toml), so a system
  # python3 is optional. On Windows a python3 on PATH is often a Microsoft Store alias and proves nothing.
  if py_version="$(uv python find --show-version 2>/dev/null | tr -d '\r')" && [ -n "$py_version" ]; then
    py_path="$(uv python find 2>/dev/null | tr -d '\r' || true)"
    ok "Python for the workshop: $py_version (${py_path:-path unknown})"
  else
    warn "no installed Python matches requires-python in pyproject.toml; 'uv sync' downloads a matching one automatically"
  fi
else
  warn "uv missing; install with: curl -LsSf https://astral.sh/uv/install.sh | sh (works in Git Bash too; Windows PowerShell: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\")"
fi

printf '\nContainer engine:\n'
# Detection first: it may start a stopped Podman machine. The per-engine lines below
# only observe, so keep the detected selection and restore it afterwards.
requested_engine="${CONTAINER_ENGINE:-}"
selected_engine=""
selected_compose=()
if container_engine_detect; then
  selected_engine="$CONTAINER_ENGINE"
  selected_compose=("${COMPOSE_CMD[@]}")
fi

for engine in docker podman; do
  if ce_installed "$engine"; then
    ok "$engine installed: $("$engine" --version 2>&1 | head -1 | tr -d '\r')"
    if ce_daemon_ready "$engine"; then
      ok "$engine daemon is reachable"
      if ce_compose_available "$engine"; then
        ok "$engine compose available: ${COMPOSE_CMD[*]}"
        if [ "$engine" = podman ] && ! ce_podman_socket_running && [ "${COMPOSE_CMD[0]}" = podman ]; then
          warn "podman API socket is not running; 'podman compose' needs it: systemctl --user start podman.socket"
        fi
      elif [ "$engine" = podman ]; then
        warn "podman has no compose provider"
        container_engine_hint podman-compose
      else
        warn "docker compose is not available; install the compose plugin, see SETUP.md step 2"
      fi
    elif [ "$engine" = podman ]; then
      if ce_desktop_os; then
        machines="$(podman machine list --format '{{.Name}}' 2>/dev/null | tr -d '\r' || true)"
        if [ -n "$machines" ]; then
          warn "podman is installed but its machine is not running (or failed to start, see above); start it with: podman machine start"
        else
          warn "podman is installed but no podman machine exists yet"
          container_engine_hint podman
        fi
      else
        warn "podman is installed but 'podman info' fails; check the podman service/socket"
      fi
    else
      warn "docker is installed but the daemon is not running/reachable"
      if ce_desktop_os; then container_engine_hint docker; fi
    fi
  else
    warn "$engine is not installed"
  fi
done

# Restore the selection the per-engine checks above may have overwritten.
CONTAINER_ENGINE="$selected_engine"
COMPOSE_CMD=()
if [ -n "$selected_engine" ]; then
  export CONTAINER_ENGINE
  COMPOSE_CMD=("${selected_compose[@]}")
  ok "using container engine: $CONTAINER_ENGINE (compose: ${COMPOSE_CMD[*]})"
  if [ -n "$requested_engine" ]; then
    ok "engine pinned by CONTAINER_ENGINE=$requested_engine"
  fi
else
  bad "no usable container engine; install Docker or Podman (see SETUP.md step 2)"
  container_engine_hint docker
  if ce_installed podman && ce_daemon_ready podman; then
    container_engine_hint podman-compose
  else
    container_engine_hint podman
  fi
  if ce_windows_virtualization_off; then
    bad "$(ce_virtualization_message)"
  fi
fi

free_kb=0
if command -v df >/dev/null 2>&1; then
  disk_target=.
  disk_where="in this filesystem"
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      # Docker Desktop and Podman keep their WSL disks under the user profile.
      disk_target="$HOME"
      disk_where="on the drive of your user profile ($HOME), where Docker Desktop and Podman keep their WSL disks"
      ;;
  esac
  free_kb=$(df -Pk "$disk_target" | awk 'NR==2 {print $4}')
  if [ "${free_kb:-0}" -ge 20971520 ]; then
    ok "disk free >= 20 GB $disk_where"
  else
    warn "less than 20 GB free $disk_where; the Oracle image is about 14 GB on disk (about 4 GB download) plus datafiles and the Python environment"
  fi
fi

# Oracle runs inside the engine's VM on macOS/Windows (Docker Desktop, Colima, Podman machine),
# so the memory that matters is what the engine reports, not the host's.
if [ -n "${CONTAINER_ENGINE:-}" ]; then
  case "$CONTAINER_ENGINE" in
    docker) engine_mem=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0) ;;
    podman) engine_mem=$(podman info --format '{{.Host.MemTotal}}' 2>/dev/null || echo 0) ;;
  esac
  # Round to the nearest GB: a 6 GB VM reports ~5.8 GB after the kernel's reservation.
  engine_mem_gb=$(( (${engine_mem:-0} + 536870912) / 1073741824 ))
  if [ "$engine_mem_gb" -ge 6 ]; then
    ok "$CONTAINER_ENGINE has ${engine_mem_gb} GB of memory for containers"
  else
    case "$(uname -s)" in
      MINGW*|MSYS*|CYGWIN*)
        warn "$CONTAINER_ENGINE has only ${engine_mem_gb} GB for containers; on Windows both engines get their memory from WSL2 (half of the RAM by default): put memory=8GB under [wsl2] in %UserProfile%\\.wslconfig, run: wsl --shutdown, then restart the engine (or use Codespaces)"
        ;;
      *)
        warn "$CONTAINER_ENGINE has only ${engine_mem_gb} GB for containers; Oracle needs about 2 GB plus headroom, give it 8 GB (podman machine set --memory 8192, or Docker Desktop > Resources) or use Codespaces"
        ;;
    esac
  fi
fi

if [ -f .env ]; then ok ".env exists"; else warn ".env missing; setup_oracle.sh copies .env.example for you, or run: cp .env.example .env"; fi

env_file=.env
[ -f "$env_file" ] || env_file=.env.example
# shellcheck disable=SC1090
set -a; source "$env_file"; set +a
if [ -n "${OCI_GENAI_ENDPOINT:-}${OCI_GENAI_FALLBACK_ENDPOINT:-}" ]; then
  if env | grep -Eq '^OCI_GENAI_(FALLBACK_)?API_KEY(_[0-9])?=.+'; then
    ok "OAMP_LLM=${OAMP_LLM:-unset} through the shared OCI Generative AI keys"
  else
    warn "OCI_GENAI_ENDPOINT is set but no OCI_GENAI_API_KEY* value is; copy them from .env.example"
  fi
elif [ -n "${OAMP_LLM:-}" ]; then
  warn "OAMP_LLM=$OAMP_LLM uses your own provider key; make sure that provider's key is set"
else
  warn "OAMP_LLM is not set; copy .env.example to .env"
fi
printf '  (the smoke check makes a live LLM call, which is the real test)\n'

if [ -n "${CONTAINER_ENGINE:-}" ]; then
  if "$CONTAINER_ENGINE" image inspect "$WORKSHOP_ORACLE_IMAGE" >/dev/null 2>&1; then
    ok "release-26 Oracle image digest already pulled"
  else
    warn "release-26 Oracle image digest not present yet; setup_oracle.sh will pull it"
  fi
fi

printf '\nNext setup steps (run them during the live session if not done yet):\n'
printf '  scripts/setup_oracle.sh\n'
printf '  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh\n'
printf '  uv sync --all-extras\n'
printf '  uv run python scripts/load_onnx_model.py\n'
printf '  uv run workshop-smoke-check --require-onnx\n'
if [ -n "${CONTAINER_ENGINE:-}" ]; then
  printf '\nIf Oracle misbehaves, recreating the volume fixes most issues (it deletes local DB data):\n'
  printf '  %s down -v && scripts/setup_oracle.sh\n' "${COMPOSE_CMD[*]}"
fi
printf '\n'

if [ "$fail" -eq 0 ]; then
  ok "preflight completed without hard failures"
else
  bad "preflight found hard failures; use SETUP.md for install links"
fi
exit "$fail"
