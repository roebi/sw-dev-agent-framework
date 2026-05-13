"""
TDD - RED phase tests for SW dev framework phases.
All tests must fail before production code is written.
"""
from sw_dev_agent.phases import Phase, PhaseStatus, PhaseResult


class TestPhaseEnum:
    def test_all_sw_dev_phases_exist(self):
        phases = [p.value for p in Phase]
        assert "requirements" in phases
        assert "design" in phases
        assert "implement" in phases
        assert "review" in phases
        assert "release" in phases

    def test_phases_have_defined_order(self):
        ordered = Phase.ordered()
        assert ordered[0] == Phase.REQUIREMENTS
        assert ordered[-1] == Phase.RELEASE

    def test_each_phase_has_a_next_phase(self):
        assert Phase.REQUIREMENTS.next() == Phase.DESIGN
        assert Phase.DESIGN.next() == Phase.IMPLEMENT
        assert Phase.IMPLEMENT.next() == Phase.REVIEW
        assert Phase.REVIEW.next() == Phase.RELEASE

    def test_release_has_no_next_phase(self):
        assert Phase.RELEASE.next() is None


class TestPhaseStatus:
    def test_status_values(self):
        assert PhaseStatus.PENDING.value == "pending"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.DONE.value == "done"
        assert PhaseStatus.BLOCKED.value == "blocked"


class TestPhaseResult:
    def test_phase_result_stores_phase_and_status(self):
        result = PhaseResult(phase=Phase.REQUIREMENTS, status=PhaseStatus.DONE)
        assert result.phase == Phase.REQUIREMENTS
        assert result.status == PhaseStatus.DONE

    def test_phase_result_has_empty_output_by_default(self):
        result = PhaseResult(phase=Phase.DESIGN, status=PhaseStatus.PENDING)
        assert result.output == ""

    def test_phase_result_stores_output(self):
        result = PhaseResult(
            phase=Phase.IMPLEMENT,
            status=PhaseStatus.DONE,
            output="feat: implemented login module"
        )
        assert result.output == "feat: implemented login module"

    def test_phase_result_is_done_returns_true_when_done(self):
        result = PhaseResult(phase=Phase.REVIEW, status=PhaseStatus.DONE)
        assert result.is_done() is True

    def test_phase_result_is_done_returns_false_when_pending(self):
        result = PhaseResult(phase=Phase.REVIEW, status=PhaseStatus.PENDING)
        assert result.is_done() is False
