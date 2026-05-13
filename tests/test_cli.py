"""
TDD - tests for the Typer CLI entry point.
Uses typer.testing.CliRunner - no subprocess, no I/O side effects.
"""
from typer.testing import CliRunner
from sw_dev_agent.cli import app
from sw_dev_agent.phases import Phase

runner = CliRunner()


class TestStartCommand:
    def test_start_exits_zero(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["start", "Build a REST API"])
        assert result.exit_code == 0

    def test_start_prints_goal(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["start", "Build a REST API"])
        assert "Build a REST API" in result.output

    def test_start_prints_active_skill(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["start", "Build a REST API"])
        assert "gather-requirements-en" in result.output

    def test_start_writes_handover_state_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["start", "Build a CLI tool"])
        assert (tmp_path / "Handover-State.md").exists()

    def test_start_handover_state_contains_goal(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["start", "Build a CLI tool"])
        content = (tmp_path / "Handover-State.md").read_text()
        assert "Build a CLI tool" in content

    def test_start_handover_state_starts_at_requirements(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["start", "Build something"])
        content = (tmp_path / "Handover-State.md").read_text()
        assert "requirements" in content


class TestStatusCommand:
    def test_status_fails_without_handover_state(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1

    def test_status_shows_error_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["status"])
        assert "Handover-State.md" in result.output

    def test_status_shows_pipeline_after_start(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["start", "Build a parser"])
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Build a parser" in result.output

    def test_status_shows_active_skill(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["start", "Build a parser"])
        result = runner.invoke(app, ["status"])
        assert "gather-requirements-en" in result.output

    def test_status_shows_done_when_complete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Write a fully-complete handover state
        from sw_dev_agent.orchestrator import HandoverState
        from sw_dev_agent.phases import PhaseStatus, PhaseResult
        state = HandoverState(goal="Finished project")
        for phase in Phase.ordered():
            state.results.append(PhaseResult(phase=phase, status=PhaseStatus.DONE))
        state.current_phase = Phase.RELEASE
        (tmp_path / "Handover-State.md").write_text(state.to_yaml())
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower() or "released" in result.output.lower()


class TestPhasesCommand:
    def test_phases_exits_zero(self):
        result = runner.invoke(app, ["phases"])
        assert result.exit_code == 0

    def test_phases_lists_all_five_phases(self):
        result = runner.invoke(app, ["phases"])
        for phase in Phase.ordered():
            assert phase.value in result.output

    def test_phases_lists_all_skill_names(self):
        result = runner.invoke(app, ["phases"])
        for skill in [
            "gather-requirements-en",
            "design-architecture-en",
            "apply-tdd-loop-en",
            "code-review-en",
            "release-sw-project-en",
        ]:
            assert skill in result.output
