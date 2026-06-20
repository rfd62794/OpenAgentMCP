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
