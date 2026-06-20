# OpenAgentMCP

Repo-aware directive generator with optional MCP server.

## About

OpenAgentMCP is a clean rebuild of `openagent-directive` (v0.3.0). It generates structured directives for AI agents by analyzing repository structure and producing actionable guidance.

## Installation

```bash
# Core CLI only
pip install openagent-directive

# With MCP server support
pip install openagent-directive[mcp]
```

## Quick Start

```bash
openagent --version
```

## Architecture

OpenAgentMCP follows a two-stage pipeline architecture:

1. **Scanner** — Pure stdlib, scans repository structure
2. **Assessor** — Cheap model analysis, structured JSON output
3. **Writer** — Capable model, Markdown directive output

No framework. No orchestration layer. Direct function calls between stages.

## License

MIT

## Links

- [GitHub](https://github.com/rfd62794/OpenAgentMCP)
- [Issues](https://github.com/rfd62794/OpenAgentMCP/issues)
