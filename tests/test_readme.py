"""G-10: README Skills chapter lists the orchestrator first, then the
phase skills in the order defined by the orchestrator."""
import re
from pathlib import Path

from sw_dev_agent.catalog import ORCHESTRATOR
from sw_dev_agent.orchestrator import PHASE_SKILL_MAP
from sw_dev_agent.phases import Phase

README = Path(__file__).resolve().parent.parent / "README.md"


def test_skills_table_order():
    text = README.read_text(encoding="utf-8")
    chapter = text.split("## Skills", 1)[1].split("\n## ", 1)[0]
    listed = re.findall(r"^\|[^|]*\|\s*`([a-z0-9-]+)`", chapter, re.MULTILINE)
    expected = [ORCHESTRATOR] + [PHASE_SKILL_MAP[p] for p in Phase.ordered()]
    assert listed == expected
