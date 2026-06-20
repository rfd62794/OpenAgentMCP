"""Tests for openagent.state_writer."""
import tempfile
from pathlib import Path
from openagent.state_writer import StateWriter
from openagent.models import AssessmentResult


def test_write_creates_current_md():
    """Writes to docs/state/current.md in tmp repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "intent", "directive")
        assert path.exists()
        assert path.name == "current.md"


def test_write_returns_path():
    """Returns Path pointing to current.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "intent", "directive")
        assert isinstance(path, Path)
        assert "current.md" in str(path)


def test_write_atomic():
    """tmp file cleaned up after write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "intent", "directive")
        tmp_path = path.parent / "current.tmp"
        assert not tmp_path.exists()


def test_content_includes_phase():
    """assessment phase_current appears in file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "intent", "directive")
        content = path.read_text(encoding="utf-8")
        assert "Phase 1" in content


def test_content_includes_agent_name():
    """"OpenAgentMCP v0.3" in written content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "intent", "directive")
        content = path.read_text(encoding="utf-8")
        assert "OpenAgentMCP v0.3" in content


def test_content_includes_intent():
    """intent string appears in what_is_next field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = StateWriter()
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
        path = writer.write(tmpdir, assessment, "custom intent", "directive")
        content = path.read_text(encoding="utf-8")
        assert "custom intent" in content
