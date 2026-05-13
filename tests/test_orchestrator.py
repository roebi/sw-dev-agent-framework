"""
TDD - RED phase tests for SW dev Orchestrator.
"""
from sw_dev_agent.phases import Phase, PhaseStatus, PhaseResult
from sw_dev_agent.orchestrator import Orchestrator, HandoverState


class TestHandoverState:
    def test_handover_state_starts_at_requirements(self):
        state = HandoverState(goal="Build a REST API in Python")
        assert state.current_phase == Phase.REQUIREMENTS

    def test_handover_state_stores_goal(self):
        state = HandoverState(goal="Build a CLI tool")
        assert state.goal == "Build a CLI tool"

    def test_handover_state_has_empty_results_initially(self):
        state = HandoverState(goal="Build something")
        assert state.results == []

    def test_handover_state_is_complete_when_all_phases_done(self):
        state = HandoverState(goal="Build something")
        for phase in Phase.ordered():
            state.results.append(
                PhaseResult(phase=phase, status=PhaseStatus.DONE)
            )
        assert state.is_complete() is True

    def test_handover_state_is_not_complete_with_missing_phases(self):
        state = HandoverState(goal="Build something")
        state.results.append(
            PhaseResult(phase=Phase.REQUIREMENTS, status=PhaseStatus.DONE)
        )
        assert state.is_complete() is False

    def test_handover_state_serializes_to_yaml(self):
        state = HandoverState(goal="Build a CLI")
        yaml_str = state.to_yaml()
        assert "goal: Build a CLI" in yaml_str
        assert "current_phase: requirements" in yaml_str

    def test_handover_state_deserializes_from_yaml(self):
        yaml_str = "goal: Build a CLI\ncurrent_phase: requirements\nresults: []\n"
        state = HandoverState.from_yaml(yaml_str)
        assert state.goal == "Build a CLI"
        assert state.current_phase == Phase.REQUIREMENTS


class TestOrchestrator:
    def test_orchestrator_accepts_a_goal(self):
        orch = Orchestrator(goal="Build a login module")
        assert orch.goal == "Build a login module"

    def test_orchestrator_creates_initial_handover_state(self):
        orch = Orchestrator(goal="Build something")
        assert isinstance(orch.state, HandoverState)
        assert orch.state.current_phase == Phase.REQUIREMENTS

    def test_orchestrator_advance_moves_to_next_phase(self):
        orch = Orchestrator(goal="Build something")
        result = PhaseResult(phase=Phase.REQUIREMENTS, status=PhaseStatus.DONE)
        orch.advance(result)
        assert orch.state.current_phase == Phase.DESIGN

    def test_orchestrator_advance_records_result(self):
        orch = Orchestrator(goal="Build something")
        result = PhaseResult(phase=Phase.REQUIREMENTS, status=PhaseStatus.DONE)
        orch.advance(result)
        assert len(orch.state.results) == 1
        assert orch.state.results[0].phase == Phase.REQUIREMENTS

    def test_orchestrator_is_done_when_all_phases_complete(self):
        orch = Orchestrator(goal="Build something")
        for phase in Phase.ordered():
            result = PhaseResult(phase=phase, status=PhaseStatus.DONE)
            orch.advance(result)
        assert orch.is_done() is True

    def test_orchestrator_is_not_done_initially(self):
        orch = Orchestrator(goal="Build something")
        assert orch.is_done() is False

    def test_orchestrator_returns_active_skill_name_per_phase(self):
        orch = Orchestrator(goal="Build something")
        assert orch.active_skill() == "gather-requirements-en"
        orch.advance(PhaseResult(phase=Phase.REQUIREMENTS, status=PhaseStatus.DONE))
        assert orch.active_skill() == "design-architecture-en"
        orch.advance(PhaseResult(phase=Phase.DESIGN, status=PhaseStatus.DONE))
        assert orch.active_skill() == "apply-tdd-loop-en"
        orch.advance(PhaseResult(phase=Phase.IMPLEMENT, status=PhaseStatus.DONE))
        assert orch.active_skill() == "code-review-en"
        orch.advance(PhaseResult(phase=Phase.REVIEW, status=PhaseStatus.DONE))
        assert orch.active_skill() == "release-sw-project-en"

    def test_orchestrator_active_skill_returns_none_when_done(self):
        orch = Orchestrator(goal="Build something")
        for phase in Phase.ordered():
            orch.advance(PhaseResult(phase=phase, status=PhaseStatus.DONE))
        assert orch.active_skill() is None
