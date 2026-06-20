updated: 2026-06-20
agent: OpenAgentMCP v0.3
phase: Phase 5 — SSE Transport + NSSM + PyPI Publish
test_floor: 77 passing, 0 failing, 0 skipped
what_is_built: SSE transport (--transport sse), port option (--port), ADR-005, docs/nssm.md, README rewrite, transport tests, PyPI v0.3.0 published
what_is_next: NSSM install on Nitro

open_questions:
- Which OpenRouter models for cheap/capable stage routing?
- SOUL.md interview — run openagent init on first use or bundled?

recent_decisions:
- Two transport modes locked: stdio for Claude Desktop, SSE for NSSM
- Port 8008 locked as SSE default
- PyPI v0.3.0 published: https://pypi.org/project/openagent-directive/0.3.0/

directive_generated: 2026-06-20 18:33
