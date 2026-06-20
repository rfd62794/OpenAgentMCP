"""Minimal pytest fixtures for scaffold tests."""
import pytest
from pathlib import Path


@pytest.fixture
def repo_root():
    """Return the repository root directory."""
    return Path(__file__).parent.parent
