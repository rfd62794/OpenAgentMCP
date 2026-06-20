updated: 2026-06-20
agent: OpenAgentMCP v0.3
phase: Phase 5 — SSE Transport + NSSM + PyPI Publish
test_floor: 77 passing, 0 failing, 0 skipped
what_is_built: SSE transport (--transport sse), port option (--port), ADR-005, docs/nssm.md, README rewrite, transport tests
what_is_next: NSSM install on Nitro + PyPI publish v0.3.0 (token issue)

open_questions:
- Which OpenRouter models for cheap/capable stage routing?
- SOUL.md interview — run openagent init on first use or bundled?

recent_decisions:
- Two transport modes locked: stdio for Claude Desktop, SSE for NSSM
- Port 8008 locked as SSE default

directive_generated: 2026-06-20 18:29
