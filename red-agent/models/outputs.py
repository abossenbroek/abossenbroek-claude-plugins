"""Pydantic models for sub-agent output structures."""

import re

from pydantic import BaseModel, Field, field_validator

from .enums import RiskCategoryName

# Valid severity levels for attacker findings
ATTACKER_SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


# =============================================================================
# Nested models for AttackerFinding
# =============================================================================


class FindingTarget(BaseModel):
    """Target of an attacker finding."""

    claim_id: str | None = None
    claim_text: str | None = None
    message_num: int | None = None


class AttackApplied(BaseModel):
    """Attack style and probe used."""

    style: str
    probe: str


class FindingEvidence(BaseModel):
    """Evidence for a finding."""

    type: str
    description: str | None = None
    quote: str | None = None
    assumption: str | None = None
    why_problematic: str | None = None


class FindingImpact(BaseModel):
    """Impact of a finding."""

    if_exploited: str | None = None
    if_assumption_fails: str | None = None
    affected_claims: list[str] = Field(default_factory=list)
    likelihood: str | None = None


class AttackerFinding(BaseModel):
    """A finding from an attacker sub-agent."""

    # Required fields (existing)
    id: str
    severity: str
    title: str
    confidence: float | str

    # New required fields (strict validation)
    category: str
    target: FindingTarget
    evidence: FindingEvidence
    attack_applied: AttackApplied
    impact: FindingImpact
    recommendation: str = Field(min_length=10)

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


class DetectedPattern(BaseModel):
    """A pattern detected across findings."""

    pattern: str
    instances: int = Field(ge=1, default=1)
    description: str
    systemic_recommendation: str | None = None


class SeverityCounts(BaseModel):
    """Counts by severity level."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class AttackSummary(BaseModel):
    """Summary of attack results."""

    total_findings: int = 0
    by_severity: SeverityCounts = Field(default_factory=SeverityCounts)
    highest_risk_claim: str | None = None
    primary_weakness: str | None = None


class AttackResults(BaseModel):
    """Results from an attacker sub-agent."""

    attack_type: str
    findings: list[AttackerFinding] = Field(default_factory=list)
    categories_probed: list[str] = Field(default_factory=list)
    # New required fields
    patterns_detected: list[DetectedPattern] = Field(default_factory=list)
    summary: AttackSummary

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


# =============================================================================
# Nested models for GroundingAssessment
# =============================================================================


class EvidenceReview(BaseModel):
    """Evidence review section of grounding assessment."""

    evidence_exists: bool
    evidence_accurate: bool | str = True  # true, false, "partial"
    evidence_sufficient: bool | str = True  # true, false, "partial"


class QuoteVerification(BaseModel):
    """Quote verification for grounding."""

    original_quote: str | None = None
    actual_source: str | None = None
    match_quality: str = "exact"  # exact, close, partial, mismatch, not_found


class InferenceValidity(BaseModel):
    """Inference validity check."""

    valid: bool | str = True  # true, false, "partial"
    reasoning: str | None = None


class GroundingIssue(BaseModel):
    """An issue found during grounding."""

    issue: str
    severity: str = "medium"  # high, medium, low


class GroundingAssessment(BaseModel):
    """Assessment from a grounding sub-agent."""

    finding_id: str
    evidence_strength: float = Field(ge=0.0, le=1.0)
    original_confidence: float = Field(ge=0.0, le=1.0)
    evidence_review: EvidenceReview
    quote_verification: QuoteVerification
    inference_validity: InferenceValidity
    issues_found: list[GroundingIssue] = Field(default_factory=list)
    adjusted_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None


class GroundingResults(BaseModel):
    """Results from a grounding sub-agent."""

    agent: str
    assessments: list[GroundingAssessment] = Field(default_factory=list)


class GroundingOutput(BaseModel):
    """Root structure for grounding sub-agent output."""

    grounding_results: GroundingResults


# =============================================================================
# Context Analysis models
# =============================================================================


class ClaimAnalysis(BaseModel):
    """Analysis of a single claim."""

    claim_id: str
    risk_level: str | None = None
    content: str | None = None
    # New fields
    original_text: str | None = None
    verifiability: str | None = None  # verifiable, partially_verifiable, unverifiable
    risk_factors: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class RiskSurface(BaseModel):
    """Risk surface analysis."""

    areas: list[str] = Field(default_factory=list)
    exposure_level: str | None = None


class DependencyChain(BaseModel):
    """A dependency chain in the graph."""

    root: str
    depends: list[str] = Field(default_factory=list)
    risk_if_root_fails: str | None = None


class DependencyGraph(BaseModel):
    """Dependency graph for claims."""

    roots: list[str] = Field(default_factory=list)
    chains: list[DependencyChain] = Field(default_factory=list)


class ContextAnalysisResults(BaseModel):
    """Results from context analyzer."""

    summary: dict | None = None
    claim_analysis: list[ClaimAnalysis] = Field(default_factory=list)
    reasoning_patterns: list[str] = Field(default_factory=list)
    risk_surface: RiskSurface | None = None
    # New fields
    dependency_graph: DependencyGraph | None = None
    key_observations: list[str] = Field(default_factory=list)


class ContextAnalysisOutput(BaseModel):
    """Root structure for context analysis output."""

    context_analysis: ContextAnalysisResults
