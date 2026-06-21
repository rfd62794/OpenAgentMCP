"""
Tests for GitContextReader and Assessor git context integration.
All git subprocess calls mocked. No real git repo required.
No network. No API calls.
"""
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openagent.git_context import GitContextReader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_side_effect(*outputs):
    """Return a side_effect list of CompletedProcess mocks."""
    results = []
    for out in outputs:
        m = MagicMock()
        m.stdout = out
        results.append(m)
    return results


# ---------------------------------------------------------------------------
# GitContextReader tests
# ---------------------------------------------------------------------------

class TestGitContextReaderErrors:
    def test_returns_none_not_git_repo(self):
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")):
            result = GitContextReader().read("/some/path")
        assert result is None

    def test_returns_none_git_unavailable(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = GitContextReader().read("/some/path")
        assert result is None

    def test_returns_none_on_any_git_error(self):
        side_effects = _make_run_side_effect("main\n", "abc1234\n")
        side_effects.append(subprocess.CalledProcessError(1, "git log"))
        with patch("subprocess.run", side_effect=side_effects):
            result = GitContextReader().read("/some/path")
        assert result is None


class TestGitContextReaderFields:
    def _patch_run(self, branch="main", hash_="abc1234", msg="Fix bug", date="2026-06-21T00:00:00+00:00", status=""):
        outputs = [f"{branch}\n", f"{hash_}\n", f"{msg}\n", f"{date}\n", status]
        return _make_run_side_effect(*outputs)

    def test_active_branch(self):
        with patch("subprocess.run", side_effect=self._patch_run(branch="feature-x")):
            result = GitContextReader().read("/repo")
        assert result is not None
        assert result["active_branch"] == "feature-x"

    def test_last_commit_fields(self):
        with patch("subprocess.run", side_effect=self._patch_run(
            hash_="deadbee", msg="Add tests", date="2026-06-20T12:00:00+00:00"
        )):
            result = GitContextReader().read("/repo")
        assert result is not None
        assert result["last_commit_hash"] == "deadbee"
        assert result["last_commit_message"] == "Add tests"
        assert result["last_commit_date"] == "2026-06-20T12:00:00+00:00"

    def test_uncommitted_files_dirty(self):
        with patch("subprocess.run", side_effect=self._patch_run(status=" M file.py\n")):
            result = GitContextReader().read("/repo")
        assert result is not None
        assert result["uncommitted_files"] == ["file.py"]

    def test_uncommitted_files_clean(self):
        with patch("subprocess.run", side_effect=self._patch_run(status="")):
            result = GitContextReader().read("/repo")
        assert result is not None
        assert result["uncommitted_files"] == []


class TestGitContextReaderWorkflows:
    def test_workflows_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            wf_dir = Path(tmp) / ".windsurf" / "workflows"
            wf_dir.mkdir(parents=True)
            (wf_dir / "a.md").write_text("workflow a")
            (wf_dir / "b.md").write_text("workflow b")

            outputs = ["main\n", "abc1234\n", "init\n", "2026-06-21T00:00:00+00:00\n", ""]
            with patch("subprocess.run", side_effect=_make_run_side_effect(*outputs)):
                result = GitContextReader().read(tmp)

        assert result is not None
        assert sorted(result["workflows"]) == ["a.md", "b.md"]

    def test_workflows_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = ["main\n", "abc1234\n", "init\n", "2026-06-21T00:00:00+00:00\n", ""]
            with patch("subprocess.run", side_effect=_make_run_side_effect(*outputs)):
                result = GitContextReader().read(tmp)
        assert result is not None
        assert result["workflows"] == []


class TestGitContextReaderStatePhase:
    def test_state_phase_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "docs" / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "current.md").write_text("phase: 'Phase 5'\nother: value\n")

            outputs = ["main\n", "abc1234\n", "init\n", "2026-06-21T00:00:00+00:00\n", ""]
            with patch("subprocess.run", side_effect=_make_run_side_effect(*outputs)):
                result = GitContextReader().read(tmp)

        assert result is not None
        assert result["state_phase"] == "Phase 5"

    def test_state_phase_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = ["main\n", "abc1234\n", "init\n", "2026-06-21T00:00:00+00:00\n", ""]
            with patch("subprocess.run", side_effect=_make_run_side_effect(*outputs)):
                result = GitContextReader().read(tmp)
        assert result is not None
        assert result["state_phase"] is None


# ---------------------------------------------------------------------------
# Assessor git context integration tests
# ---------------------------------------------------------------------------

class TestAssessorGitContext:
    def _make_scan_result(self, repo_path="/repo"):
        return {
            "repo_path": repo_path,
            "file_tree": ["openagent/scanner.py"],
            "py_files": ["openagent/scanner.py"],
            "test_files": [],
            "config_files": [],
            "doc_files": [],
        }

    def _make_doc_result(self):
        return {"current_md": {
            "phase": "Phase 5",
            "what_is_built": "Scanner",
            "what_is_next": "GitContextReader",
            "test_floor": "258/0/0",
            "open_questions": "",
            "recent_decisions": "",
        }}

    def _make_git_ctx(self):
        return {
            "active_branch": "phase-6",
            "last_commit_hash": "abc1234",
            "last_commit_message": "Add git context",
            "last_commit_date": "2026-06-21T00:00:00+00:00",
            "uncommitted_files": [],
            "workflows": ["phase6.md"],
            "state_phase": "Phase 6",
        }

    def test_assessor_includes_git_context(self):
        from openagent.assessor import Assessor
        assessor = Assessor()
        git_ctx = self._make_git_ctx()

        with patch("openagent.assessor.GitContextReader") as MockGCR:
            MockGCR.return_value.read.return_value = git_ctx
            prompt = assessor._build_prompt(
                {**self._make_scan_result(), "git": git_ctx},
                self._make_doc_result(),
            )

        assert "phase-6" in prompt
        assert "abc1234" in prompt
        assert "phase6.md" in prompt

    def test_assessor_handles_null_git_context(self):
        from openagent.assessor import Assessor
        assessor = Assessor()

        with patch("openagent.assessor.GitContextReader") as MockGCR:
            MockGCR.return_value.read.return_value = None
            prompt = assessor._build_prompt(
                {**self._make_scan_result(), "git": None},
                self._make_doc_result(),
            )

        assert "Git State" not in prompt
        assert "Repository:" in prompt
