"""
Assessor — Phase 2.

Consumes structured inventory from Scanner and produces
analysis using a cheap model. Single model call, structured JSON output.
"""


class Assessor:
    """Assesses repository structure and produces analysis."""

    def assess(self, inventory: dict) -> dict:
        """Assess inventory and return structured analysis. Not yet implemented."""
        raise NotImplementedError("Assessor not yet implemented — Phase 2.")
