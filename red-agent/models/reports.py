"""Pydantic models for red team report structures."""

import re

from pydantic import BaseModel, Field, field_validator

from .enums import AnalysisMode, Severity
from .findings import Finding, Pattern, RiskCategory


class RiskOverview(BaseModel):
    """Overview of risk assessment."""

    overall_risk_level: Severity
    analysis_confidence: str | None = None
    categories: list[RiskCategory] = Field(default_factory=list)

    @field_validator("analysis_confidence")
    @classmethod
    def validate_confidence_format(cls, v: str | None) -> str | None:
        """Validate confidence is a percentage string if provided."""
        if v is not None and not re.match(r"^\d{1,3}%$", v):
            msg = f"Confidence '{v}' must be a percentage (e.g., '85%')"
            raise ValueError(msg)
        return v


class FindingsByLevel(BaseModel):
    """Findings organized by severity level."""

    critical: list[Finding] = Field(default_factory=list)
    high: list[Finding] = Field(default_factory=list)
    medium: list[Finding] = Field(default_factory=list)
    low: list[Finding] = Field(default_factory=list)


class Recommendations(BaseModel):
    """Recommendations organized by timeframe."""

    immediate: list[str] = Field(default_factory=list)
    short_term: list[str] = Field(default_factory=list)
    long_term: list[str] = Field(default_factory=list)


class Limitations(BaseModel):
    """Limitations and caveats of the analysis."""

    scope: str | None = None
    coverage: str | None = None
    confidence_note: str | None = None
    temporal_note: str | None = None


class Methodology(BaseModel):
    """Methodology used for the analysis."""

    mode: AnalysisMode = AnalysisMode.STANDARD
    grounding_enabled: bool = True
    categories_analyzed: list[str] = Field(default_factory=list)


class RedTeamReport(BaseModel):
    """Complete red team analysis report."""

    executive_summary: str = Field(min_length=50)
    risk_overview: RiskOverview
    findings: FindingsByLevel
    patterns_detected: list[Pattern] = Field(default_factory=list)
    recommendations: Recommendations | None = None
    limitations: Limitations | None = None
    methodology: Methodology | None = None
