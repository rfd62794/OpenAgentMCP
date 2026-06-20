"""
Writer — Phase 3.

Consumes analysis from Assessor and produces Markdown directive
using a capable model. Single model call, Markdown output.
"""


class DirectiveWriter:
    """Writes directives based on assessment analysis."""

    def write(self, analysis: dict, repo_path: str, context: dict) -> str:
        """Write directive based on analysis. Not yet implemented."""
        raise NotImplementedError("DirectiveWriter not yet implemented — Phase 3.")
