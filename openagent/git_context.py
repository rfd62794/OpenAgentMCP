"""
GitContextReader — reads local git state for a repo path.

Subprocess-based. Returns None if path is not a git repo,
git binary is unavailable, or any command fails.
Never raises — all errors degrade to None return.
"""
from __future__ import annotations
import subprocess
from pathlib import Path


class GitContextReader:
    def read(self, repo_path: str) -> dict | None:
        """
        Returns git context dict or None.

        Keys when successful:
          active_branch: str
          last_commit_hash: str        # 7-char short hash
          last_commit_message: str
          last_commit_date: str        # ISO 8601
          uncommitted_files: list[str] # empty list if clean
          workflows: list[str]         # .md names in .windsurf/workflows/
          state_phase: str | None      # from docs/state/current.md
        """
        try:
            active_branch = self._run(repo_path, ["git", "-C", repo_path, "branch", "--show-current"])
            last_commit_hash = self._run(repo_path, ["git", "-C", repo_path, "log", "-1", "--format=%h"])
            last_commit_message = self._run(repo_path, ["git", "-C", repo_path, "log", "-1", "--format=%s"])
            last_commit_date = self._run(repo_path, ["git", "-C", repo_path, "log", "-1", "--format=%cI"])
            status_raw = self._run(repo_path, ["git", "-C", repo_path, "status", "--short"])
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

        uncommitted_files = self._parse_status(status_raw)
        workflows = self._read_workflows(repo_path)
        state_phase = self._read_state_phase(repo_path)

        return {
            "active_branch": active_branch,
            "last_commit_hash": last_commit_hash,
            "last_commit_message": last_commit_message,
            "last_commit_date": last_commit_date,
            "uncommitted_files": uncommitted_files,
            "workflows": workflows,
            "state_phase": state_phase,
        }

    def _run(self, repo_path: str, cmd: list[str]) -> str:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def _parse_status(self, status_raw: str) -> list[str]:
        files = []
        for line in status_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            files.append(line.split()[-1])
        return files

    def _read_workflows(self, repo_path: str) -> list[str]:
        wf_path = Path(repo_path) / ".windsurf" / "workflows"
        if not wf_path.exists():
            return []
        return [f.name for f in wf_path.glob("*.md")]

    def _read_state_phase(self, repo_path: str) -> str | None:
        state_path = Path(repo_path) / "docs" / "state" / "current.md"
        if not state_path.exists():
            return None
        for line in state_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("phase:"):
                value = line[len("phase:"):].strip().strip("'\"")
                return value if value else None
        return None
