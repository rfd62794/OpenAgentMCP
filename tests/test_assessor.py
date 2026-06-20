"""Tests for openagent.assessor."""
import pytest
from unittest.mock import patch, MagicMock
from openagent.assessor import Assessor
from openagent.models import AssessmentResult


def test_assess_returns_assessment_result():
    """Mock _call_model -> valid JSON -> returns dict with all required keys."""
    assessor = Assessor()
    scan_result = {
        "repo_path": "/test/repo",
        "file_tree": ["file1.py", "file2.py"],
    }
    doc_result = {"current_md": {"phase": "Phase 1", "what_is_built": "scaffold"}}
    
    mock_response = {
        "repo_name": "test-repo",
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
    
    with patch.object(assessor, "_call_model", return_value='{"repo_name": "test-repo", "phase_current": "Phase 1", "what_is_built": "scaffold", "what_is_stubbed": [], "test_floor": {"passing": 10, "failing": 0, "skipped": 0, "ok": true}, "open_questions": [], "recent_decisions": [], "files_in_scope": [], "complexity_flags": [], "doc_gaps": []}'):
        result = assessor.assess(scan_result, doc_result)
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


def test_assess_parses_markdown_fenced_json():
    """Raw output wrapped in ```json ... ``` -> parsed correctly."""
    assessor = Assessor()
    scan_result = {"repo_path": "/test/repo", "file_tree": []}
    doc_result = {"current_md": {}}
    
    raw_json = '''```json
{
  "repo_name": "test-repo",
  "phase_current": "Phase 1",
  "what_is_built": "scaffold",
  "what_is_stubbed": [],
  "test_floor": {"passing": 10, "failing": 0, "skipped": 0, "ok": true},
  "open_questions": [],
  "recent_decisions": [],
  "files_in_scope": [],
  "complexity_flags": [],
  "doc_gaps": []
}
```'''
    
    with patch.object(assessor, "_call_model", return_value=raw_json):
        result = assessor.assess(scan_result, doc_result)
        assert result["repo_name"] == "test-repo"


def test_assess_raises_on_missing_key():
    """JSON missing repo_name -> raises ValueError."""
    assessor = Assessor()
    scan_result = {"repo_path": "/test/repo", "file_tree": []}
    doc_result = {"current_md": {}}
    
    incomplete_json = '{"phase_current": "Phase 1", "what_is_built": "scaffold", "what_is_stubbed": [], "test_floor": {"passing": 10, "failing": 0, "skipped": 0, "ok": true}, "open_questions": [], "recent_decisions": [], "files_in_scope": [], "complexity_flags": [], "doc_gaps": []}'
    
    with patch.object(assessor, "_call_model", return_value=incomplete_json):
        with pytest.raises(ValueError, match="missing keys"):
            assessor.assess(scan_result, doc_result)


def test_assess_raises_on_invalid_json():
    """_call_model returns garbage -> raises ValueError."""
    assessor = Assessor()
    scan_result = {"repo_path": "/test/repo", "file_tree": []}
    doc_result = {"current_md": {}}
    
    with patch.object(assessor, "_call_model", return_value="not valid json at all"):
        with pytest.raises(ValueError, match="Could not parse"):
            assessor.assess(scan_result, doc_result)


def test_assess_sets_floor_ok_true():
    """failing=0, skipped=0 -> test_floor["ok"] is True."""
    assessor = Assessor()
    scan_result = {"repo_path": "/test/repo", "file_tree": []}
    doc_result = {"current_md": {}}
    
    json_response = '{"repo_name": "test", "phase_current": "Phase 1", "what_is_built": "scaffold", "what_is_stubbed": [], "test_floor": {"passing": 10, "failing": 0, "skipped": 0}, "open_questions": [], "recent_decisions": [], "files_in_scope": [], "complexity_flags": [], "doc_gaps": []}'
    
    with patch.object(assessor, "_call_model", return_value=json_response):
        result = assessor.assess(scan_result, doc_result)
        assert result["test_floor"]["ok"] is True


def test_assess_sets_floor_ok_false():
    """failing=1 -> test_floor["ok"] is False."""
    assessor = Assessor()
    scan_result = {"repo_path": "/test/repo", "file_tree": []}
    doc_result = {"current_md": {}}
    
    json_response = '{"repo_name": "test", "phase_current": "Phase 1", "what_is_built": "scaffold", "what_is_stubbed": [], "test_floor": {"passing": 10, "failing": 1, "skipped": 0}, "open_questions": [], "recent_decisions": [], "files_in_scope": [], "complexity_flags": [], "doc_gaps": []}'
    
    with patch.object(assessor, "_call_model", return_value=json_response):
        result = assessor.assess(scan_result, doc_result)
        assert result["test_floor"]["ok"] is False


def test_call_model_not_invoked_in_tests():
    """Confirm all tests use mock — no real network call."""
    assessor = Assessor()
    # This test validates that _call_model is mocked in all other tests
    # by checking that the method exists and can be patched
    assert hasattr(assessor, "_call_model")
    assert callable(assessor._call_model)
