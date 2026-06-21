"""
AsyncTestRunner — spawns a test suite as a detached background process.

Uses shell=True (ADR-006 locked). Returns within one second.
Writes stdout+stderr to docs/state/openagent_test.log.
Writes PID to docs/state/openagent_test.pid.
Never blocks. Any spawn error surfaces in the return dict.
"""
from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LOG_FILENAME = "openagent_test.log"
PID_FILENAME = "openagent_test.pid"
_STATE_DIR = Path("docs") / "state"


class AsyncTestRunner:
    def run(self, repo_path: str, cmd: str) -> dict:
        """
        Spawn cmd as a detached background process in repo_path.

        Returns:
          {"status": "started", "pid": int, "log_path": str, "cmd": str}
          {"status": "error",   "reason": str, "pid": None, "cmd": str}
        """
        repo = Path(repo_path).resolve()
        state_dir = repo / _STATE_DIR
        state_dir.mkdir(parents=True, exist_ok=True)

        log_path = state_dir / LOG_FILENAME
        pid_path = state_dir / PID_FILENAME

        try:
            log_file = log_path.open("w", encoding="utf-8")
            log_file.write(f"# Test run started: {datetime.now(timezone.utc).isoformat()}\n")
            log_file.write(f"# Command: {cmd}\n")
            log_file.flush()

            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(repo),
                stdout=log_file,
                stderr=log_file,
            )
            pid_path.write_text(str(proc.pid), encoding="utf-8")

            return {
                "status": "started",
                "pid": proc.pid,
                "log_path": str(log_path),
                "cmd": cmd,
            }
        except Exception as exc:
            return {
                "status": "error",
                "reason": str(exc),
                "pid": None,
                "cmd": cmd,
            }
