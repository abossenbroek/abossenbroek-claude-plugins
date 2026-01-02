"""Shared validation utilities for Pydantic models."""

import re

# Compiled regex for finding ID validation
FINDING_ID_PATTERN = re.compile(r"^[A-Z]{2,3}-\d{3}$")


def validate_finding_id(v: str) -> str:
    """Validate finding ID matches XX-NNN or XXX-NNN format.

    Args:
        v: The finding ID string to validate

    Returns:
        The validated finding ID

    Raises:
        ValueError: If the ID doesn't match the expected format
    """
    if not FINDING_ID_PATTERN.match(v):
        msg = f"Finding ID '{v}' must match XX-NNN or XXX-NNN format (e.g., RF-001)"
        raise ValueError(msg)
    return v
