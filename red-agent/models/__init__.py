"""Pydantic models for red team agent outputs.

This module provides type-safe models for validating red team analysis outputs.
"""

from .enums import (
    AnalysisMode,
    Confidence,
    FindingSeverity,
    RiskCategoryName,
    Severity,
)
from .findings import (
    Evidence,
    Finding,
    GroundingNotes,
    Pattern,
    RiskCategory,
)
from .outputs import (
    AttackerFinding,
    AttackerOutput,
    AttackResults,
    ClaimAnalysis,
    ContextAnalysisOutput,
    ContextAnalysisResults,
    GroundingAssessment,
    GroundingOutput,
    GroundingResults,
    RiskSurface,
)
from .reports import (
    FindingsByLevel,
    Limitations,
    Methodology,
    Recommendations,
    RedTeamReport,
    RiskOverview,
)

__all__ = [
    # Enums
    "AnalysisMode",
    "Confidence",
    "FindingSeverity",
    "RiskCategoryName",
    "Severity",
    # Findings
    "Evidence",
    "Finding",
    "GroundingNotes",
    "Pattern",
    "RiskCategory",
    # Reports
    "FindingsByLevel",
    "Limitations",
    "Methodology",
    "Recommendations",
    "RedTeamReport",
    "RiskOverview",
    # Outputs
    "AttackerFinding",
    "AttackerOutput",
    "AttackResults",
    "ClaimAnalysis",
    "ContextAnalysisOutput",
    "ContextAnalysisResults",
    "GroundingAssessment",
    "GroundingOutput",
    "GroundingResults",
    "RiskSurface",
]
