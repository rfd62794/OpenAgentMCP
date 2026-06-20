"""
ModelRouter — routes tasks to the appropriate OpenRouter model.
Two task types: 'inventory' (cheap) and 'directive' (capable).
Models are env-var overridable.
"""
import os

CHEAP_MODEL_DEFAULT = "deepseek/deepseek-chat-v3-0324"
CAPABLE_MODEL_DEFAULT = "anthropic/claude-haiku-4-5"
FALLBACK_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ModelRouter:
    """Routes task types to OpenRouter model strings."""

    def __init__(self):
        self.base_url = os.getenv("OPENAGENT_BASE_URL", OPENROUTER_BASE_URL)
        self._cheap = os.getenv("OPENAGENT_CHEAP_MODEL", CHEAP_MODEL_DEFAULT)
        self._capable = os.getenv("OPENAGENT_CAPABLE_MODEL", CAPABLE_MODEL_DEFAULT)

    def get_model(self, task_type: str) -> str:
        """Return model string for task_type. Unknown types return fallback."""
        if task_type == "inventory":
            return self._cheap
        if task_type == "directive":
            return self._capable
        return FALLBACK_MODEL
