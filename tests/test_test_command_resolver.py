"""
Tests for TestCommandResolver.
All file I/O uses tmp_path. No subprocess. No network.
"""
from __future__ import annotations
import pytest
from pathlib import Path

from openagent.test_command_resolver import TestCommandResolver


def _write_contract(tmp_path: Path, content: str) -> None:
    (tmp_path / "AGENT_CONTRACT.md").write_text(content, encoding="utf-8")


class TestFromContract:
    def test_resolves_from_agent_contract(self, tmp_path):
        _write_contract(tmp_path, "# Contract\ntest_cmd: cargo test\n")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "cargo test"

    def test_strips_backticks(self, tmp_path):
        _write_contract(tmp_path, "test_cmd: `uv run pytest`\n")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "uv run pytest"

    def test_contract_wins_over_detection(self, tmp_path):
        _write_contract(tmp_path, "test_cmd: cargo test\n")
        (tmp_path / "Cargo.toml").write_text("[package]", encoding="utf-8")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "cargo test"


class TestFromDetection:
    def test_detects_cargo(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]", encoding="utf-8")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "cargo test"

    def test_detects_pytest(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "python -m pytest"

    def test_detects_npm(self, tmp_path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result == "npm test"

    def test_returns_none_unresolvable(self, tmp_path):
        result = TestCommandResolver().resolve(str(tmp_path))
        assert result is None
