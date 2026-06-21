"""
RepoScanner — discovers git repos one level deep under a root path.

Pure stdlib + GitContextReader. No subprocess directly.
Never raises — errors per repo degrade to partial result.
"""
from __future__ import annotations
from pathlib import Path

from openagent.git_context import GitContextReader


class RepoScanner:
    def scan(self, root_path: str, max_repos: int = 50) -> list[dict]:
        """
        Returns list of repo context dicts, sorted by last_commit_date
        descending (most recently active first). Repos where
        GitContextReader returns None are included with git: null.

        Each dict shape:
          {
            "name": str,          # directory name
            "path": str,          # absolute path
            "git": dict | None,   # GitContextReader output
          }
        """
        root = Path(root_path)
        max_repos = max(1, min(max_repos, 200))
        reader = GitContextReader()
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
                })
            except PermissionError:
                continue

        results.sort(
            key=lambda r: r["git"]["last_commit_date"] if r["git"] else "",
            reverse=True,
        )
        return results[:max_repos]
