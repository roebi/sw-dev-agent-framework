#!/usr/bin/env bash
# Build the container image. Reentrant: re-running rebuilds and re-tags the
# same image names; nothing has to be cleaned up first.
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="${IMAGE:-localhost/sw-dev-agent-framework}"
VERSION="$(sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml | head -n1)"
SKILLS_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

podman build \
  --format docker \
  --build-arg "SKILLS_COMMIT=${SKILLS_COMMIT}" \
  --tag "${IMAGE}:${VERSION}" \
  --tag "${IMAGE}:latest" \
  --file Dockerfile \
  .

echo "Built ${IMAGE}:${VERSION} (skills commit ${SKILLS_COMMIT})"
