"""TDD - OpenAPI HTTP API (R-API-001..010, R-CI-002, NFR-05)."""
import json
from pathlib import Path

import pytest

from sw_dev_agent.api import SPEC_PATH, BuildInfo, create_app, implemented_operations
from sw_dev_agent.catalog import ORCHESTRATOR, SkillCatalog

INFO = BuildInfo(package_version="9.9.9", skills_commit="abc123")


def write_skill(root: Path, name: str, body: str) -> None:
    (root / name).mkdir()
    (root / name / "SKILL.md").write_bytes(
        f"---\nname: {name}\ndescription: Desc of {name}.\n---\n{body}".encode()
    )


@pytest.fixture
def root(tmp_path):
    write_skill(tmp_path, ORCHESTRATOR, "# Orchestrator\n")
    write_skill(tmp_path, "gather-requirements-en", "# Gather ä\n")
    return tmp_path


@pytest.fixture
def client(root):
    app = create_app(SkillCatalog(root), INFO)
    with app.test_client() as c:
        yield c


class TestSpec:
    def test_spec_file_is_valid_openapi(self):
        from openapi_spec_validator import validate
        validate(json.loads(SPEC_PATH.read_text()))

    def test_every_spec_operation_is_implemented_and_vice_versa(self):
        spec = json.loads(SPEC_PATH.read_text())
        op_ids = {
            op["operationId"].rsplit(".", 1)[-1]
            for path in spec["paths"].values() for op in path.values()
        }
        assert op_ids == implemented_operations()

    def test_spec_version_matches_package(self):
        import tomllib
        spec = json.loads(SPEC_PATH.read_text())
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        assert spec["info"]["version"] == tomllib.loads(pyproject.read_text())["project"]["version"]

    def test_serves_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        assert set(r.json()["paths"]) == set(json.loads(SPEC_PATH.read_text())["paths"])


class TestHealthAndVersion:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_version(self, client):
        r = client.get("/version")
        assert r.status_code == 200
        assert r.json() == {"package_version": "9.9.9", "skills_commit": "abc123"}


class TestSkills:
    def test_list(self, client):
        r = client.get("/skills")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        assert r.json() == {"skills": [
            {"name": "gather-requirements-en", "description": "Desc of gather-requirements-en.",
             "path": "/skills/gather-requirements-en"},
            {"name": ORCHESTRATOR, "description": f"Desc of {ORCHESTRATOR}.",
             "path": f"/skills/{ORCHESTRATOR}"},
        ]}

    def test_orchestrator_returns_markdown_unchanged(self, client, root):
        r = client.get("/skills/orchestrator")
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/markdown; charset=utf-8"
        assert r.content == (root / ORCHESTRATOR / "SKILL.md").read_bytes()

    def test_skill_by_name_returns_markdown_unchanged(self, client, root):
        r = client.get("/skills/gather-requirements-en")
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/markdown; charset=utf-8"
        assert r.content == (root / "gather-requirements-en" / "SKILL.md").read_bytes()

    def test_unknown_skill_is_404_problem(self, client):
        r = client.get("/skills/missing-skill")
        assert r.status_code == 404
        assert r.headers["content-type"].startswith("application/problem+json")
        assert r.json()["status"] == 404

    @pytest.mark.parametrize("name", ["Upper", "double--dash", "a" * 65, "dot.md"])
    def test_invalid_name_is_400_problem(self, client, name):
        r = client.get(f"/skills/{name}")
        assert r.status_code == 400
        assert r.headers["content-type"].startswith("application/problem+json")

    @pytest.mark.parametrize("path", ["/skills/..%2F..%2Fetc%2Fpasswd", "/skills/../pyproject.toml"])
    def test_traversal_never_succeeds(self, client, path):
        r = client.get(path)
        assert r.status_code in (400, 404)
        assert "[project]" not in r.text


class TestRobustness:
    def test_unknown_route_is_404(self, client):
        assert client.get("/nope").status_code == 404

    def test_write_methods_not_allowed(self, client):
        assert client.post("/skills").status_code == 405
        assert client.delete("/skills/gather-requirements-en").status_code == 405

    def test_handler_error_returns_500_without_traceback(self, tmp_path):
        class Broken(SkillCatalog):
            def list(self):
                raise RuntimeError("secret internal detail")

        app = create_app(Broken(tmp_path), INFO)
        with app.test_client() as c:
            r = c.get("/skills")
        assert r.status_code == 500
        assert "secret internal detail" not in r.text
        assert "Traceback" not in r.text
