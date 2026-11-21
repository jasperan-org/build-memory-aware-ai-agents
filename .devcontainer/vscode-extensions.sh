#!/usr/bin/env bash
# Installs the Python and Jupyter extensions into the Codespace's VS Code server during
# provisioning. Codespaces installs the devcontainer.json extensions only once a browser or
# desktop client connects, so without this a notebook can open before Jupyter is there and
# the kernel picker is empty. Outside Codespaces (no server under /vscode) it does nothing.
set -uo pipefail

# Codespaces hosts keep the server under /vscode/bin/linux-x64/<commit> or /vscode/serverCache/<commit>.
server="$(ls -td /vscode/bin/linux-x64/*/bin/code-server /vscode/serverCache/*/bin/code-server 2>/dev/null | head -1)"
if [ -z "$server" ]; then
  echo "VS Code server not found; the notebook extensions install when VS Code connects."
  exit 0
fi

for ext in ms-python.python ms-toolsai.jupyter; do
  if ls "$HOME/.vscode-remote/extensions" 2>/dev/null | grep -q "^${ext}-[0-9]"; then
    echo "✓ VS Code extension $ext already installed"
  elif "$server" --server-data-dir "$HOME/.vscode-remote" --install-extension "$ext" >/tmp/vscode-ext-install.log 2>&1; then
    echo "✓ VS Code extension $ext installed"
  else
    echo "⚠ VS Code extension $ext did not install now; VS Code installs it when it connects:"
    tail -3 /tmp/vscode-ext-install.log
  fi
done
exit 0
