"""Mock PAL (Prompt-Agent-Loop) for testing PAL optional integration.

This module provides test fixtures for mocking PAL availability scenarios.
"""

from contextlib import contextmanager
from typing import Any


@contextmanager
def mock_pal_unavailable():
    """Mock PAL as unavailable (MCP not installed).

    Use this to test that workflows gracefully degrade when PAL is unavailable.

    Example:
        with mock_pal_unavailable():
            result = run_redteam_analysis()
            assert result.pal_available is False
    """
    # TODO: Implement mock when integration tests are added
    # For now, this is a placeholder for future test implementation
    yield


@contextmanager
def mock_pal_available(models: list[str] | None = None):
    """Mock PAL as available with specified models.

    Args:
        models: List of model names to return. Defaults to ["gpt-4o", "gemini-pro"].

    Example:
        with mock_pal_available(models=["gpt-4o"]):
            result = run_redteam_analysis()
            assert result.pal_available is True
            assert "gpt-4o" in result.pal_models
    """
    if models is None:
        models = ["gpt-4o", "gemini-pro"]
    # TODO: Implement mock when integration tests are added
    yield


@contextmanager
def mock_pal_timeout():
    """Mock PAL availability check timing out.

    Use this to test that workflows continue when PAL check exceeds timeout.

    Example:
        with mock_pal_timeout():
            result = run_redteam_analysis()
            assert result.pal_available is False  # Timeout results in unavailable
    """
    # TODO: Implement mock when integration tests are added
    yield


@contextmanager
def mock_pal_failure():
    """Mock PAL enhancement failing mid-analysis.

    Use this to test that workflows complete even if PAL enhancement fails.

    Example:
        with mock_pal_failure():
            result = run_redteam_pr_analysis()
            assert result.pal_enhanced is False  # Enhancement failed
            assert result.findings  # But analysis completed
    """
    # TODO: Implement mock when integration tests are added
    yield


class MockPAL:
    """Configurable PAL mock for testing.

    This class provides a flexible mock for PAL integration testing.

    Args:
        available: Whether PAL should be available. Defaults to True.
        models: List of model names to return. Defaults to ["gpt-4o", "gemini-pro"].
        timeout: Whether availability check should timeout. Defaults to False.
        enhancement_fails: Whether PAL enhancement should fail. Defaults to False.

    Example:
        # Mock PAL unavailable
        with MockPAL(available=False):
            result = run_redteam_analysis()
            assert result.pal_available is False

        # Mock PAL with specific models
        with MockPAL(available=True, models=["gpt-4o"]):
            result = run_redteam_analysis()
            assert "gpt-4o" in result.pal_models

        # Mock PAL timeout
        with MockPAL(timeout=True):
            result = run_redteam_analysis()
            assert result.pal_available is False

        # Mock PAL enhancement failure
        with MockPAL(available=True, enhancement_fails=True):
            result = run_redteam_pr_analysis()
            assert result.pal_available is True  # Check passed
            assert result.pal_enhanced is False  # But enhancement failed
    """

    def __init__(
        self,
        available: bool = True,
        models: list[str] | None = None,
        timeout: bool = False,
        enhancement_fails: bool = False,
    ) -> None:
        """Initialize MockPAL."""
        self.available = available
        self.models = models if models is not None else ["gpt-4o", "gemini-pro"]
        self.timeout = timeout
        self.enhancement_fails = enhancement_fails

    def __enter__(self) -> "MockPAL":
        """Enter context manager."""
        # TODO: Implement mock when integration tests are added
        # This would mock the mcp__pal__listmodels tool and PAL enhancement agents
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        # TODO: Implement mock cleanup when integration tests are added
        pass


def create_pal_check_output(available: bool = True, models: list[str] | None = None) -> dict[str, Any]:
    """Create mock output for pal-availability-checker agent.

    Args:
        available: Whether PAL is available.
        models: List of models. Defaults to ["gpt-4o", "gemini-pro"] if available.

    Returns:
        Dictionary representing pal-availability-checker YAML output.

    Example:
        >>> output = create_pal_check_output(available=True)
        >>> output["pal_check"]["available"]
        True
        >>> output["pal_check"]["models"][0]["name"]
        'gpt-4o'
    """
    if models is None:
        models = ["gpt-4o", "gemini-pro"] if available else []

    if not available:
        return {
            "pal_check": {
                "available": False,
                "reason": "MCP tool mcp__pal__listmodels not found",
            }
        }

    return {
        "pal_check": {
            "available": True,
            "models": [
                {
                    "name": model,
                    "provider": "openai" if "gpt" in model else "google",
                }
                for model in models
            ],
        }
    }


def create_pal_enhanced_output(
    base_output: dict[str, Any],
    pal_enhanced: bool = True,
    adjustments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Add PAL enhancement fields to agent output.

    Args:
        base_output: Base agent output dictionary.
        pal_enhanced: Whether PAL enhancement was applied.
        adjustments: List of PAL adjustments (for diff-analyzer).

    Returns:
        Output with PAL enhancement fields added.

    Example:
        >>> base = {"file_analysis": [...]}
        >>> enhanced = create_pal_enhanced_output(base, pal_enhanced=True)
        >>> enhanced["pal_enhanced"]
        True
    """
    output = base_output.copy()
    output["pal_enhanced"] = pal_enhanced

    if pal_enhanced and adjustments:
        output["pal_adjustments"] = adjustments

    return output
