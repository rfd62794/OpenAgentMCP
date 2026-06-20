from typing import TypedDict

class TestFloor(TypedDict):
    passing: int
    failing: int
    skipped: int
    ok: bool

class AssessmentResult(TypedDict):
    repo_name: str
    phase_current: str
    what_is_built: str
    what_is_stubbed: list[str]
    test_floor: TestFloor
    open_questions: list[str]
    recent_decisions: list[str]
    files_in_scope: list[str]
    complexity_flags: list[str]
    doc_gaps: list[str]
