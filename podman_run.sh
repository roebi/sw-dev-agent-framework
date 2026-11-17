#!/usr/bin/env bash
# Run the container. Reentrant: an existing container with the same name is
# replaced. Usage: ./podman_run.sh [serve|mcp]   (default: serve)
# The port is published on 127.0.0.1 of the host only.
set -euo pipefail

MODE="${1:-serve}"
IMAGE="${IMAGE:-localhost/sw-dev-agent-framework:latest}"
NAME="${NAME:-sw-dev-agent-${MODE}}"
PORT="${PORT:-8765}"

case "$MODE" in
  serve|mcp) ;;
  *) echo "Usage: $0 [serve|mcp]" >&2; exit 1 ;;
esac

podman rm --force --ignore "$NAME" >/dev/null

podman run --detach \
  --name "$NAME" \
  --publish "127.0.0.1:${PORT}:8765" \
  --read-only \
  --tmpfs /tmp:rw,size=1m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  "$IMAGE" "$MODE" >/dev/null

if [ "$MODE" = "mcp" ]; then
  echo "MCP server: http://127.0.0.1:${PORT}/sw-dev-agent-framework/mcp (container ${NAME})"
else
  echo "Skills API: http://127.0.0.1:${PORT}/skills/orchestrator (container ${NAME})"
fi
