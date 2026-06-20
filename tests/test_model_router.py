"""Tests for openagent.model_router."""
import os
from openagent.model_router import ModelRouter


def test_inventory_returns_cheap_model():
    """get_model("inventory") returns deepseek model string."""
    router = ModelRouter()
    model = router.get_model("inventory")
    assert "deepseek" in model.lower()


def test_directive_returns_capable_model():
    """get_model("directive") returns haiku model string."""
    router = ModelRouter()
    model = router.get_model("directive")
    assert "haiku" in model.lower() or "claude" in model.lower()


def test_unknown_type_returns_fallback():
    """get_model("unknown") returns fallback string."""
    router = ModelRouter()
    model = router.get_model("unknown")
    assert "llama" in model.lower()


def test_env_var_overrides_cheap_model():
    """Set OPENAGENT_CHEAP_MODEL -> returned by get_model("inventory")."""
    os.environ["OPENAGENT_CHEAP_MODEL"] = "custom/cheap-model"
    try:
        router = ModelRouter()
        model = router.get_model("inventory")
        assert model == "custom/cheap-model"
    finally:
        del os.environ["OPENAGENT_CHEAP_MODEL"]


def test_env_var_overrides_capable_model():
    """Set OPENAGENT_CAPABLE_MODEL -> returned by get_model("directive")."""
    os.environ["OPENAGENT_CAPABLE_MODEL"] = "custom/capable-model"
    try:
        router = ModelRouter()
        model = router.get_model("directive")
        assert model == "custom/capable-model"
    finally:
        del os.environ["OPENAGENT_CAPABLE_MODEL"]


def test_base_url_is_openrouter():
    """router.base_url contains "openrouter.ai"."""
    router = ModelRouter()
    assert "openrouter.ai" in router.base_url
