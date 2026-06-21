"""
Tests for AsyncTestRunner.
All subprocess calls mocked. No real processes spawned. No network.
"""
from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from openagent.test_runner import AsyncTestRunner, LOG_FILENAME, PID_FILENAME, _STATE_DIR


def _make_mock_proc(pid: int = 42):
    proc = MagicMock()
    proc.pid = pid
    return proc


class TestAsyncTestRunner:
    def test_run_returns_started(self, tmp_path):
        mock_proc = _make_mock_proc(pid=42)
        with patch("openagent.test_runner.subprocess.Popen", return_value=mock_proc):
            result = AsyncTestRunner().run(str(tmp_path), "pytest")
        assert result["status"] == "started"
        assert result["pid"] == 42
        assert result["cmd"] == "pytest"
        assert "log_path" in result

    def test_run_writes_pid_file(self, tmp_path):
        mock_proc = _make_mock_proc(pid=99)
        with patch("openagent.test_runner.subprocess.Popen", return_value=mock_proc):
            AsyncTestRunner().run(str(tmp_path), "pytest")
        pid_path = tmp_path / _STATE_DIR / PID_FILENAME
        assert pid_path.exists()
        assert pid_path.read_text(encoding="utf-8").strip() == "99"

    def test_run_writes_log_header(self, tmp_path):
        mock_proc = _make_mock_proc(pid=7)
        with patch("openagent.test_runner.subprocess.Popen", return_value=mock_proc):
            AsyncTestRunner().run(str(tmp_path), "pytest")
        log_path = tmp_path / _STATE_DIR / LOG_FILENAME
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert content.startswith("# Test run started:")

    def test_run_uses_shell_true(self, tmp_path):
        mock_proc = _make_mock_proc()
        with patch("openagent.test_runner.subprocess.Popen", return_value=mock_proc) as mock_popen:
            AsyncTestRunner().run(str(tmp_path), "pytest")
        _, kwargs = mock_popen.call_args
        assert kwargs.get("shell") is True
