updated: 2026-06-21
agent: OpenAgentMCP v0.3
phase: Phase 8 — RepoScanner
certified_floor: 115/0/0
test_floor: 115 passing, 0 failing, 0 skipped
what_is_built: SSE transport, GitContextReader, TestCommandResolver, AsyncTestRunner, TestLogReader, RepoScanner, run_tests MCP tool, get_test_log MCP tool, list_repos MCP tool, ADR-006
what_is_next: Phase 9 — repos.db Cache + Collectors Integration

open_questions:
- Which OpenRouter models for cheap/capable stage routing?
- SOUL.md interview — run openagent init on first use or bundled?

recent_decisions:
- Two transport modes locked: stdio for Claude Desktop, SSE for NSSM
- Port 8008 locked as SSE default
- PyPI v0.3.0 published: https://pypi.org/project/openagent-directive/0.3.0/
- GitContextReader added as separate module (not in Scanner)
- shell=True locked for test execution (ADR-006)
- TestCommandResolver resolution order: AGENT_CONTRACT.md → detection → None
- Log: docs/state/openagent_test.log, PID: docs/state/openagent_test.pid

directive_generated: 2026-06-21
