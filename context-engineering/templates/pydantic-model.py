"""Pydantic Model Template

Copy and customize this template when creating validation models.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums (define valid values)
# =============================================================================


class ExampleEnum(str, Enum):
    """Example enumeration for constrained string values."""

    VALUE_1 = "VALUE_1"
    VALUE_2 = "VALUE_2"
    VALUE_3 = "VALUE_3"


# =============================================================================
# Nested Models (define reusable structures)
# =============================================================================


class NestedItem(BaseModel):
    """A nested item within the main output."""

    # Required fields (no default)
    id: str
    description: str

    # Optional fields (with default)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    notes: str | None = None


class Summary(BaseModel):
    """Summary statistics."""

    total_items: int = Field(ge=0)
    by_category: dict[str, int] = Field(default_factory=dict)


# =============================================================================
# Main Output Model
# =============================================================================


class ExampleOutput(BaseModel):
    """Main output structure from the sub-agent.

    This is the root output structure that the agent should produce.
    """

    # Strict validation - no extra fields allowed
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # Agent identification
    agent: str

    # Main content
    items: list[NestedItem] = Field(default_factory=list)

    # Summary section
    summary: Summary = Field(default_factory=Summary)

    # Optional observations
    observations: list[str] = Field(default_factory=list)

    # Custom validators
    @field_validator("agent")
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Validate agent name is not empty."""
        if not v.strip():
            msg = "Agent name cannot be empty"
            raise ValueError(msg)
        return v

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v: list[NestedItem]) -> list[NestedItem]:
        """Validate at least one item exists."""
        if not v:
            msg = "At least one item is required"
            raise ValueError(msg)
        return v


# =============================================================================
# Usage Example
# =============================================================================

# To validate output:
#
# import yaml
# from pydantic import ValidationError
#
# yaml_output = """
# agent: example-agent
# items:
#   - id: EX-001
#     description: Example item
#     confidence: 0.9
# summary:
#   total_items: 1
#   by_category:
#     example: 1
# """
#
# try:
#     data = yaml.safe_load(yaml_output)
#     validated = ExampleOutput(**data)
#     print("Valid output!")
# except ValidationError as e:
#     print("Validation errors:")
#     for error in e.errors():
#         print(f"  {error['loc']}: {error['msg']}")
