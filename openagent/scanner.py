"""
Scanner — reads repository structure.
Returns a structured file inventory for the Assessor.
Pure stdlib. No external dependencies. No model calls.
"""
import os
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", ".pytest_cache"}
FILE_TREE_LIMIT = 60


class Scanner:
    """Scans a repository and returns a structured file inventory."""

    def scan(self, repo_path: str) -> dict:
        """
        Scan repo_path and return structured inventory.

        Returns:
            dict with keys:
                repo_path: str
                file_tree: list[str]  — all files, relative paths, forward slashes
                py_files: list[str]   — .py files excluding tests/
                test_files: list[str] — files under tests/ ending in .py
                config_files: list[str]
                doc_files: list[str]
        """
        repo = Path(repo_path).resolve()
        all_files = self._walk(repo)

        test_files = [f for f in all_files if f.startswith("tests/") and f.endswith(".py")]
        py_files = [f for f in all_files if f.endswith(".py") and f not in test_files]
        config_files = [f for f in all_files if Path(f).name in {"pyproject.toml", ".env.example", "Cargo.toml"}]
        doc_files = [f for f in all_files if Path(f).name in {"README.md", "AGENT_CONTRACT.md", "SOUL.md"}]

        handled = set(test_files + py_files + config_files + doc_files)
        other_files = [f for f in all_files if f not in handled]

        file_tree = self._truncate(py_files, test_files, config_files, doc_files, other_files)

        return {
            "repo_path": str(repo),
            "file_tree": file_tree,
            "py_files": py_files,
            "test_files": test_files,
            "config_files": config_files,
            "doc_files": doc_files,
        }

    def _walk(self, repo: Path) -> list[str]:
        """Walk repo, skip excluded dirs, return relative paths with forward slashes."""
        result = []
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in sorted(files):
                rel = os.path.relpath(os.path.join(root, file), repo)
                result.append(rel.replace("\\", "/"))
        return sorted(result)

    def _truncate(self, py_files, test_files, config_files, doc_files, other_files) -> list[str]:
        """Assemble file_tree up to FILE_TREE_LIMIT, prioritising test files."""
        budget = FILE_TREE_LIMIT - len(test_files)
        py_part = py_files[:budget]
        budget -= len(py_part)
        config_part = config_files[:budget]
        budget -= len(config_part)
        doc_part = doc_files[:budget]
        budget -= len(doc_part)
        other_part = other_files[:budget]

        tree = py_part + test_files + config_part + doc_part + other_part
        if (len(py_files) + len(test_files) + len(config_files) +
                len(doc_files) + len(other_files)) > FILE_TREE_LIMIT:
            tree.append("... (truncated)")
        return tree
