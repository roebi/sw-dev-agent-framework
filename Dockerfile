# sw-dev-agent-framework - container run mode (R-CTR-001..005)
# Build with ./podman_build.sh, run with ./podman_run.sh [serve|mcp]

FROM docker.io/library/python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv
WORKDIR /src
COPY pyproject.toml uv.lock README.md CHANGELOG.md hatch_build.py ./
COPY src ./src
COPY skills ./skills
# No .git in the build context: the skills commit is passed in.
ARG SKILLS_COMMIT=unknown
RUN SKILLS_COMMIT="${SKILLS_COMMIT}" uv build --wheel --out-dir /dist

FROM docker.io/library/python:3.14-slim
LABEL org.opencontainers.image.title="sw-dev-agent-framework" \
      org.opencontainers.image.source="https://github.com/roebi/sw-dev-agent-framework" \
      org.opencontainers.image.licenses="MIT AND CC-BY-NC-SA-4.0"
COPY --from=build /dist /dist
# Debian security updates newer than the base image (Trivy: zlib1g CVE-2026-85091).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
# pip is only needed for this install. It vendors pkg_resources from
# setuptools 70.3.0 (Trivy: CVE-2025-47273), so it is removed afterwards.
RUN WHEEL="$(ls /dist/*.whl)" \
    && pip install --no-cache-dir "${WHEEL}[mcp]" \
    && rm -rf /dist \
    && python -m pip uninstall -y pip \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh
USER 10001
ENV SW_DEV_AGENT_PORT=8765 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/usr/local/bin/entrypoint.sh", "healthcheck"]
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["serve"]
