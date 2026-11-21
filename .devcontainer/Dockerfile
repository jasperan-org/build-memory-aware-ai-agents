FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The base image ships a Yarn apt source whose signing key is no longer published
# (NO_PUBKEY 62D54FD4003F6525). Features run `apt-get update` on top of this image, so the
# Docker-in-Docker feature fails and Codespaces falls back to a recovery container.
# The workshop needs no Yarn.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# System-wide uv: on PATH for every shell, including non-interactive `gh codespace ssh -- ...`.
RUN pip install --no-cache-dir uv
