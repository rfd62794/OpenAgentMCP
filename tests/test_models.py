"""Tests for openagent.models TypedDict structures."""
from openagent.models import AssessmentResult, TestFloor


def test_assessment_result_structure():
    """TypedDict has all required keys."""
    result: AssessmentResult = {
        "repo_name": "test",
        "phase_current": "Phase 1",
        "what_is_built": "scaffold",
        "what_is_stubbed": [],
        "test_floor": {"passing": 10, "failing": 0, "skipped": 0, "ok": True},
        "open_questions": [],
        "recent_decisions": [],
        "files_in_scope": [],
        "complexity_flags": [],
        "doc_gaps": [],
    }
    assert "repo_name" in result
    assert "phase_current" in result
    assert "what_is_built" in result
    assert "what_is_stubbed" in result
    assert "test_floor" in result
    assert "open_questions" in result
    assert "recent_decisions" in result
    assert "files_in_scope" in result
    assert "complexity_flags" in result
    assert "doc_gaps" in result


def test_test_floor_structure():
    """TestFloor has passing/failing/skipped/ok."""
    floor: TestFloor = {"passing": 10, "failing": 0, "skipped": 0, "ok": True}
    assert "passing" in floor
    assert "failing" in floor
    assert "skipped" in floor
    assert "ok" in floor
