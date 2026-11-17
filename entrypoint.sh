#!/bin/sh
# Container entrypoint: serve (default) | mcp | healthcheck | any command.
set -eu

PORT="${SW_DEV_AGENT_PORT:-8765}"
MODE_FILE=/tmp/sw-dev-agent-mode

case "${1:-serve}" in
  serve)
    echo serve > "$MODE_FILE"
    exec sw-dev-agent serve --host 0.0.0.0 --port "$PORT"
    ;;
  mcp)
    echo mcp > "$MODE_FILE"
    exec sw-dev-agent mcp --host 0.0.0.0 --port "$PORT"
    ;;
  healthcheck)
    # serve mode: GET /health must return {"status": "ok"}.
    # mcp mode has no /health route: the port must accept connections.
    exec python - "$PORT" "$(cat "$MODE_FILE" 2>/dev/null || echo serve)" <<'PY'
import json, socket, sys, urllib.request
port, mode = int(sys.argv[1]), sys.argv[2]
if mode == "mcp":
    socket.create_connection(("127.0.0.1", port), timeout=3).close()
else:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as r:  # nosec B310
        assert json.load(r) == {"status": "ok"}
PY
    ;;
  *)
    exec "$@"
    ;;
esac
