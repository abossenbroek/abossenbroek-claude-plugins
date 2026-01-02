"""Pydantic models for findings and related structures."""

import re

from pydantic import BaseModel, Field, field_validator

from .enums import FindingSeverity, RiskCategoryName, Severity
from .validators import validate_finding_id


class Evidence(BaseModel):
    """Evidence supporting a finding."""

    quote: str
    source: str
    message_num: int | None = None


class GroundingNotes(BaseModel):
    """Grounding assessment for a finding."""

    evidence_strength: float = Field(ge=0.0, le=1.0)
    notes: str | None = None


class Finding(BaseModel):
    """A single finding from red team analysis."""

    id: str
    category: str
    severity: FindingSeverity
    title: str = Field(min_length=10)
    confidence: str
    evidence: Evidence | None = None
    issue: str | None = None
    probing_question: str | None = None
    recommendation: str | None = None
    grounding_notes: GroundingNotes | None = None

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate finding ID matches XX-NNN or XXX-NNN format."""
        return validate_finding_id(v)

    @field_validator("confidence")
    @classmethod
    def validate_confidence_format(cls, v: str) -> str:
        """Validate confidence is a percentage string."""
        if not re.match(r"^\d{1,3}%$", v):
            msg = f"Confidence '{v}' must be a percentage (e.g., '85%')"
            raise ValueError(msg)
        return v


class Pattern(BaseModel):
    """A detected pattern in the analysis."""

    name: str
    description: str
    instances: int = Field(ge=1, default=1)


class RiskCategory(BaseModel):
    """Risk assessment for a category."""

    category: RiskCategoryName
    severity: Severity
    count: int = Field(ge=0, default=0)
    confidence: str | None = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence_format(cls, v: str | None) -> str | None:
        """Validate confidence is a percentage string if provided."""
        if v is not None and not re.match(r"^\d{1,3}%$", v):
            msg = f"Confidence '{v}' must be a percentage (e.g., '85%')"
            raise ValueError(msg)
        return v
