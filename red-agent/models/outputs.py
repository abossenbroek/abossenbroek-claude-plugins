"""Pydantic models for sub-agent output structures."""

import re

from pydantic import BaseModel, Field, field_validator

from .enums import RiskCategoryName

# Valid severity levels for attacker findings
ATTACKER_SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


class AttackerFinding(BaseModel):
    """A finding from an attacker sub-agent."""

    id: str
    severity: str
    title: str
    confidence: float | str

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate finding ID matches XX-NNN or XXX-NNN format."""
        if not re.match(r"^[A-Z]{2,3}-\d{3}$", v):
            msg = f"Finding ID '{v}' must match XX-NNN or XXX-NNN format (e.g., RF-001)"
            raise ValueError(msg)
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is a known level."""
        if v not in ATTACKER_SEVERITY_LEVELS:
            msg = f"Severity '{v}' must be one of {ATTACKER_SEVERITY_LEVELS}"
            raise ValueError(msg)
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float | str) -> float | str:
        """Validate confidence is either a float 0-1 or percentage string."""
        if isinstance(v, float | int):
            if not 0.0 <= v <= 1.0:
                msg = f"Confidence {v} must be between 0.0 and 1.0"
                raise ValueError(msg)
        elif isinstance(v, str) and not v.endswith("%"):
            msg = f"String confidence '{v}' should be numeric or end with %"
            raise ValueError(msg)
        return v


class AttackResults(BaseModel):
    """Results from an attacker sub-agent."""

    attack_type: str
    findings: list[AttackerFinding] = Field(default_factory=list)
    categories_probed: list[str] = Field(default_factory=list)

    @field_validator("categories_probed")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        """Warn if unknown categories are present."""
        valid_categories = {cat.value for cat in RiskCategoryName}
        for cat in v:
            if cat not in valid_categories:
                pass  # Allow unknown categories but could log warning
        return v


class AttackerOutput(BaseModel):
    """Root structure for attacker sub-agent output."""

    attack_results: AttackResults


class GroundingAssessment(BaseModel):
    """Assessment from a grounding sub-agent."""

    finding_id: str
    evidence_strength: float = Field(ge=0.0, le=1.0)
    adjusted_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None


class GroundingResults(BaseModel):
    """Results from a grounding sub-agent."""

    agent: str
    assessments: list[GroundingAssessment] = Field(default_factory=list)


class GroundingOutput(BaseModel):
    """Root structure for grounding sub-agent output."""

    grounding_results: GroundingResults


class ClaimAnalysis(BaseModel):
    """Analysis of a single claim."""

    claim_id: str
    risk_level: str | None = None
    content: str | None = None


class RiskSurface(BaseModel):
    """Risk surface analysis."""

    areas: list[str] = Field(default_factory=list)
    exposure_level: str | None = None


class ContextAnalysisResults(BaseModel):
    """Results from context analyzer."""

    summary: dict | None = None
    claim_analysis: list[ClaimAnalysis] = Field(default_factory=list)
    reasoning_patterns: list[str] = Field(default_factory=list)
    risk_surface: RiskSurface | None = None


class ContextAnalysisOutput(BaseModel):
    """Root structure for context analysis output."""

    context_analysis: ContextAnalysisResults
