"""
Tests for TestLogReader.
All file I/O uses tmp_path. _is_running mocked. No real processes. No network.
"""
from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import patch

from openagent.test_log_reader import TestLogReader
from openagent.test_runner import LOG_FILENAME, PID_FILENAME, _STATE_DIR


def _state_dir(tmp_path: Path) -> Path:
    d = tmp_path / _STATE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


class TestTestLogReader:
    def test_not_started_no_pid_file(self, tmp_path):
        result = TestLogReader().read(str(tmp_path))
        assert result["status"] == "not_started"
        assert result["output"] == ""

    def test_running_pid_alive(self, tmp_path):
        sd = _state_dir(tmp_path)
        (sd / PID_FILENAME).write_text("123", encoding="utf-8")
        (sd / LOG_FILENAME).write_text("line1\nline2\n", encoding="utf-8")
        with patch.object(TestLogReader, "_is_running", return_value=True):
            result = TestLogReader().read(str(tmp_path))
        assert result["status"] == "running"

    def test_complete_pid_dead(self, tmp_path):
        sd = _state_dir(tmp_path)
        (sd / PID_FILENAME).write_text("123", encoding="utf-8")
        (sd / LOG_FILENAME).write_text("line1\nline2\n", encoding="utf-8")
        with patch.object(TestLogReader, "_is_running", return_value=False):
            result = TestLogReader().read(str(tmp_path))
        assert result["status"] == "complete"

    def test_tail_respected(self, tmp_path):
        sd = _state_dir(tmp_path)
        (sd / PID_FILENAME).write_text("123", encoding="utf-8")
        lines = [f"line{i}" for i in range(200)]
        (sd / LOG_FILENAME).write_text("\n".join(lines), encoding="utf-8")
        with patch.object(TestLogReader, "_is_running", return_value=False):
            result = TestLogReader().read(str(tmp_path), tail=50)
        returned_lines = result["output"].splitlines()
        assert len(returned_lines) == 50
        assert returned_lines[-1] == "line199"

    def test_missing_log_file(self, tmp_path):
        sd = _state_dir(tmp_path)
        (sd / PID_FILENAME).write_text("123", encoding="utf-8")
        with patch.object(TestLogReader, "_is_running", return_value=True):
            result = TestLogReader().read(str(tmp_path))
        assert result["output"] == ""
