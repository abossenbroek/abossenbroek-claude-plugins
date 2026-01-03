"""Pydantic models for synthesis sub-agent outputs.

These models define the output schemas for:
- improvement-synthesizer: Generates final improvement report
"""

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# File Change Models
# =============================================================================


class FileDiff(BaseModel):
    """A diff for a single file."""

    before: str | None = None
    after: str | None = None
    diff: str | None = None  # Unified diff format


class FileChange(BaseModel):
    """A file change in the improvement report."""

    file_path: str
    change_type: str  # "modify", "create", "delete"
    description: str
    diff: FileDiff | None = None


# =============================================================================
# Token Metrics Models
# =============================================================================


class TokenMetrics(BaseModel):
    """Token metrics before and after improvements."""

    before: int = Field(default=0, ge=0)
    after: int = Field(default=0, ge=0)
    reduction: int = 0
    reduction_percent: float = Field(default=0.0, ge=-100.0, le=100.0)


# =============================================================================
# Before/After Comparison Models
# =============================================================================


class PatternComplianceMetrics(BaseModel):
    """Pattern compliance before and after."""

    before: float = Field(default=0.0, ge=0.0, le=1.0)  # % compliant
    after: float = Field(default=0.0, ge=0.0, le=1.0)
    improvement: float = Field(default=0.0, ge=-1.0, le=1.0)


class TierCoverageMetrics(BaseModel):
    """Context tier coverage before and after."""

    before: float = Field(default=0.0, ge=0.0, le=1.0)  # % with tier spec
    after: float = Field(default=0.0, ge=0.0, le=1.0)
    improvement: float = Field(default=0.0, ge=-1.0, le=1.0)


class BeforeAfterComparison(BaseModel):
    """Before/after comparison for the improvement report."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    total_tokens: TokenMetrics = Field(default_factory=TokenMetrics)
    pattern_compliance: PatternComplianceMetrics = Field(
        default_factory=PatternComplianceMetrics
    )
    tier_coverage: TierCoverageMetrics = Field(default_factory=TierCoverageMetrics)


# =============================================================================
# Applied Improvement Models
# =============================================================================


class AppliedImprovement(BaseModel):
    """An improvement that was applied."""

    improvement_id: str
    description: str
    files_modified: list[str] = Field(default_factory=list)
    token_reduction: int | None = None
    risk_level: str | None = None


# =============================================================================
# Improvement Report Models (improvement-synthesizer output)
# =============================================================================


class NextStep(BaseModel):
    """A recommended next step."""

    description: str
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    rationale: str | None = None


class ImprovementReport(BaseModel):
    """Final improvement report from improvement-synthesizer.

    This is the root output structure returned to the main session.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # Executive summary
    executive_summary: str

    # Improvements applied
    improvements_applied: list[AppliedImprovement] = Field(default_factory=list)
    improvements_skipped: list[str] = Field(
        default_factory=list
    )  # IDs of skipped improvements

    # Before/after comparison
    comparison: BeforeAfterComparison = Field(default_factory=BeforeAfterComparison)

    # File changes
    files_modified: list[FileChange] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    files_deleted: list[str] = Field(default_factory=list)

    # Statistics
    total_improvements: int = 0
    applied_count: int = 0
    skipped_count: int = 0

    # Next steps
    next_steps: list[NextStep] = Field(default_factory=list)

    # Metadata
    plugin_name: str | None = None
    analysis_mode: str | None = None  # quick, standard, deep
