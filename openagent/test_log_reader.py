"""
TestLogReader — reads the async test log and checks process liveness.

Reads docs/state/openagent_test.log.
Checks PID liveness via tasklist (Windows) with ps fallback (Unix).
Never raises — errors surface as not_started or empty output.
"""
from __future__ import annotations
import subprocess
from pathlib import Path

from openagent.test_runner import LOG_FILENAME, PID_FILENAME, _STATE_DIR

_MAX_TAIL = 200


class TestLogReader:
    def read(self, repo_path: str, tail: int = 100) -> dict:
        """
        Read the test log and check process status.

        tail: lines to return from end of log (capped at 200).

        Returns:
          {"status": "running"|"complete"|"not_started", "output": str, "exit_code": None}
        """
        repo = Path(repo_path).resolve()
        pid_path = repo / _STATE_DIR / PID_FILENAME
        log_path = repo / _STATE_DIR / LOG_FILENAME

        if not pid_path.exists():
            return {"status": "not_started", "output": "", "exit_code": None}

        pid = int(pid_path.read_text(encoding="utf-8").strip())
        running = self._is_running(pid)

        tail = min(tail, _MAX_TAIL)
        output = ""
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            output = "\n".join(lines[-tail:]) if lines else ""

        status = "running" if running else "complete"
        return {"status": status, "output": output, "exit_code": None}

    def _is_running(self, pid: int) -> bool:
        """Return True if the process with pid is alive."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, check=False,
            )
            if str(pid) in result.stdout:
                return True
        except FileNotFoundError:
            pass

        try:
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True, text=True, check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            pass

        return False
