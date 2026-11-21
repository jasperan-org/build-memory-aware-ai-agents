#!/usr/bin/env bash
# The docker-in-docker daemon starts with the container; lifecycle scripts can run before it is up.
for _ in $(seq 1 60); do
  docker info >/dev/null 2>&1 && exit 0
  sleep 2
done
echo "Docker daemon did not start within 2 minutes; rebuild the Codespace or run: sudo service docker start" >&2
exit 1
