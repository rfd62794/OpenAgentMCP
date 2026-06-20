"""Tests for openagent.cli."""
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from openagent.cli import cli
from openagent.models import AssessmentResult


def test_analyze_exits_0_on_success():
    """Mock Scanner, Assessor, Writer, StateWriter -> exit code 0."""
    runner = CliRunner()
    
    mock_scan_result = {
        "repo_path": "/test/repo",
        "file_tree": ["file1.py"],
        "py_files": ["file1.py"],
        "test_files": [],
        "config_files": [],
        "doc_files": [],
    }
    
    mock_assessment: AssessmentResult = {
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
        "what_is_next": "next phase",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("openagent.cli.Scanner") as mock_scanner, \
             patch("openagent.cli.Assessor") as mock_assessor, \
             patch("openagent.cli.Writer") as mock_writer, \
             patch("openagent.cli.StateWriter") as mock_state_writer, \
             patch("openagent.cli._read_soul", return_value=""), \
             patch("openagent.cli._read_current_md", return_value={"current_md": {}}):
            
            mock_scanner.return_value.scan.return_value = mock_scan_result
            mock_assessor.return_value.assess.return_value = mock_assessment
            mock_writer.return_value.write.return_value = "DIRECTIVE CONTENT"
            mock_state_writer.return_value.write.return_value = Path(tmpdir) / "docs" / "state" / "current.md"
            
            result = runner.invoke(cli, ["analyze", tmpdir])
            assert result.exit_code == 0


def test_analyze_prints_directive():
    """Directive string appears in CLI output."""
    runner = CliRunner()
    
    mock_scan_result = {
        "repo_path": "/test/repo",
        "file_tree": ["file1.py"],
        "py_files": ["file1.py"],
        "test_files": [],
        "config_files": [],
        "doc_files": [],
    }
    
    mock_assessment: AssessmentResult = {
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
        "what_is_next": "next phase",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("openagent.cli.Scanner") as mock_scanner, \
             patch("openagent.cli.Assessor") as mock_assessor, \
             patch("openagent.cli.Writer") as mock_writer, \
             patch("openagent.cli.StateWriter") as mock_state_writer, \
             patch("openagent.cli._read_soul", return_value=""), \
             patch("openagent.cli._read_current_md", return_value={"current_md": {}}):
            
            mock_scanner.return_value.scan.return_value = mock_scan_result
            mock_assessor.return_value.assess.return_value = mock_assessment
            mock_writer.return_value.write.return_value = "DIRECTIVE CONTENT"
            mock_state_writer.return_value.write.return_value = Path(tmpdir) / "docs" / "state" / "current.md"
            
            result = runner.invoke(cli, ["analyze", tmpdir])
            assert "DIRECTIVE CONTENT" in result.output


def test_analyze_exits_1_on_floor_failure():
    """Floor failing=1 -> exit code 1."""
    runner = CliRunner()
    
    mock_scan_result = {
        "repo_path": "/test/repo",
        "file_tree": ["file1.py"],
        "py_files": ["file1.py"],
        "test_files": [],
        "config_files": [],
        "doc_files": [],
    }
    
    mock_assessment: AssessmentResult = {
        "repo_name": "test",
        "phase_current": "Phase 1",
        "what_is_built": "scaffold",
        "what_is_stubbed": [],
        "test_floor": {"passing": 10, "failing": 1, "skipped": 0, "ok": False},
        "open_questions": [],
        "recent_decisions": [],
        "files_in_scope": [],
        "complexity_flags": [],
        "doc_gaps": [],
        "what_is_next": "next phase",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("openagent.cli.Scanner") as mock_scanner, \
             patch("openagent.cli.Assessor") as mock_assessor, \
             patch("openagent.cli._read_soul", return_value=""), \
             patch("openagent.cli._read_current_md", return_value={"current_md": {}}):
            
            mock_scanner.return_value.scan.return_value = mock_scan_result
            mock_assessor.return_value.assess.return_value = mock_assessment
            
            result = runner.invoke(cli, ["analyze", tmpdir])
            assert result.exit_code == 1


def test_analyze_accepts_path_arg():
    """Path argument passed through to Scanner."""
    runner = CliRunner()
    
    mock_scan_result = {
        "repo_path": "/test/repo",
        "file_tree": ["file1.py"],
        "py_files": ["file1.py"],
        "test_files": [],
        "config_files": [],
        "doc_files": [],
    }
    
    mock_assessment: AssessmentResult = {
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
        "what_is_next": "next phase",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("openagent.cli.Scanner") as mock_scanner, \
             patch("openagent.cli.Assessor") as mock_assessor, \
             patch("openagent.cli.Writer") as mock_writer, \
             patch("openagent.cli.StateWriter") as mock_state_writer, \
             patch("openagent.cli._read_soul", return_value=""), \
             patch("openagent.cli._read_current_md", return_value={"current_md": {}}):
            
            mock_scanner.return_value.scan.return_value = mock_scan_result
            mock_assessor.return_value.assess.return_value = mock_assessment
            mock_writer.return_value.write.return_value = "DIRECTIVE"
            mock_state_writer.return_value.write.return_value = Path(tmpdir) / "docs" / "state" / "current.md"
            
            result = runner.invoke(cli, ["analyze", tmpdir])
            mock_scanner.return_value.scan.assert_called_once()
