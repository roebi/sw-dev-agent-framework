"""
OpenAPI HTTP API - Connexion v3 app built from the bundled openapi.json.

Each operationId `sw_dev_agent.api.handlers.<op>` is resolved to the method
`<op>` of a SkillHandlers instance, so the catalog is injected instead of
being global state.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import connexion
from connexion.lifecycle import ConnexionResponse
from connexion.middleware import MiddlewarePosition
from connexion.problem import problem
from connexion.resolver import Resolver

from sw_dev_agent import build_info
from sw_dev_agent.catalog import InvalidSkillName, SkillCatalog, SkillNotFound

SPEC_PATH = Path(__file__).resolve().parent / "openapi.json"
OPERATION_PREFIX = "sw_dev_agent.api.handlers."
MARKDOWN = "text/markdown"


@dataclass(frozen=True)
class BuildInfo:
    package_version: str
    skills_commit: str

    @classmethod
    def current(cls) -> BuildInfo:
        return cls(build_info.package_version(), build_info.skills_commit())


class SkillHandlers:
    def __init__(self, catalog: SkillCatalog, info: BuildInfo) -> None:
        self.catalog = catalog
        self.info = info

    def get_health(self) -> dict[str, str]:
        return {"status": "ok"}

    def get_version(self) -> dict[str, str]:
        return {
            "package_version": self.info.package_version,
            "skills_commit": self.info.skills_commit,
        }

    def list_skills(self) -> dict[str, Any]:
        return {
            "skills": [
                {"name": s.name, "description": s.description, "path": s.path}
                for s in self.catalog.list()
            ]
        }

    def get_orchestrator_skill(self) -> ConnexionResponse:
        return _markdown(self.catalog.get_orchestrator())

    def get_skill(self, name: str) -> Any:
        try:
            return _markdown(self.catalog.get(name))
        except InvalidSkillName:
            return problem(400, "Bad Request", "Invalid skill name.")
        except SkillNotFound:
            return problem(404, "Not Found", f"No skill named '{name}' is bundled.")


def _markdown(text: str) -> ConnexionResponse:
    return ConnexionResponse(status_code=200, content_type=MARKDOWN, body=text)


def implemented_operations() -> set[str]:
    return {
        name for name in vars(SkillHandlers)
        if not name.startswith("_") and callable(getattr(SkillHandlers, name))
    }


def _resolver(handlers: SkillHandlers) -> Resolver:
    def resolve(operation_id: str):
        if not operation_id.startswith(OPERATION_PREFIX):
            raise ValueError(f"Unexpected operationId: {operation_id}")
        name = operation_id[len(OPERATION_PREFIX):]
        if name not in implemented_operations():
            raise ValueError(f"Operation not implemented: {name}")
        return getattr(handlers, name)

    return Resolver(function_resolver=resolve)


SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
    (b"cache-control", b"no-store"),
]


class ResponseHeadersMiddleware:
    """Adds security headers and '; charset=utf-8' to text/markdown responses.

    Runs outside Connexion's response validation, which compares the bare
    media type with the spec.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                names = {name for name, _ in SECURITY_HEADERS}
                headers = [
                    (k, b"text/markdown; charset=utf-8")
                    if k.lower() == b"content-type" and v == MARKDOWN.encode()
                    else (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower() not in names
                ]
                message["headers"] = headers + SECURITY_HEADERS
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app(catalog: SkillCatalog, info: BuildInfo) -> connexion.AsyncApp:
    app = connexion.AsyncApp(__name__)
    app.add_api(
        SPEC_PATH,
        resolver=_resolver(SkillHandlers(catalog, info)),
        validate_responses=True,
        strict_validation=True,
        swagger_ui_options=connexion.options.SwaggerUIOptions(swagger_ui=False),
    )
    app.add_middleware(ResponseHeadersMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION)
    return app
