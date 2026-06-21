updated: 2026-06-21
agent: OpenAgentMCP v0.3
phase: Phase 6 — GitContextReader
certified_floor: 90/0/0
test_floor: 90 passing, 0 failing, 0 skipped
what_is_built: SSE transport (--transport sse), port option (--port), ADR-005, docs/nssm.md, README rewrite, transport tests, PyPI v0.3.0 published, GitContextReader (git_context.py), Assessor git context merge
what_is_next: Phase 7 — Local Repo Collector Integration

open_questions:
- Which OpenRouter models for cheap/capable stage routing?
- SOUL.md interview — run openagent init on first use or bundled?

recent_decisions:
- Two transport modes locked: stdio for Claude Desktop, SSE for NSSM
- Port 8008 locked as SSE default
- PyPI v0.3.0 published: https://pypi.org/project/openagent-directive/0.3.0/
- GitContextReader added as separate module (not in Scanner — preserves pure stdlib contract)
- Assessor merges git context before prompt build; degrades gracefully when git unavailable

directive_generated: 2026-06-21
