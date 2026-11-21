# shellcheck shell=bash
# Shared container engine detection for the workshop scripts.
#
# Source this file, then call `container_engine_detect`. On success it sets
# CONTAINER_ENGINE (docker|podman) and COMPOSE_CMD (a bash array holding the
# compose command, e.g. `docker compose` or `podman-compose`).
#
# Override the choice with CONTAINER_ENGINE=docker|podman when both engines are
# installed and you want a specific one.

ce_installed() { command -v "$1" >/dev/null 2>&1; }

ce_daemon_ready() {
  case "$1" in
    docker) ce_installed docker && docker info >/dev/null 2>&1 ;;
    podman) ce_installed podman && podman info >/dev/null 2>&1 ;;
    *) return 1 ;;
  esac
}

# ce_podman_socket_running — true when the Podman API socket is up.
# `podman compose` usually delegates to docker-compose, which talks to that socket.
ce_podman_socket_running() {
  [ "$(podman info --format '{{.Host.RemoteSocket.Exists}}' 2>/dev/null)" = "true" ]
}

# ce_compose_available <engine> — sets COMPOSE_CMD when a compose command works.
ce_compose_available() {
  # shellcheck disable=SC2034  # COMPOSE_CMD is consumed by the scripts that source this file
  COMPOSE_CMD=()
  case "$1" in
    docker)
      if ce_installed docker && docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
        return 0
      fi
      ;;
    podman)
      if ce_installed podman && ce_podman_socket_running && podman compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(podman compose)
        return 0
      fi
      if ce_installed podman-compose; then
        COMPOSE_CMD=(podman-compose)
        return 0
      fi
      if ce_installed podman && podman compose version >/dev/null 2>&1; then
        # No socket and no podman-compose: the provider may not need the API socket.
        COMPOSE_CMD=(podman compose)
        return 0
      fi
      ;;
  esac
  return 1
}

# ce_desktop_os — true on macOS and Windows shells, where containers run in a VM.
ce_desktop_os() {
  case "$(uname -s)" in
    Darwin | MINGW* | MSYS* | CYGWIN*) return 0 ;;
  esac
  return 1
}

# ce_windows_virtualization_off — true on Windows when CPU virtualization is off in the firmware.
# While a hypervisor runs, VirtualizationFirmwareEnabled reads False even though it is on,
# so only "no hypervisor AND firmware flag False" proves it is off. Any error -> false.
ce_windows_virtualization_off() {
  case "$(uname -s)" in
    MINGW* | MSYS* | CYGWIN*) ;;
    *) return 1 ;;
  esac
  # powershell.exe is not always on Git Bash's PATH; fall back to its fixed location.
  local ps="powershell.exe" root
  if ! ce_installed "$ps"; then
    root="${SYSTEMROOT:-${SystemRoot:-C:\\Windows}}"
    command -v cygpath >/dev/null 2>&1 && root="$(cygpath -u "$root" 2>/dev/null || echo "$root")"
    ps="$root/System32/WindowsPowerShell/v1.0/powershell.exe"
    [ -x "$ps" ] || return 1
  fi
  local out
  out="$("$ps" -NoProfile -NonInteractive -Command \
    'Write-Output ([string](Get-CimInstance Win32_ComputerSystem).HypervisorPresent,[string](Get-CimInstance Win32_Processor | Select-Object -First 1).VirtualizationFirmwareEnabled -join [char]32)' \
    2>/dev/null | tr -d '\r')" || return 1
  [ "$out" = "False False" ]
}

# ce_virtualization_message — what to tell the user when virtualization is off.
ce_virtualization_message() {
  echo "CPU virtualization is off in the BIOS/UEFI; Docker Desktop and Podman need it (Intel VT-x / AMD SVM Mode). Enable it, reboot and rerun, or use Codespaces (CODESPACES.md)."
}

# ce_podman_machine_start — Podman is installed but not answering: start an existing,
# stopped Podman machine (macOS/Windows). Returns 0 once `podman info` works, 1 otherwise.
# Never creates a machine. Silent when there is none (Linux native podman, or not created yet).
ce_podman_machine_start() {
  local list line name running chosen="" chosen_running="" first="" first_running="" out status
  list="$(podman machine list --format '{{.Name}} {{.Running}}' 2>/dev/null | tr -d '\r' || true)"
  while read -r name running; do
    [ -n "$name" ] || continue
    if [ -z "$first" ]; then
      first="$name"
      first_running="$running"
    fi
    case "$name" in
      *'*')
        chosen="${name%\*}"
        chosen_running="$running"
        break
        ;;
    esac
  done <<EOF
$list
EOF
  if [ -z "$chosen" ]; then
    chosen="${first%\*}"
    chosen_running="$first_running"
  fi
  [ -n "$chosen" ] || return 1
  # Already running yet `podman info` failed: starting again will not help.
  [ "$chosen_running" = "true" ] && return 1

  echo "Starting podman machine '$chosen' (once per boot, can take a minute)..." >&2
  status=0
  # wsl.exe writes UTF-16, so the output carries NUL bytes; keep it in a file and strip them.
  local tmp
  tmp="$(mktemp)"
  podman machine start "$chosen" >"$tmp" 2>&1 || status=$?
  out="$(tr -d '\000\r' <"$tmp")"
  rm -f "$tmp"
  if [ "$status" -ne 0 ]; then
    local shown=0
    while IFS= read -r line; do
      line="$(printf '%s' "$line" | tr -d '\r')"
      [ -n "${line//[[:space:]]/}" ] || continue
      printf '  %s\n' "$line" >&2
      shown=$((shown + 1))
      [ "$shown" -lt 15 ] || break
    done <<EOF
$out
EOF
    return 1
  fi
  podman info >/dev/null 2>&1
}

# container_engine_hint <engine> — prints the install/start hint for that engine.
# Engine "podman-compose" hints at the missing compose provider.
container_engine_hint() {
  case "$1" in
    docker)
      if ce_desktop_os; then
        echo "Docker: install Docker Desktop, start it (the scripts never launch it) and wait until it says it is running, then rerun."
      else
        echo "Docker: install Docker Engine + the compose plugin; start the daemon and rerun."
      fi
      ;;
    podman)
      if ce_desktop_os; then
        echo "Podman: create a machine once with 'podman machine init --memory 8192' and 'podman machine start' (the scripts start an existing stopped machine themselves)."
      else
        echo "Podman: install podman plus podman-compose (or the docker-compose provider for 'podman compose')."
      fi
      ;;
    podman-compose)
      if ce_desktop_os; then
        echo "Podman compose: Podman Desktop > Settings > Resources > Compose > Setup, or: uv tool install podman-compose"
      else
        echo "Podman compose: install podman-compose (or the docker-compose provider for 'podman compose')."
      fi
      ;;
  esac
}

# container_engine_detect — pick the engine and compose command.
# Returns 0 when a usable engine + compose pair was found, 1 otherwise.
container_engine_detect() {
  local requested="${CONTAINER_ENGINE:-}"
  local candidates=()
  local engine

  CONTAINER_ENGINE=""
  # shellcheck disable=SC2034  # both are consumed by the scripts that source this file
  COMPOSE_CMD=()

  case "$requested" in
    "") candidates=(docker podman) ;;
    docker | podman) candidates=("$requested") ;;
    *)
      echo "CONTAINER_ENGINE must be 'docker' or 'podman' (got: '$requested')" >&2
      return 1
      ;;
  esac

  for engine in "${candidates[@]}"; do
    if ! ce_daemon_ready "$engine"; then
      # A stopped Podman machine (macOS/Windows) is started here, once per boot.
      if [ "$engine" = podman ] && ce_installed podman && ce_podman_machine_start; then
        :
      else
        continue
      fi
    fi
    if ! ce_compose_available "$engine"; then
      continue
    fi
    CONTAINER_ENGINE="$engine"
    export CONTAINER_ENGINE
    return 0
  done

  return 1
}

# container_image_reference <container> — the image reference the container was
# created from. Docker exposes it as .Config.Image; podman as .ImageName.
container_image_reference() {
  local container="$1"
  local out=""

  if [ -n "${CONTAINER_ENGINE:-}" ]; then
    case "$CONTAINER_ENGINE" in
      docker) out="$(docker inspect --format='{{.Config.Image}}' "$container" 2>/dev/null || true)" ;;
      podman) out="$(podman inspect --format='{{.ImageName}}' "$container" 2>/dev/null || true)" ;;
    esac
  fi
  if [ -z "$out" ]; then
    # Cross-engine fallback so a Docker-created container still reports under podman and vice versa.
    out="$(docker inspect --format='{{.Config.Image}}' "$container" 2>/dev/null || true)"
  fi
  if [ -z "$out" ]; then
    out="$(podman inspect --format='{{.ImageName}}' "$container" 2>/dev/null || true)"
  fi
  printf '%s' "$out"
}

# container_image_id <container> — the image ID the container runs.
container_image_id() {
  local container="$1"
  if [ -n "${CONTAINER_ENGINE:-}" ]; then
    "$CONTAINER_ENGINE" inspect --format='{{.Image}}' "$container" 2>/dev/null || true
  fi
}
