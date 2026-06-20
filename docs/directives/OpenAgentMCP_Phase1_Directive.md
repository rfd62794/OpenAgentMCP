# OpenAgentMCP — Phase 1 Directive: Repo Scaffold + Framework Foundation

*June 2026 | Read fully before executing anything.*

---

> ⛔ **STOP:** This is a new repo. No existing test floor.
> Create the repo structure first. Report directory tree before writing any code.

---

## §0 Context

**What this is:**
OpenAgentMCP is a clean rebuild of `openagent-directive` (PyPI). v0.3.0. Public, MIT licensed, open source. The old `OpenAgent` repo is archived — do not reference or copy from it directly. The legacy components (`scanner.py`, `assessor.py`, `writer.py`, `model_router.py`, `scope_guard.py`, `state_writer.py`) will be rebuilt one at a time in future phases, cleanly, with SRP discipline.

**What Phase 1 delivers:**
1. Repo scaffold — directory structure, all `__init__.py` files, no logic yet
2. `pyproject.toml` — `openagent-directive` v0.3.0, MIT, Python ≥3.12, `[mcp]` optional extra from day one
3. Three foundation ADRs
4. `AGENT_CONTRACT.md` — structural contract for this repo
5. `SOUL.md` — architect profile (copy from existing)
6. `README.md` — public-facing description
7. `docs/state/current.md` — project state file
8. Minimal test floor — scaffold tests only, no logic tests yet
9. `.gitignore`, `.env.example`

**What is NOT in scope:**
- Any implementation of scanner, assessor, writer, model_router, or any logic component
- The MCP server (Phase 4+)
- The CLI (Phase 2)
- Copying any file wholesale from the old OpenAgent repo
- Any ADK, orchestration, or agent framework code — ever

---

## §1 Scope Statement

| File/Dir | Status | Action |
|---|---|---|
| `openagent/__init__.py` | New | Package init, version string only |
| `openagent/cli.py` | New | Stub — `click` group, no commands yet |
| `openagent/scanner.py` | New | Stub — empty class, docstring only |
| `openagent/assessor.py` | New | Stub — empty class, docstring only |
| `openagent/writer.py` | New | Stub — empty class, docstring only |
| `openagent/model_router.py` | New | Stub — empty class, docstring only |
| `openagent/scope_guard.py` | New | Stub — empty class, docstring only |
| `openagent/state_writer.py` | New | Stub — empty class, docstring only |
| `openagent/server.py` | New | Stub — guarded import, docstring only |
| `tests/__init__.py` | New | Empty |
| `tests/conftest.py` | New | Minimal fixtures |
| `tests/test_scaffold.py` | New | Scaffold tests |
| `pyproject.toml` | New | Full project config |
| `AGENT_CONTRACT.md` | New | Structural contract |
| `SOUL.md` | New | Architect profile |
| `README.md` | New | Public description |
| `docs/adr/ADR-001.md` | New | Language decision |
| `docs/adr/ADR-002.md` | New | Two-stage pipeline architecture |
| `docs/adr/ADR-003.md` | New | MCP as optional extra |
| `docs/state/current.md` | New | Project state |
| `.gitignore` | New | Standard Python + uv |
| `.env.example` | New | Required env vars documented |

---

## §2 Implementation

### 2.1 `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "openagent-directive"
version = "0.3.0"
description = "Repo-aware directive generator with optional MCP server"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
authors = [
    {name = "Robert Floyd Dugger", email = "RFDITServices@gmail.com"}
]
keywords = ["code-analysis", "directive", "mcp", "developer-tools", "ai-agents"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Code Generators",
]
dependencies = [
    "click>=8.1.7",
    "python-dotenv>=1.2.2",
    "requests>=2.32.5",
    "rich>=14.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
mcp = ["fastmcp>=0.4.0"]
dev = ["pytest>=8.0.0", "pytest-mock>=3.0.0"]

[project.urls]
Homepage = "https://github.com/rfd62794/OpenAgentMCP"
Repository = "https://github.com/rfd62794/OpenAgentMCP"
"Bug Tracker" = "https://github.com/rfd62794/OpenAgentMCP/issues"

[project.scripts]
openagent = "openagent.cli:cli"

[tool.hatch.build.targets.wheel]
packages = ["openagent"]
```

> ⚠️ RULE: `pytest` goes in `[dev]` optional, not core dependencies. Core deps are runtime only.

> ⚠️ RULE: `fastmcp` goes in `[mcp]` optional only. Never in core dependencies.

---

### 2.2 Module Stubs

Every stub follows this pattern — no logic, no imports beyond stdlib:

```python
# openagent/scanner.py
"""
Scanner — Phase 2.

Reads repository structure and produces a structured inventory
for consumption by the Assessor. Pure stdlib. No external dependencies.
"""


class Scanner:
    """Scans a repository and returns structured file inventory."""

    def scan(self, repo_path: str) -> dict:
        """Scan repo_path and return structured inventory. Not yet implemented."""
        raise NotImplementedError("Scanner not yet implemented — Phase 2.")
```

Apply the same pattern to: `assessor.py`, `writer.py`, `model_router.py`, `scope_guard.py`, `state_writer.py`

> ⚠️ RULE: Stubs raise `NotImplementedError`. They do not return `None` or empty dict silently. Callers must know this is unimplemented.

---

### 2.3 `openagent/server.py` Stub

```python
"""
MCP Server — Phase 4.

Optional. Requires: pip install openagent-directive[mcp]

Exposes OpenAgent's analyze pipeline as MCP tools for use
with Claude Desktop and other MCP clients.
"""

try:
    import fastmcp  # noqa: F401
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def main():
    """Entry point for MCP server. Requires [mcp] extra."""
    if not _MCP_AVAILABLE:
        raise ImportError(
            "MCP server requires the [mcp] extra.\n"
            "Install with: pip install openagent-directive[mcp]"
        )
    raise NotImplementedError("MCP server not yet implemented — Phase 4.")
```

> ⚠️ RULE: `server.py` must never import fastmcp at module level. The guarded import pattern above is mandatory. Core install must not fail if fastmcp is absent.

---

### 2.4 `openagent/cli.py` Stub

```python
"""CLI entry point — openagent command."""
import click


@click.group()
@click.version_option("0.3.0")
def cli():
    """OpenAgent v0.3 — repo-aware directive generator."""


# Commands added in Phase 2 (analyze, init) and Phase 4 (serve)
```

---

### 2.5 `openagent/__init__.py`

```python
"""OpenAgent — repo-aware directive generator."""

__version__ = "0.3.0"
__all__ = ["__version__"]
```

---

### 2.6 ADRs

**`docs/adr/ADR-001.md` — Python as implementation language:**
```markdown
# ADR-001: Python as Implementation Language

## Status
Accepted

## Context
Primary language across all RFD IT Services projects. Best stdlib tooling for file/AST operations. Fastest path to working CLI and MCP server.

## Decision
Python 3.12+ only. No Rust extension layer until Python core is stable.

## Consequences
- All modules are pure Python
- No compiled extensions in v0.3
- Rust layer may be added in a future ADR if performance requires it
```

**`docs/adr/ADR-002.md` — Two-stage pipeline architecture:**
```markdown
# ADR-002: Two-Stage Pipeline Architecture

## Status
Accepted

## Context
v0.2 accumulated a heavyweight ADK orchestration layer that was never needed. The original two-stage design (cheap model scans repo → capable model writes directive) was working and is the correct architecture.

## Decision
The pipeline is: Scanner → Assessor (cheap model) → Writer (capable model). No framework. No orchestration layer. Direct function calls between stages.

Each stage is a single-responsibility module. No stage knows about the others except through its input/output contract.

## Consequences
- Scanner: pure stdlib, no model calls
- Assessor: one model call, structured JSON output
- Writer: one model call, Markdown directive output
- No agent framework dependency ever
- Stages are independently testable with mocks
```

**`docs/adr/ADR-003.md` — MCP as optional extra:**
```markdown
# ADR-003: MCP Server as Optional Extra

## Status
Accepted

## Context
Not all users need the MCP server. Adding fastmcp to core dependencies bloats the install for CLI-only users. Claude Desktop users need the MCP server; terminal users do not.

## Decision
FastMCP is an optional dependency: pip install openagent-directive[mcp]

The MCP server lives in server.py which guards its fastmcp import. Core package installs and runs without fastmcp present. server.py raises ImportError with install instructions if MCP is unavailable.

## Consequences
- Core install is lightweight
- MCP server is opt-in
- server.py must never import fastmcp at module level
- This ADR is permanent — fastmcp never moves to core dependencies
```

---

### 2.7 `AGENT_CONTRACT.md`

```yaml
# AGENT_CONTRACT
version: 1.0
repo: OpenAgentMCP
updated: 2026-06-20

## STRUCTURE
docs/adr/        : Architectural decisions. Locked after merge. Numbered sequentially.
docs/state/      : current.md only. Always current. Updated each session.
tests/           : All test files. pytest convention. 0 failing 0 skipped invariant.
openagent/       : Source package. One module per responsibility.

## INVARIANTS
test_floor       : 0 failing, 0 skipped — enforced on every directive
scope            : Directives list explicit file scope — no implicit modification
phases           : No phase begins without passing floor from previous phase
adr_003          : fastmcp never moves to core dependencies
stubs            : Raise NotImplementedError — never return None silently

## FILE_REGISTRY
docs/state/current.md   | Project state  | both  | every session
docs/adr/ADR-NNN.md     | Decision       | human | on decision
AGENT_CONTRACT.md       | This file      | human | on structural change
```

---

### 2.8 `docs/state/current.md`

```markdown
phase: 'Phase 1 — Repo Scaffold'
certified_floor: 0/0/0
what_is_built: 'Repo structure, pyproject.toml, stubs, ADRs 001-003, AGENT_CONTRACT.md'
what_is_next: 'Phase 2 — Scanner + Assessor implementation'
open_questions:
  - 'Which OpenRouter models for cheap/capable stage routing?'
  - 'SOUL.md interview — run openagent init on first use or bundled?'
```

---

### 2.9 `.gitignore`

```
.venv/
__pycache__/
*.pyc
.env
dist/
*.egg-info/
logs/
.pytest_cache/
```

### 2.10 `.env.example`

```
# Required for analyze command (Phase 2)
OPENROUTER_API_KEY=your_key_here

# Optional: cheap model override (default: deepseek/deepseek-chat)
OPENAGENT_CHEAP_MODEL=

# Optional: capable model override (default: anthropic/claude-haiku-4-5)
OPENAGENT_CAPABLE_MODEL=
```

---

## §3 Test Anchors

No logic to test yet. Scaffold tests verify structure only.

| Test | File | Behaviour |
|---|---|---|
| `test_package_imports` | `test_scaffold.py` | `import openagent` succeeds |
| `test_version_string` | `test_scaffold.py` | `openagent.__version__ == "0.3.0"` |
| `test_cli_importable` | `test_scaffold.py` | `from openagent.cli import cli` succeeds |
| `test_scanner_stub_raises` | `test_scaffold.py` | `Scanner().scan(".")` raises `NotImplementedError` |
| `test_assessor_stub_raises` | `test_scaffold.py` | `Assessor().assess({})` raises `NotImplementedError` |
| `test_writer_stub_raises` | `test_scaffold.py` | `DirectiveWriter().write({}, "", {})` raises `NotImplementedError` |
| `test_server_no_fastmcp_raises` | `test_scaffold.py` | `main()` raises `ImportError` when fastmcp absent (mock import) |
| `test_agent_contract_exists` | `test_scaffold.py` | `Path("AGENT_CONTRACT.md").exists()` is True |
| `test_adr_directory_exists` | `test_scaffold.py` | `Path("docs/adr").is_dir()` is True |
| `test_three_adrs_present` | `test_scaffold.py` | ADR-001, ADR-002, ADR-003 all exist |

**Target: 10 passing, 0 failing, 0 skipped**

---

## §4 Completion Criteria

- [ ] `uv init` run, `.venv` created, `uv sync` passes
- [ ] pytest: **10 passing, 0 failing, 0 skipped** — raw terminal output pasted
- [ ] `openagent --version` outputs `0.3.0`
- [ ] All stub files exist and raise `NotImplementedError` on use
- [ ] `server.py` import guard verified: `python -c "from openagent.server import main; main()"` raises `ImportError` with install instructions (not fastmcp ImportError)
- [ ] GitHub repo `rfd62794/OpenAgentMCP` created — public, MIT
- [ ] Initial commit pushed
- [ ] `docs/state/current.md` written

---

## §5 Quick Reference

| Key | Value |
|---|---|
| PyPI name | `openagent-directive` (unchanged) |
| Version | `0.3.0` |
| New repo | `C:\Github\OpenAgentMCP` |
| GitHub | `github.com/rfd62794/OpenAgentMCP` |
| License | MIT |
| Target floor | 10/0/0 |
| fastmcp | Optional — `[mcp]` extra only, never core |
| Old repo | `C:\Github\OpenAgent` — archive only, do not modify |
| Phase 2 | Scanner + Assessor implementation |
| Phase 3 | Writer + ModelRouter + CLI `analyze` command |
| Phase 4 | MCP server + `serve` command |
