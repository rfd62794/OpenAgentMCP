"""
RepoScanner — discovers git repos one level deep under a root path.

Pure stdlib + GitContextReader. No subprocess directly.
Never raises — errors per repo degrade to partial result.
"""
from __future__ import annotations
from pathlib import Path

from openagent.git_context import GitContextReader
from openagent.test_command_resolver import TestCommandResolver


class RepoScanner:
    def scan(
        self,
        root_path: str,
        max_repos: int = 50,
        use_cache: bool = False,
        refresh: bool = False,
    ) -> list[dict]:
        """
        Returns list of repo context dicts, sorted by last_commit_date
        descending (most recently active first). Repos where
        GitContextReader returns None are included with git: null.

        Each dict shape:
          {
            "name": str,          # directory name
            "path": str,          # absolute path
            "git": dict | None,   # GitContextReader output
            "test_cmd": str | None,
          }

        use_cache: read/write SQLite cache (default False)
        refresh: force full re-scan even if cache is fresh
        """
        max_repos = max(1, min(max_repos, 200))

        if use_cache and not refresh:
            from openagent.repo_cache import RepoCache
            cache = RepoCache()
            if cache.is_fresh(root_path):
                return cache.load(root_path)[:max_repos]

        results = self._live_scan(root_path)

        if use_cache:
            from openagent.repo_cache import RepoCache
            RepoCache().save(root_path, results)

        results.sort(
            key=lambda r: r["git"]["last_commit_date"] if r["git"] else "",
            reverse=True,
        )
        return results[:max_repos]

    def _live_scan(self, root_path: str) -> list[dict]:
        root = Path(root_path)
        reader = GitContextReader()
        resolver = TestCommandResolver()
        results = []

        for subdir in root.iterdir():
            try:
                if not subdir.is_dir():
                    continue
                if not (subdir / ".git").exists():
                    continue
                try:
                    git_ctx = reader.read(str(subdir))
                except Exception:
                    git_ctx = None
                results.append({
                    "name": subdir.name,
                    "path": str(subdir),
                    "git": git_ctx,
                    "test_cmd": resolver.resolve(str(subdir)),
                })
            except PermissionError:
                continue

        return results
