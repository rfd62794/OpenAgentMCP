"""
ScopeGuard — Phase 2.

Enforces file scope boundaries. Ensures directives only modify
files explicitly listed in their scope. No silent modifications.
"""


class ScopeGuard:
    """Guards file scope boundaries for directives."""

    def validate_scope(self, directive: dict, repo_path: str) -> bool:
        """Validate directive scope against repo. Not yet implemented."""
        raise NotImplementedError("ScopeGuard not yet implemented — Phase 2.")
