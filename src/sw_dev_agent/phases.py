"""
SW dev framework - Phase definitions.
Maps each phase of software development to an agent skill.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Phase(Enum):
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    RELEASE = "release"

    @classmethod
    def ordered(cls) -> list["Phase"]:
        return [
            cls.REQUIREMENTS,
            cls.DESIGN,
            cls.IMPLEMENT,
            cls.REVIEW,
            cls.RELEASE,
        ]

    def next(self) -> Optional["Phase"]:
        ordered = Phase.ordered()
        idx = ordered.index(self)
        if idx + 1 < len(ordered):
            return ordered[idx + 1]
        return None


class PhaseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class PhaseResult:
    phase: Phase
    status: PhaseStatus
    output: str = field(default="")

    def is_done(self) -> bool:
        return self.status == PhaseStatus.DONE
