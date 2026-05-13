"""
SW dev framework - Orchestrator.
Coordinates the full software development lifecycle via phases and skills.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import yaml

from sw_dev_agent.phases import Phase, PhaseStatus, PhaseResult

# Maps each phase to the skill that handles it
PHASE_SKILL_MAP: dict[Phase, str] = {
    Phase.REQUIREMENTS: "gather-requirements-en",
    Phase.DESIGN: "design-architecture-en",
    Phase.IMPLEMENT: "apply-tdd-loop-en",
    Phase.REVIEW: "code-review-en",
    Phase.RELEASE: "release-sw-project-en",
}


@dataclass
class HandoverState:
    goal: str
    current_phase: Phase = field(default_factory=lambda: Phase.REQUIREMENTS)
    results: list[PhaseResult] = field(default_factory=list)

    def is_complete(self) -> bool:
        done_phases = {r.phase for r in self.results if r.is_done()}
        return all(p in done_phases for p in Phase.ordered())

    def to_yaml(self) -> str:
        data = {
            "goal": self.goal,
            "current_phase": self.current_phase.value,
            "results": [
                {"phase": r.phase.value, "status": r.status.value, "output": r.output}
                for r in self.results
            ],
        }
        return yaml.dump(data, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "HandoverState":
        data = yaml.safe_load(yaml_str)
        state = cls(goal=data["goal"])
        state.current_phase = Phase(data["current_phase"])
        state.results = [
            PhaseResult(
                phase=Phase(r["phase"]),
                status=PhaseStatus(r["status"]),
                output=r.get("output", ""),
            )
            for r in (data.get("results") or [])
        ]
        return state


class Orchestrator:
    def __init__(self, goal: str) -> None:
        self.goal = goal
        self.state = HandoverState(goal=goal)

    def advance(self, result: PhaseResult) -> None:
        self.state.results.append(result)
        next_phase = self.state.current_phase.next()
        if next_phase is not None:
            self.state.current_phase = next_phase

    def is_done(self) -> bool:
        return self.state.is_complete()

    def active_skill(self) -> Optional[str]:
        if self.is_done():
            return None
        return PHASE_SKILL_MAP.get(self.state.current_phase)
