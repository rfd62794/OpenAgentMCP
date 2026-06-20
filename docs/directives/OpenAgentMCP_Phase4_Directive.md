# OpenAgentMCP — Phase 4 Directive: MCP Server + Serve Command

*June 2026 | Read fully before executing anything.*

---

> ⛔ **STOP:** Run pytest before touching any file.
> Must report **60 passing, 0 failing, 0 skipped**.
> If count differs, stop and report — do not proceed.

---

## §0 Context

**What exists:**
- Phase 3 certified at 60/0/0
- Full pipeline operational: Scanner → Assessor → Writer → ScopeGuard → StateWriter
- `openagent serve` CLI command does not yet exist
- `openagent/server.py` is a stub with import guard — `_MCP_AVAILABLE` flag, `main()` raises `NotImplementedError`
- `pyproject.toml` has `[mcp]` optional extra with `fastmcp>=0.4.0` — version needs updating

**What Phase 4 delivers:**
1. `openagent/server.py` — FastMCP server with two tools: `analyze_repo` and `assess_repo`
2. `openagent/cli.py` — `serve` command added
3. `pyproject.toml` — fastmcp version updated to `>=2.0.0`
4. `docs/adr/ADR-004.md` — two MCP tools, stdio transport for Claude Desktop
5. Tests for tool functions and serve command

**What is NOT in scope:**
- HTTP or SSE transport — stdio only for Claude Desktop
- Authentication or OAuth
- Any changes to Scanner, Assessor, Writer, ScopeGuard, StateWriter
- Any changes to existing tests

**FastMCP version note:**
FastMCP is at 3.x as of June 2026. Update the `[mcp]` extra to `fastmcp>=2.0.0`.
The decorator pattern `@mcp.tool()` is stable across 2.x and 3.x.

---

## §1 Scope Statement

| File | Status | Action |
|---|---|---|
| `openagent/server.py` | Modify | Replace stub with FastMCP server + two tools |
| `openagent/cli.py` | Modify | Add `serve` command |
| `pyproject.toml` | Modify | Update `fastmcp>=0.4.0` → `fastmcp>=2.0.0` |
| `docs/adr/ADR-004.md` | New | Two MCP tools, stdio transport |
| `tests/test_server.py` | New | Tool function tests + serve command test |

**Read-only — do not touch:**
`openagent/scanner.py`, `openagent/assessor.py`, `openagent/writer.py`,
`openagent/scope_guard.py`, `openagent/state_writer.py`, `openagent/models.py`,
`openagent/model_router.py`, `openagent/__init__.py`,
all existing tests, `AGENT_CONTRACT.md`, `SOUL.md`, ADRs 001-003

---

## §2 Implementation

### 2.1 `docs/adr/ADR-004.md`

Write this ADR before touching any code.

```markdown
# ADR-004: Two MCP Tools, Stdio Transport

## Status
Accepted

## Context
OpenAgentMCP exposes the analysis pipeline as MCP tools for Claude Desktop.
Two distinct use cases exist:
1. Full pipeline run — scan, assess, write directive, save state (slow, costs tokens)
2. Assessment only — scan + assess, return structured state (fast, cheap)

Users need both without running the full pipeline every time.

## Decision
Two MCP tools:
- `analyze_repo(repo_path, intent)` — full pipeline, writes current.md, returns directive + metadata
- `assess_repo(repo_path)` — scan + assess only, returns AssessmentResult, does not write state

Transport: stdio only. Claude Desktop launches the server as a subprocess.
Server entry: `openagent serve` CLI command calls `mcp.run()`.

## Consequences
- Both tools must handle missing SOUL.md gracefully (empty string)
- Both tools raise ValueError on bad repo_path — not caught, surfaced to MCP client
- `assess_repo` never writes files — safe for read-only inspection
- This ADR is permanent — no HTTP transport added without a superseding ADR
```

---

### 2.2 `openagent/server.py`

```python
"""
MCP Server — exposes OpenAgent pipeline as MCP tools.
Requires: pip install openagent-directive[mcp]

Tools:
  analyze_repo(repo_path, intent) — full pipeline, writes state
  assess_repo(repo_path)          — scan + assess only, read-only
"""

try:
    from fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def _require_mcp() -> None:
    if not _MCP_AVAILABLE:
        raise ImportError(
            "MCP server requires the [mcp] extra.\n"
            "Install with: pip install openagent-directive[mcp]"
        )


def _build_server():
    """Build and return the FastMCP server instance. Called lazily."""
    from fastmcp import FastMCP
    from pathlib import Path

    mcp = FastMCP("OpenAgentMCP")

    @mcp.tool()
    def analyze_repo(repo_path: str, intent: str = "") -> dict:
        """
        Analyze a repository and generate a directive.

        Runs the full pipeline: Scanner → Assessor → Writer → StateWriter.
        Writes docs/state/current.md in the target repo.

        Args:
            repo_path: Absolute or relative path to the repository root.
            intent: Architect's goal for this phase. Falls back to what_is_next
                    in current.md if empty.

        Returns:
            dict with keys:
                directive: str — the generated directive text
                assessment: dict — AssessmentResult from Assessor
                state_path: str — path of written current.md
                floor_ok: bool — whether test floor was clean
        """
        from openagent.scanner import Scanner
        from openagent.assessor import Assessor
        from openagent.writer import Writer
        from openagent.scope_guard import ScopeGuard
        from openagent.state_writer import StateWriter

        repo = Path(repo_path).resolve()
        soul_text = _read_soul(repo)
        doc_result = _read_current_md(repo)

        scan_result = Scanner().scan(str(repo))
        assessment = Assessor().assess(scan_result, doc_result)

        guard = ScopeGuard()
        floor_ok, _ = guard.check_floor(assessment)

        writer = Writer()
        directive = writer.write(assessment, intent or None, soul_text)

        state_path = StateWriter().write(repo, assessment, intent or None, directive)

        return {
            "directive": directive,
            "assessment": assessment,
            "state_path": str(state_path),
            "floor_ok": floor_ok,
        }

    @mcp.tool()
    def assess_repo(repo_path: str) -> dict:
        """
        Assess a repository's current state without generating a directive.

        Runs Scanner + Assessor only. Does not write any files.
        Cheaper and faster than analyze_repo — useful for status checks.

        Args:
            repo_path: Absolute or relative path to the repository root.

        Returns:
            AssessmentResult dict with repo state, test floor, open questions, etc.
        """
        from openagent.scanner import Scanner
        from openagent.assessor import Assessor

        repo = Path(repo_path).resolve()
        doc_result = _read_current_md(repo)
        scan_result = Scanner().scan(str(repo))
        return Assessor().assess(scan_result, doc_result)

    return mcp


def _read_soul(repo) -> str:
    soul = repo / "SOUL.md"
    return soul.read_text(encoding="utf-8") if soul.exists() else ""


def _read_current_md(repo) -> dict:
    current = repo / "docs" / "state" / "current.md"
    if not current.exists():
        return {"current_md": {}}
    lines = current.read_text(encoding="utf-8").splitlines()
    fields = {}
    for line in lines:
        if ": " in line:
            key, _, val = line.partition(": ")
            fields[key.strip()] = val.strip()
    return {"current_md": fields}


def main() -> None:
    """Entry point for MCP server. Requires [mcp] extra."""
    _require_mcp()
    mcp = _build_server()
    mcp.run()
```

> ⚠️ RULE: `_build_server()` is called lazily inside `main()` — never at module import time. `server.py` must remain importable without fastmcp installed.

> ⚠️ RULE: `_read_soul` and `_read_current_md` are duplicated from `cli.py` intentionally — `server.py` must not import from `cli.py`. Keep them in sync manually or extract to a `_utils.py` in Phase 5.

> ⚠️ RULE: All pipeline imports (`Scanner`, `Assessor`, etc.) are inside the tool functions — never at module level. This keeps `server.py` importable without triggering `requests`.

---

### 2.3 `openagent/cli.py` — add `serve` command

Add after the existing `analyze` command:

```python
@cli.command()
def serve():
    """
    Start the MCP server for Claude Desktop.

    Requires: pip install openagent-directive[mcp]

    Add to claude_desktop_config.json:
        {
          "openagent": {
            "command": "uv",
            "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"]
          }
        }
    """
    from openagent.server import main
    main()
```

> ⚠️ RULE: `serve` command imports `main` from `server.py` inside the function body — not at module level.

---

### 2.4 `pyproject.toml`

Update the `[mcp]` optional dependency version only:

```toml
[project.optional-dependencies]
mcp = ["fastmcp>=2.0.0"]
dev = ["pytest>=8.0.0", "pytest-mock>=3.0.0"]
```

> ⚠️ RULE: This is a one-line change. Touch only the fastmcp version string.

---

## §3 Test Anchors

Testing strategy: FastMCP is mocked at the import boundary. Tool functions are tested directly without MCP protocol overhead.

```python
# Fixture pattern for tests:
@pytest.fixture
def mock_fastmcp(monkeypatch):
    """Mock fastmcp so server.py is importable without the [mcp] extra."""
    mock_mcp_module = MagicMock()
    mock_server = MagicMock()
    mock_mcp_module.FastMCP.return_value = mock_server
    monkeypatch.setitem(sys.modules, "fastmcp", mock_mcp_module)
    return mock_server
```

| Test | File | Behaviour |
|---|---|---|
| `test_main_raises_without_fastmcp` | `test_server.py` | Remove fastmcp from sys.modules → `main()` raises `ImportError` with install instructions |
| `test_build_server_returns_mcp_instance` | `test_server.py` | Mock fastmcp → `_build_server()` returns FastMCP instance |
| `test_analyze_repo_tool_returns_required_keys` | `test_server.py` | Mock Scanner, Assessor, Writer, StateWriter → result has directive, assessment, state_path, floor_ok |
| `test_analyze_repo_tool_empty_intent_falls_back` | `test_server.py` | intent="" → Writer called with intent=None |
| `test_assess_repo_tool_returns_assessment` | `test_server.py` | Mock Scanner, Assessor → returns AssessmentResult dict |
| `test_assess_repo_tool_does_not_write_files` | `test_server.py` | StateWriter never called in `assess_repo` |
| `test_read_soul_returns_empty_when_missing` | `test_server.py` | tmp dir without SOUL.md → returns "" |
| `test_read_soul_returns_content_when_present` | `test_server.py` | SOUL.md in tmp dir → returns file content |
| `test_serve_command_calls_main` | `test_server.py` | Mock `server.main` → Click CliRunner `serve` → main called once |
| `test_serve_command_fails_without_fastmcp` | `test_server.py` | fastmcp absent → serve exits non-zero with install message |

**Target: 70 passing, 0 failing, 0 skipped** (60 existing + 10 new)

---

## §4 Completion Criteria

- [ ] pytest: **70 passing, 0 failing, 0 skipped** — raw terminal output pasted
- [ ] `uv run openagent serve --help` shows serve command with Claude Desktop config hint
- [ ] `uv pip install -e ".[mcp]"` succeeds and installs fastmcp
- [ ] Manual smoke test: `uv run openagent analyze . --intent "verify Phase 4 MCP server"` runs end-to-end and prints directive
- [ ] `ADR-004.md` written to `docs/adr/ADR-004.md`
- [ ] `docs/state/current.md` updated: phase 4, floor 70/0/0, next = Phase 5 (Claude Desktop config, PyPI publish v0.3.0)

---

## §5 Quick Reference

| Key | Value |
|---|---|
| Baseline floor | 60/0/0 |
| Target floor | 70/0/0 |
| FastMCP version | `>=2.0.0` (3.x current as of June 2026) |
| Transport | stdio only — Claude Desktop subprocess model |
| Tool 1 | `analyze_repo(repo_path, intent)` — full pipeline |
| Tool 2 | `assess_repo(repo_path)` — read-only scan + assess |
| MCP import guard | `_MCP_AVAILABLE` flag in server.py — always present |
| `_build_server()` | Called lazily inside `main()` — never at import time |
| serve command | Imports `server.main` inside function body |
| Claude Desktop config | `uv run --with openagent-directive[mcp] openagent serve` |
| Phase 5 | Claude Desktop config doc + PyPI publish v0.3.0 |
