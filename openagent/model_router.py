"""
ModelRouter — Phase 3.

Routes model requests to appropriate providers (OpenRouter primary).
Handles cheap vs capable model selection based on stage.
"""


class ModelRouter:
    """Routes model requests to appropriate providers."""

    def route(self, stage: str, prompt: str) -> str:
        """Route request to appropriate model for stage. Not yet implemented."""
        raise NotImplementedError("ModelRouter not yet implemented — Phase 3.")
