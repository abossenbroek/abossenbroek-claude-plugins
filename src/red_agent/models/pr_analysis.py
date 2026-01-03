"""Pydantic models for PR analysis and diff processing."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

from .validators import validate_finding_id

# Valid severity levels for PR findings
PR_FINDING_SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


class FileMetadata(BaseModel):
    """Metadata for a single file change."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    path: str = Field(min_length=1, description="File path relative to repo root")
    additions: int = Field(ge=0, description="Number of lines added")
    deletions: int = Field(ge=0, description="Number of lines deleted")
    change_type: Literal["added", "modified", "deleted"]
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score for this file")


class DiffMetadata(BaseModel):
    """Metadata from git diff operation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    git_operation: Literal["staged", "working", "branch", "diff_file"]
    files_changed: list[FileMetadata] = Field(default_factory=list)
    total_files_changed: int = Field(ge=0)
    total_additions: int = Field(ge=0)
    total_deletions: int = Field(ge=0)
    pr_size: Literal["tiny", "small", "medium", "large", "massive"]


class FileRef(BaseModel):
    """Reference to a file with lazy loading support."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    file_id: str = Field(min_length=1, description="Unique identifier for the file")
    path: str = Field(min_length=1, description="File path relative to repo root")
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score for this file")
    diff_snippet: str = Field(description="Snippet of the diff for preview")
    line_ranges: list[list[int]] = Field(
        default_factory=list, description="Line ranges affected: [[start, end], ...]"
    )


# =============================================================================
# Diff Analysis Models
# =============================================================================


class DiffSummary(BaseModel):
    """Summary statistics from diff analysis."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    files_changed: int = Field(ge=0, description="Total files changed")
    high_risk_files: int = Field(ge=0, description="Count of high-risk files")
    medium_risk_files: int = Field(ge=0, description="Count of medium-risk files")
    low_risk_files: int = Field(ge=0, description="Count of low-risk files")
    total_insertions: int = Field(ge=0, description="Total lines added")
    total_deletions: int = Field(ge=0, description="Total lines deleted")


class FileAnalysis(BaseModel):
    """Analysis of a single file's changes."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    file_id: str = Field(min_length=1, description="Sanitized file identifier")
    path: str = Field(min_length=1, description="File path relative to repo root")
    risk_level: Literal["high", "medium", "low"]
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score for this file")
    change_summary: str = Field(min_length=1, description="Brief description of changes")
    risk_factors: list[str] = Field(
        default_factory=list, description="Specific risk factors identified"
    )
    line_ranges: list[list[int]] = Field(
        default_factory=list, description="Affected line ranges [[start, end], ...]"
    )
    change_type: Literal["addition", "modification", "deletion", "refactor"]
    insertions: int = Field(ge=0, description="Lines added in this file")
    deletions: int = Field(ge=0, description="Lines deleted in this file")


class RiskCategoryExposure(BaseModel):
    """Exposure assessment for a risk category."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    category: str = Field(min_length=1, description="Risk category name")
    exposure: Literal["high", "medium", "low", "none"]
    affected_files: list[str] = Field(
        default_factory=list, description="File IDs affected by this risk"
    )
    notes: str = Field(min_length=1, description="Why this category is exposed")


class PatternDetected(BaseModel):
    """A cross-file pattern detected in the diff."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    pattern: str = Field(min_length=1, description="Pattern name")
    description: str = Field(min_length=1, description="What the pattern indicates")
    instances: int = Field(ge=1, description="Number of instances found")
    affected_files: list[str] = Field(
        default_factory=list, description="File IDs exhibiting this pattern"
    )
    risk_implication: str = Field(
        min_length=1, description="Why this pattern matters"
    )


class FocusArea(BaseModel):
    """An area requiring focused attention."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    area: str = Field(min_length=1, description="General area name")
    files: list[str] = Field(default_factory=list, description="Related file IDs")
    rationale: str = Field(min_length=1, description="Why this needs attention")


class DiffAnalysisResults(BaseModel):
    """Complete diff analysis results structure."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    summary: DiffSummary
    file_analysis: list[FileAnalysis] = Field(
        default_factory=list, description="Per-file analysis"
    )
    risk_surface: list[RiskCategoryExposure] = Field(
        default_factory=list, description="Risk category exposure assessment"
    )
    patterns_detected: list[PatternDetected] = Field(
        default_factory=list, description="Cross-file patterns"
    )
    high_risk_files: list[str] = Field(
        default_factory=list, description="File IDs with risk_score > 0.7"
    )
    focus_areas: list[FocusArea] = Field(
        default_factory=list, description="Areas needing attention"
    )
    key_observations: list[str] = Field(
        default_factory=list, description="Key insights from analysis"
    )


class DiffAnalysisOutput(BaseModel):
    """Output from diff-analyzer agent."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    diff_analysis: DiffAnalysisResults


# =============================================================================
# Code Attacker Models
# =============================================================================


class CodeFindingTarget(BaseModel):
    """Target information for a code-level finding."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    file_path: str = Field(min_length=1, description="Path to the affected file")
    line_numbers: list[int] = Field(
        default_factory=list, description="Line numbers affected"
    )
    diff_snippet: str = Field(min_length=1, description="Diff snippet showing the issue")
    function_name: str | None = Field(
        default=None, description="Function name if applicable"
    )


class CodeFindingEvidence(BaseModel):
    """Evidence for a code-level finding."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: str = Field(min_length=1, description="Type of evidence")
    description: str | None = Field(
        default=None, description="Description of the flaw"
    )
    code_quote: str | None = Field(
        default=None, description="Problematic code snippet"
    )
    assumption: str | None = Field(
        default=None, description="Hidden assumption in the code"
    )
    why_problematic: str | None = Field(
        default=None, description="Why this assumption can fail"
    )
    edge_case: str | None = Field(
        default=None, description="Specific edge case not handled"
    )


class CodeAttackApplied(BaseModel):
    """Attack information for code-level finding."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    style: str = Field(min_length=1, description="Attack style used")
    probe: str = Field(min_length=1, description="Scenario or input that triggers issue")


class CodeFindingImpact(BaseModel):
    """Impact assessment for code-level finding."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    if_exploited: str | None = Field(
        default=None, description="What goes wrong if bug is hit"
    )
    affected_functionality: str | None = Field(
        default=None, description="Feature or system that breaks"
    )
    if_assumption_fails: str | None = Field(
        default=None, description="Error type when assumption fails"
    )
    likelihood: str | None = Field(
        default=None, description="Likelihood: likely|possible|unlikely"
    )
    if_triggered: str | None = Field(
        default=None, description="Behavior when edge case occurs"
    )
    severity_justification: str | None = Field(
        default=None, description="Why this severity level"
    )


class CodeAttackerFinding(BaseModel):
    """A finding from code-reasoning-attacker agent."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(min_length=1, description="Finding ID (LE-NNN, AG-NNN, EH-NNN)")
    category: str = Field(
        min_length=1, description="Category: logic-errors, assumption-gaps, edge-case-handling"
    )
    severity: str = Field(min_length=1, description="Severity level")
    title: str = Field(min_length=1, description="Short descriptive title")
    target: CodeFindingTarget
    evidence: CodeFindingEvidence
    attack_applied: CodeAttackApplied
    impact: CodeFindingImpact
    recommendation: str = Field(min_length=10, description="Specific fix with code suggestion")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in finding")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate finding ID matches expected patterns (LE-NNN, AG-NNN, EH-NNN)."""
        # Allow LE-, AG-, EH- prefixes for code attacker findings
        if not (v.startswith("LE-") or v.startswith("AG-") or v.startswith("EH-")):
            # Fall back to generic validation
            return validate_finding_id(v)
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is a known level."""
        if v not in PR_FINDING_SEVERITY_LEVELS:
            msg = f"Severity '{v}' must be one of {PR_FINDING_SEVERITY_LEVELS}"
            raise ValueError(msg)
        return v


class CodePatternDetected(BaseModel):
    """A cross-file pattern detected by code attacker."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    pattern: str = Field(min_length=1, description="Pattern name")
    instances: int = Field(ge=1, description="Number of instances")
    files_affected: list[str] = Field(
        default_factory=list, description="Files exhibiting this pattern"
    )
    description: str = Field(
        min_length=1, description="Cross-cutting observation"
    )
    systemic_recommendation: str | None = Field(
        default=None, description="How to address pattern"
    )


class CodeAttackSummary(BaseModel):
    """Summary of code attack results."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    total_findings: int = Field(ge=0, description="Total findings count")
    by_severity: dict[str, int] = Field(
        default_factory=dict, description="Counts by severity level"
    )
    highest_risk_file: str | None = Field(
        default=None, description="Path to highest risk file"
    )
    primary_weakness: str | None = Field(
        default=None, description="One sentence summary"
    )


class CodeAttackResults(BaseModel):
    """Results structure from code-reasoning-attacker."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    attack_type: str = Field(min_length=1, description="Should be 'code-reasoning-attacker'")
    categories_probed: list[str] = Field(
        default_factory=list, description="Categories analyzed"
    )
    findings: list[CodeAttackerFinding] = Field(
        default_factory=list, description="All findings from code analysis"
    )
    patterns_detected: list[CodePatternDetected] = Field(
        default_factory=list, description="Cross-file patterns"
    )
    summary: CodeAttackSummary


class CodeAttackerOutput(BaseModel):
    """Output from code-reasoning-attacker agent."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    attack_results: CodeAttackResults


class PRSummary(BaseModel):
    """Summary of PR changes and metadata."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    title: str | None = Field(default=None, description="PR title if available")
    description: str | None = Field(
        default=None, description="PR description if available"
    )
    files_changed: int = Field(ge=0, description="Total number of files changed")
    additions: int = Field(ge=0, description="Total lines added")
    deletions: int = Field(ge=0, description="Total lines deleted")
    pr_size: Literal["tiny", "small", "medium", "large", "massive"]
    high_risk_files: list[str] = Field(
        default_factory=list, description="Paths of high-risk files"
    )


class PRFinding(BaseModel):
    """A finding specific to PR analysis."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(min_length=1, description="Finding ID (e.g., PR-001)")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str = Field(min_length=1, description="Short title of the finding")
    description: str = Field(min_length=10, description="Detailed description")
    file_path: str | None = Field(default=None, description="Affected file path")
    line_ranges: list[list[int]] = Field(
        default_factory=list, description="Affected line ranges"
    )
    recommendation: str = Field(
        min_length=10, description="Recommendation to address the finding"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the finding")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate finding ID matches XX-NNN or XXX-NNN format."""
        return validate_finding_id(v)


class BreakingChange(BaseModel):
    """A potential breaking change identified in the PR."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: str = Field(min_length=1, description="Type of breaking change")
    description: str = Field(min_length=10, description="Description of the change")
    file_path: str = Field(min_length=1, description="File containing the change")
    impact: str = Field(min_length=10, description="Potential impact on consumers")
    mitigation: str | None = Field(
        default=None, description="Suggested mitigation strategy"
    )


class PRRedTeamReport(BaseModel):
    """PR-specific red team report."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    executive_summary: str = Field(
        min_length=50, description="High-level summary of PR analysis"
    )
    pr_summary: PRSummary
    risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    findings: list[PRFinding] = Field(
        default_factory=list, description="All findings across the PR"
    )
    findings_by_file: dict[str, list[PRFinding]] = Field(
        default_factory=dict, description="Findings grouped by file path"
    )
    breaking_changes: list[BreakingChange] = Field(
        default_factory=list, description="Identified breaking changes"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="High-level recommendations"
    )
    test_coverage_notes: str | None = Field(
        default=None, description="Notes on test coverage changes"
    )
