"""
RepoCache — SQLite-backed cache for RepoScanner output.

DB location: OPENAGENT_REPOS_DB env var or ~/.openagent/repos.db
TTL: OPENAGENT_CACHE_TTL_SECONDS env var or 300 (5 minutes)
"""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path


class RepoCache:
    DEFAULT_DB = Path.home() / ".openagent" / "repos.db"
    DEFAULT_TTL = 300

    def __init__(self) -> None:
        db_path = os.environ.get("OPENAGENT_REPOS_DB", str(self.DEFAULT_DB))
        self.db_path = Path(db_path)
        self.ttl = int(os.environ.get("OPENAGENT_CACHE_TTL_SECONDS", self.DEFAULT_TTL))
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS repos (
                    name         TEXT PRIMARY KEY,
                    path         TEXT NOT NULL,
                    last_scanned TEXT NOT NULL,
                    git_json     TEXT,
                    test_cmd     TEXT
                )
            """)

    def is_fresh(self, root_path: str) -> bool:
        """True if any row for this root exists and last_scanned is within TTL."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.ttl)
        root_prefix = str(root_path).rstrip("/\\")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT MIN(last_scanned) AS oldest FROM repos WHERE path LIKE ?",
                (root_prefix + "%",),
            ).fetchone()
        oldest = row["oldest"] if row else None
        if not oldest:
            return False
        try:
            oldest_dt = datetime.fromisoformat(oldest)
            if oldest_dt.tzinfo is None:
                oldest_dt = oldest_dt.replace(tzinfo=timezone.utc)
            return oldest_dt >= cutoff
        except ValueError:
            return False

    def load(self, root_path: str) -> list[dict]:
        """Return cached rows for root_path as list of dicts."""
        root_prefix = str(root_path).rstrip("/\\")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM repos WHERE path LIKE ?",
                (root_prefix + "%",),
            ).fetchall()
        return [
            {
                "name": row["name"],
                "path": row["path"],
                "git": json.loads(row["git_json"]) if row["git_json"] else None,
                "test_cmd": row["test_cmd"],
            }
            for row in rows
        ]

    def save(self, root_path: str, repos: list[dict]) -> None:
        """Upsert all repos. Sets last_scanned to UTC now."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for repo in repos:
                conn.execute(
                    """
                    INSERT INTO repos (name, path, last_scanned, git_json, test_cmd)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        path=excluded.path,
                        last_scanned=excluded.last_scanned,
                        git_json=excluded.git_json,
                        test_cmd=excluded.test_cmd
                    """,
                    (
                        repo["name"],
                        repo["path"],
                        now,
                        json.dumps(repo.get("git")) if repo.get("git") is not None else None,
                        repo.get("test_cmd"),
                    ),
                )

    def get_one(self, name: str) -> dict | None:
        """Return single repo dict by name or None."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM repos WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return {
            "name": row["name"],
            "path": row["path"],
            "git": json.loads(row["git_json"]) if row["git_json"] else None,
            "test_cmd": row["test_cmd"],
        }
