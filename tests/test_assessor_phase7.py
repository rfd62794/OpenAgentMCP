"""
Phase 7 Assessor tests — test_cmd context in prompt.
"""
from __future__ import annotations
from unittest.mock import patch

from openagent.assessor import Assessor


def _make_scan_result(repo_path="/repo"):
    return {
        "repo_path": repo_path,
        "file_tree": ["openagent/scanner.py"],
        "py_files": ["openagent/scanner.py"],
        "test_files": [],
        "config_files": [],
        "doc_files": [],
    }


def _make_doc_result():
    return {"current_md": {
        "phase": "Phase 7",
        "what_is_built": "AsyncTestRunner",
        "what_is_next": "Phase 8",
        "test_floor": "108/0/0",
        "open_questions": "",
        "recent_decisions": "",
    }}


class TestAssessorPhase7:
    def test_assessor_includes_test_cmd(self):
        assessor = Assessor()
        scan = {**_make_scan_result(), "git": None, "test_cmd": "python -m pytest"}
        prompt = assessor._build_prompt(scan, _make_doc_result())
        assert "## Test Command" in prompt
        assert "python -m pytest" in prompt

    def test_assessor_handles_none_test_cmd(self):
        assessor = Assessor()
        scan = {**_make_scan_result(), "git": None, "test_cmd": None}
        prompt = assessor._build_prompt(scan, _make_doc_result())
        assert "## Test Command" not in prompt
        assert "Repository:" in prompt
