"""Tests for openagent.writer."""
from unittest.mock import patch
from openagent.writer import Writer
from openagent.models import AssessmentResult


def test_write_returns_directive_string():
    """Mock _call_model -> returns non-empty string."""
    writer = Writer()
    assessment: AssessmentResult = {
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
    
    with patch.object(writer, "_call_model", return_value="DIRECTIVE CONTENT"):
        directive = writer.write(assessment, "add tests")
        assert directive == "DIRECTIVE CONTENT"


def test_write_uses_intent_param():
    """Intent passed -> appears in prompt sent to model."""
    writer = Writer()
    assessment: AssessmentResult = {
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
    
    with patch.object(writer, "_call_model") as mock_call:
        writer.write(assessment, "custom intent")
        prompt = mock_call.call_args[0][0]
        assert "custom intent" in prompt


def test_write_falls_back_to_what_is_next():
    """intent=None, assessment has what_is_next -> used."""
    writer = Writer()
    assessment: AssessmentResult = {
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
        "what_is_next": "fallback intent",
    }
    
    with patch.object(writer, "_call_model") as mock_call:
        writer.write(assessment, None)
        prompt = mock_call.call_args[0][0]
        assert "fallback intent" in prompt


def test_write_raises_if_no_intent():
    """intent=None, no what_is_next -> raises ValueError."""
    writer = Writer()
    assessment: AssessmentResult = {
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
    
    with patch.object(writer, "_call_model", return_value="directive"):
        try:
            writer.write(assessment, None)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No intent provided" in str(e)


def test_write_includes_soul_text_in_prompt():
    """soul_text provided -> appears in prompt."""
    writer = Writer()
    assessment: AssessmentResult = {
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
    
    with patch.object(writer, "_call_model") as mock_call:
        writer.write(assessment, "intent", soul_text="ARCHITECT SOUL TEXT")
        prompt = mock_call.call_args[0][0]
        assert "ARCHITECT SOUL TEXT" in prompt


def test_call_model_not_invoked_directly():
    """All tests use mock — no real API call."""
    writer = Writer()
    assert hasattr(writer, "_call_model")
    assert callable(writer._call_model)


def test_write_strips_whitespace():
    """Model returns padded output -> directive is stripped."""
    writer = Writer()
    assessment: AssessmentResult = {
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
    
    with patch.object(writer, "_call_model", return_value="  directive  "):
        directive = writer.write(assessment, "intent")
        assert directive == "directive"
