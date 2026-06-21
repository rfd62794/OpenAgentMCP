"""
TestCommandResolver — resolves the test command for a repository.

Pure logic. No subprocess. No model calls. No external dependencies.

Resolution order:
  1. AGENT_CONTRACT.md test_cmd: line (wins unconditionally)
  2. File-based detection (Cargo.toml, pyproject.toml/pytest.ini/setup.cfg,
     package.json, go.mod)
  3. None — error returned, never guessed
"""
from __future__ import annotations
from pathlib import Path


_DETECTION_MAP = [
    ("Cargo.toml", "cargo test"),
    ("pyproject.toml", "python -m pytest"),
    ("pytest.ini", "python -m pytest"),
    ("setup.cfg", "python -m pytest"),
    ("package.json", "npm test"),
    ("go.mod", "go test ./..."),
]


class TestCommandResolver:
    def resolve(self, repo_path: str) -> str | None:
        """
        Return the test command string for repo_path, or None if unresolvable.

        Resolution order:
          1. AGENT_CONTRACT.md test_cmd: line
          2. File-based detection
          3. None
        """
        repo = Path(repo_path).resolve()

        cmd = self._from_contract(repo)
        if cmd is not None:
            return cmd

        return self._from_detection(repo)

    def _from_contract(self, repo: Path) -> str | None:
        contract = repo / "AGENT_CONTRACT.md"
        if not contract.exists():
            return None
        for line in contract.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("test_cmd:"):
                value = stripped[len("test_cmd:"):].strip().strip("`").strip()
                return value if value else None
        return None

    def _from_detection(self, repo: Path) -> str | None:
        for filename, cmd in _DETECTION_MAP:
            if (repo / filename).exists():
                return cmd
        return None
