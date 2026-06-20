# OpenAgentMCP — Phase 5 Directive: SSE Transport + NSSM + PyPI Publish

*June 2026 | Read fully before executing anything.*

---

> ⛔ **STOP:** Run pytest before touching any file.
> Must report **71 passing, 0 failing, 0 skipped**.
> If count differs, stop and report — do not proceed.

---

## §0 Context

**What exists:**
- Phase 4 certified at 71/0/0
- `serve` command runs stdio only — Claude Desktop subprocess model
- No persistent service mode — can't run under NSSM
- README is placeholder — not useful as a public-facing doc
- v0.3.0 not yet published to PyPI

**What Phase 5 delivers:**
1. `serve` command gains `--transport` and `--port` options
2. `server.main()` accepts transport + port, routes to FastMCP accordingly
3. `docs/adr/ADR-005.md` — two transport modes locked in
4. `docs/nssm.md` — NSSM setup instructions for Nitro
5. `README.md` — public-facing, useful, honest
6. PyPI publish v0.3.0

**What is NOT in scope:**
- HTTP transport (Streamable HTTP) — SSE only for NSSM
- OAuth or authentication
- Any changes to Scanner, Assessor, Writer, ScopeGuard, StateWriter, ModelRouter
- New MCP tools

---

## §1 Scope Statement

| File | Status | Action |
|---|---|---|
| `openagent/server.py` | Modify | `main()` accepts transport + port |
| `openagent/cli.py` | Modify | `serve` adds `--transport` and `--port` options |
| `docs/adr/ADR-005.md` | New | Two transport modes — stdio vs SSE |
| `docs/nssm.md` | New | NSSM setup for Nitro |
| `README.md` | Modify | Public-facing rewrite |
| `tests/test_server.py` | Modify | Add transport option tests |
| `tests/test_cli.py` | Modify | Add serve transport option tests |

**Read-only — do not touch:**
All existing source modules, all ADRs 001-004, `AGENT_CONTRACT.md`, `SOUL.md`

---

## §2 Implementation

### 2.1 `docs/adr/ADR-005.md`

Write before touching any code.

```markdown
# ADR-005: Two Transport Modes — Stdio and SSE

## Status
Accepted

## Context
The MCP server needs to serve two distinct clients:
1. Claude Desktop — expects stdio subprocess launched on demand
2. TOBOR, RFD_IT_Command, other local services — need a persistent SSE endpoint

A single transport mode cannot serve both.

## Decision
`openagent serve` defaults to stdio (Claude Desktop).
`openagent serve --transport sse --port 8008` runs persistent SSE (NSSM).

`server.main(transport, port)` passes transport and port to FastMCP.
FastMCP handles the protocol difference internally.

Default port for SSE: 8008.
NSSM service name: OpenAgentMCP.

## Consequences
- stdio mode: launched by Claude Desktop, exits when Desktop closes. No NSSM.
- SSE mode: persistent NSSM service on :8008. Claude Desktop uses stdio config,
  not the SSE endpoint.
- No HTTP (Streamable HTTP) transport without a superseding ADR.
- Port 8008 is the locked default. Change requires a new ADR.
```

---

### 2.2 `openagent/server.py` — update `main()`

Change the signature and routing:

```python
def main(transport: str = "stdio", port: int = 8008) -> None:
    """Entry point for MCP server. Requires [mcp] extra."""
    _require_mcp()
    mcp = _build_server()
    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()
```

> ⚠️ RULE: Only two valid transport values: `"stdio"` and `"sse"`. Any other value defaults to stdio. Do not add `"http"` or any other transport.

> ⚠️ RULE: `port` is only used when `transport="sse"`. Ignored for stdio.

---

### 2.3 `openagent/cli.py` — update `serve` command

```python
@cli.command()
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "sse"]),
    help="Transport mode. stdio for Claude Desktop, sse for NSSM service.",
)
@click.option(
    "--port",
    default=8008,
    type=int,
    help="Port for SSE transport (default: 8008). Ignored for stdio.",
)
def serve(transport: str, port: int):
    """
    Start the MCP server.

    stdio mode (default) — for Claude Desktop:
        openagent serve

    SSE mode — for NSSM persistent service:
        openagent serve --transport sse --port 8008

    Claude Desktop config (stdio):
        {
          "openagent": {
            "command": "uv",
            "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"],
            "cwd": "C:\\\\Github\\\\OpenAgentMCP"
          }
        }
    """
    from openagent.server import main
    main(transport=transport, port=port)
```

---

### 2.4 `docs/nssm.md`

```markdown
# NSSM Setup — OpenAgentMCP on Nitro

Runs OpenAgentMCP as a persistent SSE service on port 8008.
TOBOR and other local services connect via http://localhost:8008/sse.

## Prerequisites
- uv installed at C:\Users\cheat\.local\bin\uv.exe
- .env file at C:\Github\OpenAgentMCP\.env with OPENROUTER_API_KEY and OPENAGENT_BASE_URL
- nssm available in PATH

## Install

```powershell
nssm install OpenAgentMCP "C:\Users\cheat\.local\bin\uv.exe"
nssm set OpenAgentMCP AppParameters "run --project C:\Github\OpenAgentMCP openagent serve --transport sse --port 8008"
nssm set OpenAgentMCP AppDirectory C:\Github\OpenAgentMCP
nssm set OpenAgentMCP AppStdout C:\Github\OpenAgentMCP\logs\service.log
nssm set OpenAgentMCP AppStderr C:\Github\OpenAgentMCP\logs\service.log
nssm set OpenAgentMCP AppRotateFiles 1
nssm start OpenAgentMCP
```

## Verify

```powershell
nssm status OpenAgentMCP   # should show SERVICE_RUNNING
curl http://localhost:8008  # should return FastMCP response
```

## Connect from TOBOR / other services

Use mcp-remote or direct SSE client pointed at:
http://localhost:8008/sse

## Claude Desktop (stdio — separate from NSSM)

Claude Desktop uses stdio transport, not the NSSM SSE service.
Add to claude_desktop_config.json:
```json
{
  "openagent": {
    "command": "uv",
    "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"],
    "cwd": "C:\\Github\\OpenAgentMCP"
  }
}
```

## Restart after code changes

```powershell
nssm restart OpenAgentMCP
```
```

---

### 2.5 `README.md` — public rewrite

```markdown
# OpenAgentMCP

Repo-aware directive generator with optional MCP server.

Reads your repository's actual state — file tree, current phase, test floor — 
and generates structured directives for AI coding agents. Built on a two-stage 
pipeline: cheap model assesses the repo, capable model writes the directive.

## Install

```bash
pip install openagent-directive          # CLI only
pip install openagent-directive[mcp]     # CLI + MCP server
```

## Usage

```bash
# Initialize your architect profile (one-time)
openagent init

# Generate a directive
openagent analyze /path/to/repo --intent "add pagination to the API"

# Start MCP server for Claude Desktop
openagent serve

# Start persistent SSE service (for NSSM)
openagent serve --transport sse --port 8008
```

## How it works

1. **Scanner** reads the file tree and supporting docs (pure stdlib, no side effects)
2. **Assessor** calls a cheap model to assess repo state → `AssessmentResult`
3. **Writer** calls a capable model to generate the directive
4. **StateWriter** writes `docs/state/current.md` atomically

## Model routing

By default routes to OpenRouter. Point at your own router via env var:

```
OPENAGENT_BASE_URL=http://localhost:8005/v1  # RFD_Model_Router or compatible
OPENROUTER_API_KEY=your_key                  # not needed for local routing
```

## MCP tools

When running as MCP server, two tools are available:

- `analyze_repo(repo_path, intent)` — full pipeline, writes state
- `assess_repo(repo_path)` — scan + assess only, read-only

## Claude Desktop config

```json
{
  "mcpServers": {
    "openagent": {
      "command": "uv",
      "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"],
      "cwd": "/path/to/OpenAgentMCP"
    }
  }
}
```

## Architecture

```
Scanner (stdlib) → Assessor (cheap model) → Writer (capable model)
                                          → ScopeGuard (pure logic)
                                          → StateWriter (stdlib)
```

Two-stage routing: cheap model for repo assessment, capable model for directive
generation. Both configurable via `OPENAGENT_CHEAP_MODEL` and `OPENAGENT_CAPABLE_MODEL`.

## License

MIT
```

---

## §3 Test Anchors

| Test | File | Behaviour |
|---|---|---|
| `test_main_stdio_calls_mcp_run_no_args` | `test_server.py` | `main(transport="stdio")` → `mcp.run()` called without transport arg |
| `test_main_sse_calls_mcp_run_with_transport` | `test_server.py` | `main(transport="sse", port=8008)` → `mcp.run(transport="sse", port=8008)` |
| `test_main_unknown_transport_defaults_stdio` | `test_server.py` | `main(transport="http")` → `mcp.run()` called without transport arg |
| `test_serve_command_default_transport` | `test_cli.py` | `openagent serve` → main called with transport="stdio" |
| `test_serve_command_sse_transport` | `test_cli.py` | `openagent serve --transport sse` → main called with transport="sse" |
| `test_serve_command_custom_port` | `test_cli.py` | `openagent serve --transport sse --port 9000` → main called with port=9000 |

**Target: 77 passing, 0 failing, 0 skipped** (71 existing + 6 new)

---

## §4 Completion Criteria

- [ ] pytest: **77 passing, 0 failing, 0 skipped** — raw terminal output pasted
- [ ] `openagent serve --help` shows `--transport` and `--port` options
- [ ] `ADR-005.md` written to `docs/adr/`
- [ ] `docs/nssm.md` written with correct Nitro paths
- [ ] `README.md` rewritten — public-facing, accurate
- [ ] PyPI publish: `uv build && uv publish` — paste confirmation output
- [ ] `docs/state/current.md` updated: phase 5, floor 77/0/0, next = NSSM install + Claude Desktop config

---

## §5 Quick Reference

| Key | Value |
|---|---|
| Baseline floor | 71/0/0 |
| Target floor | 77/0/0 |
| SSE default port | 8008 |
| NSSM service name | OpenAgentMCP |
| stdio — for | Claude Desktop (subprocess, on-demand) |
| SSE — for | NSSM persistent service, TOBOR, RFD_IT_Command |
| PyPI name | openagent-directive |
| PyPI version | 0.3.0 |
| uv path (Nitro) | C:\Users\cheat\.local\bin\uv.exe |
| ADR-005 | Two transports locked — no HTTP without superseding ADR |
