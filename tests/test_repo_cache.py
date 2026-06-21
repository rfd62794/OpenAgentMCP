"""
Tests for RepoCache.
All SQLite ops use tmp_path with OPENAGENT_REPOS_DB env override.
No real filesystem scans. No network.
"""
from __future__ import annotations
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from openagent.repo_cache import RepoCache


def _make_cache(tmp_path: Path) -> RepoCache:
    db = str(tmp_path / "repos.db")
    with patch.dict(os.environ, {"OPENAGENT_REPOS_DB": db, "OPENAGENT_CACHE_TTL_SECONDS": "300"}):
        return RepoCache()


def _sample_repos(root: str) -> list[dict]:
    return [
        {
            "name": "alpha",
            "path": f"{root}/alpha",
            "git": {
                "active_branch": "main",
                "last_commit_hash": "abc1234",
                "last_commit_message": "init",
                "last_commit_date": "2026-06-21T00:00:00+00:00",
                "uncommitted_files": [],
                "workflows": [],
                "state_phase": None,
            },
            "test_cmd": "python -m pytest",
        },
        {
            "name": "beta",
            "path": f"{root}/beta",
            "git": None,
            "test_cmd": None,
        },
    ]


class TestRepoCache:
    def test_cache_stores_and_loads(self, tmp_path):
        cache = _make_cache(tmp_path)
        root = str(tmp_path)
        repos = _sample_repos(root)
        cache.save(root, repos)
        loaded = cache.load(root)
        names = {r["name"] for r in loaded}
        assert names == {"alpha", "beta"}
        alpha = next(r for r in loaded if r["name"] == "alpha")
        assert alpha["test_cmd"] == "python -m pytest"
        assert alpha["git"]["active_branch"] == "main"

    def test_cache_is_fresh_within_ttl(self, tmp_path):
        cache = _make_cache(tmp_path)
        root = str(tmp_path)
        cache.save(root, _sample_repos(root))
        assert cache.is_fresh(root) is True

    def test_cache_stale_past_ttl(self, tmp_path):
        db = str(tmp_path / "repos.db")
        with patch.dict(os.environ, {"OPENAGENT_REPOS_DB": db, "OPENAGENT_CACHE_TTL_SECONDS": "0"}):
            cache = RepoCache()
        root = str(tmp_path)
        cache.save(root, _sample_repos(root))
        assert cache.is_fresh(root) is False

    def test_cache_refresh_bypasses_ttl(self, tmp_path):
        from openagent.repo_scanner import RepoScanner
        root = str(tmp_path)

        git_dir = tmp_path / "myrepo"
        git_dir.mkdir()
        (git_dir / ".git").mkdir()

        db = str(tmp_path / "repos.db")
        git_ctx = {
            "active_branch": "main",
            "last_commit_hash": "abc",
            "last_commit_message": "x",
            "last_commit_date": "2026-06-21T00:00:00+00:00",
            "uncommitted_files": [],
            "workflows": [],
            "state_phase": None,
        }

        with patch.dict(os.environ, {"OPENAGENT_REPOS_DB": db, "OPENAGENT_CACHE_TTL_SECONDS": "300"}):
            with patch("openagent.repo_scanner.GitContextReader.read", return_value=git_ctx):
                with patch("openagent.repo_scanner.TestCommandResolver.resolve", return_value=None):
                    first = RepoScanner().scan(root, use_cache=True, refresh=False)
                    second = RepoScanner().scan(root, use_cache=True, refresh=True)
        assert len(first) == 1
        assert len(second) == 1

    def test_get_one_found(self, tmp_path):
        cache = _make_cache(tmp_path)
        root = str(tmp_path)
        cache.save(root, _sample_repos(root))
        result = cache.get_one("alpha")
        assert result is not None
        assert result["name"] == "alpha"
        assert result["test_cmd"] == "python -m pytest"

    def test_get_one_missing(self, tmp_path):
        cache = _make_cache(tmp_path)
        result = cache.get_one("nonexistent")
        assert result is None

    def test_scan_stores_test_cmd(self, tmp_path):
        from openagent.repo_scanner import RepoScanner

        root = str(tmp_path)
        git_dir = tmp_path / "proj"
        git_dir.mkdir()
        (git_dir / ".git").mkdir()

        db = str(tmp_path / "repos.db")
        git_ctx = {
            "active_branch": "main",
            "last_commit_hash": "abc",
            "last_commit_message": "x",
            "last_commit_date": "2026-06-21T00:00:00+00:00",
            "uncommitted_files": [],
            "workflows": [],
            "state_phase": None,
        }

        with patch.dict(os.environ, {"OPENAGENT_REPOS_DB": db}):
            with patch("openagent.repo_scanner.GitContextReader.read", return_value=git_ctx):
                with patch("openagent.repo_scanner.TestCommandResolver.resolve", return_value="cargo test"):
                    RepoScanner().scan(root, use_cache=True, refresh=False)
            cache = RepoCache()
            result = cache.get_one("proj")

        assert result is not None
        assert result["test_cmd"] == "cargo test"
