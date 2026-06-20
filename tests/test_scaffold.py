"""Scaffold tests — verify structure only, no logic tests yet."""
import pytest
from pathlib import Path
import sys


def test_package_imports():
    """import openagent succeeds."""
    import openagent
    assert openagent is not None


def test_version_string():
    """openagent.__version__ == "0.3.0"."""
    import openagent
    assert openagent.__version__ == "0.3.0"


def test_cli_importable():
    """from openagent.cli import cli succeeds."""
    from openagent.cli import cli
    assert cli is not None


def test_scanner_importable():
    """from openagent.scanner import Scanner succeeds."""
    from openagent.scanner import Scanner
    assert Scanner is not None


def test_assessor_importable():
    """from openagent.assessor import Assessor succeeds."""
    from openagent.assessor import Assessor
    assert Assessor is not None


def test_writer_importable():
    """from openagent.writer import Writer succeeds."""
    from openagent.writer import Writer
    assert Writer is not None


def test_server_no_fastmcp_raises():
    """main() raises ImportError when fastmcp absent (mock import)."""
    # Mock the import guard to simulate fastmcp not being available
    import openagent.server
    original_available = openagent.server._MCP_AVAILABLE
    try:
        openagent.server._MCP_AVAILABLE = False
        with pytest.raises(ImportError, match="MCP server requires the \\[mcp\\] extra"):
            openagent.server.main()
    finally:
        openagent.server._MCP_AVAILABLE = original_available


def test_agent_contract_exists():
    """Path("AGENT_CONTRACT.md").exists() is True."""
    assert Path("AGENT_CONTRACT.md").exists()


def test_adr_directory_exists():
    """Path("docs/adr").is_dir() is True."""
    assert Path("docs/adr").is_dir()


def test_three_adrs_present():
    """ADR-001, ADR-002, ADR-003 all exist."""
    assert Path("docs/adr/ADR-001.md").exists()
    assert Path("docs/adr/ADR-002.md").exists()
    assert Path("docs/adr/ADR-003.md").exists()
