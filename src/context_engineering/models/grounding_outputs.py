"""Pydantic models for grounding sub-agent outputs.

These models define the output schemas for:
- pattern-checker: Verifies SOTA pattern compliance
- token-estimator: Estimates token reduction
- consistency-checker: Checks internal consistency
- risk-assessor: Assesses breaking change risk
"""

from pydantic import BaseModel, ConfigDict, Field

from .enums import PatternType, RiskLevel

# =============================================================================
# Pattern Compliance Models (pattern-checker output)
# =============================================================================


class PatternViolationDetail(BaseModel):
    """A specific pattern violation found."""

    pattern: PatternType
    violation: str
    location: str | None = None
    suggestion: str | None = None


class PatternCompliance(BaseModel):
    """Pattern compliance check for an improvement.

    Output from pattern-checker grounding agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    improvement_id: str
    pattern_compliant: bool
    patterns_checked: list[PatternType] = Field(default_factory=list)
    violations: list[PatternViolationDetail] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


# =============================================================================
# Token Estimate Models (token-estimator output)
# =============================================================================


class TokenBreakdown(BaseModel):
    """Breakdown of tokens by component."""

    component: str
    before: int
    after: int
    reduction: int
    reduction_percent: float = Field(ge=-100.0, le=100.0)


class TokenEstimate(BaseModel):
    """Token reduction estimate for an improvement.

    Output from token-estimator grounding agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    improvement_id: str
    before_tokens: int = Field(ge=0)
    after_tokens: int = Field(ge=0)
    reduction_tokens: int = 0
    reduction_percent: float = Field(default=0.0, ge=-100.0, le=100.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    # Optional breakdown by component
    breakdown: list[TokenBreakdown] = Field(default_factory=list)

    # Estimation method and notes
    method: str | None = None  # "tiktoken", "heuristic", "sample"
    notes: str | None = None


# =============================================================================
# Consistency Check Models (consistency-checker output)
# =============================================================================


class ConflictDetail(BaseModel):
    """Detail about a conflict between improvements."""

    with_improvement_id: str
    conflict_type: str  # "overwrite", "dependency", "incompatible"
    description: str
    resolution: str | None = None


class DependencyDetail(BaseModel):
    """Detail about a dependency on another improvement."""

    requires_improvement_id: str
    reason: str
    is_hard_dependency: bool = True  # False = nice to have


class ConsistencyCheck(BaseModel):
    """Consistency check for an improvement.

    Output from consistency-checker grounding agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    improvement_id: str
    is_internally_consistent: bool
    conflicts_with: list[ConflictDetail] = Field(default_factory=list)
    depends_on: list[DependencyDetail] = Field(default_factory=list)
    consistency_issues: list[str] = Field(default_factory=list)

    # Recommended order if there are dependencies
    recommended_order: int | None = None


# =============================================================================
# Risk Assessment Models (risk-assessor output)
# =============================================================================


class BreakingChange(BaseModel):
    """A potential breaking change."""

    description: str
    affected_component: str
    mitigation: str | None = None


class RiskAssessment(BaseModel):
    """Risk assessment for an improvement.

    Output from risk-assessor grounding agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    improvement_id: str
    risk_level: RiskLevel
    breaking_changes: list[BreakingChange] = Field(default_factory=list)
    rollback_possible: bool = True
    rollback_complexity: str | None = None  # "simple", "moderate", "complex"

    # Mitigation
    mitigation_strategy: str | None = None
    testing_required: list[str] = Field(default_factory=list)

    # Confidence and notes
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    notes: str | None = None


# =============================================================================
# Combined Grounding Output
# =============================================================================


class GroundedImprovement(BaseModel):
    """An improvement with all grounding results attached.

    Used by synthesizer to generate final report.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    improvement_id: str
    improvement_description: str
    improvement_type: str

    # Grounding results (optional - depends on severity batching)
    pattern_compliance: PatternCompliance | None = None
    token_estimate: TokenEstimate | None = None
    consistency_check: ConsistencyCheck | None = None
    risk_assessment: RiskAssessment | None = None

    # Overall assessment
    is_approved: bool = True
    approval_notes: str | None = None
