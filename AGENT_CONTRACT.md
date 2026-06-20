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
