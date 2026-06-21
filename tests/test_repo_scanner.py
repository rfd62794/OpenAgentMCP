"""
Tests for RepoScanner.
All directory ops use tmp_path. GitContextReader mocked. No real git. No network.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from openagent.repo_scanner import RepoScanner


def _make_git_dir(parent: Path, name: str) -> Path:
    d = parent / name
    d.mkdir()
    (d / ".git").mkdir()
    return d


def _make_plain_dir(parent: Path, name: str) -> Path:
    d = parent / name
    d.mkdir()
    return d


def _git_ctx(date: str = "2026-06-21T00:00:00+00:00") -> dict:
    return {
        "active_branch": "main",
        "last_commit_hash": "abc1234",
        "last_commit_message": "init",
        "last_commit_date": date,
        "uncommitted_files": [],
        "workflows": [],
        "state_phase": None,
    }


class TestRepoScanner:
    def test_discovers_git_repos(self, tmp_path):
        _make_git_dir(tmp_path, "repo-a")
        _make_plain_dir(tmp_path, "not-a-repo")
        with patch("openagent.repo_scanner.GitContextReader.read", return_value=_git_ctx()):
            results = RepoScanner().scan(str(tmp_path))
        assert len(results) == 1
        assert results[0]["name"] == "repo-a"

    def test_skips_non_git_dirs(self, tmp_path):
        _make_plain_dir(tmp_path, "project-no-git")
        with patch("openagent.repo_scanner.GitContextReader.read", return_value=_git_ctx()):
            results = RepoScanner().scan(str(tmp_path))
        assert results == []

    def test_skips_files(self, tmp_path):
        (tmp_path / "somefile.txt").write_text("data")
        _make_git_dir(tmp_path, "real-repo")
        with patch("openagent.repo_scanner.GitContextReader.read", return_value=_git_ctx()):
            results = RepoScanner().scan(str(tmp_path))
        assert len(results) == 1
        assert results[0]["name"] == "real-repo"

    def test_returns_sorted_by_activity(self, tmp_path):
        _make_git_dir(tmp_path, "old-repo")
        _make_git_dir(tmp_path, "new-repo")

        def _ctx_for(path, *a, **kw):
            if "old-repo" in path:
                return _git_ctx("2026-01-01T00:00:00+00:00")
            return _git_ctx("2026-06-21T00:00:00+00:00")

        with patch("openagent.repo_scanner.GitContextReader.read", side_effect=_ctx_for):
            results = RepoScanner().scan(str(tmp_path))

        assert results[0]["name"] == "new-repo"
        assert results[1]["name"] == "old-repo"

    def test_repos_with_null_git_sort_last(self, tmp_path):
        _make_git_dir(tmp_path, "live-repo")
        _make_git_dir(tmp_path, "broken-repo")

        def _ctx_for(path, *a, **kw):
            if "broken-repo" in path:
                return None
            return _git_ctx("2026-06-21T00:00:00+00:00")

        with patch("openagent.repo_scanner.GitContextReader.read", side_effect=_ctx_for):
            results = RepoScanner().scan(str(tmp_path))

        assert results[0]["name"] == "live-repo"
        assert results[1]["name"] == "broken-repo"
        assert results[1]["git"] is None

    def test_max_repos_respected(self, tmp_path):
        for i in range(10):
            _make_git_dir(tmp_path, f"repo-{i:02d}")
        with patch("openagent.repo_scanner.GitContextReader.read", return_value=_git_ctx()):
            results = RepoScanner().scan(str(tmp_path), max_repos=3)
        assert len(results) == 3

    def test_empty_root(self, tmp_path):
        results = RepoScanner().scan(str(tmp_path))
        assert results == []
