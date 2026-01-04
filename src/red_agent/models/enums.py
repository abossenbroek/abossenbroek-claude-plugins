"""Enumeration types for red team agent outputs."""

from enum import Enum


class Severity(str, Enum):
    """Severity levels for findings and risk assessments."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    NONE = "NONE"


class FindingSeverity(str, Enum):
    """Severity levels specifically for findings (excludes INFO and NONE)."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Confidence(str, Enum):
    """Confidence levels for assessments."""

    EXPLORING = "exploring"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    ALMOST_CERTAIN = "almost_certain"
    CERTAIN = "certain"


class RiskCategoryName(str, Enum):
    """Risk category names from the red team taxonomy."""

    REASONING_FLAWS = "reasoning-flaws"
    ASSUMPTION_GAPS = "assumption-gaps"
    CONTEXT_MANIPULATION = "context-manipulation"
    AUTHORITY_EXPLOITATION = "authority-exploitation"
    INFORMATION_LEAKAGE = "information-leakage"
    HALLUCINATION_RISKS = "hallucination-risks"
    OVER_CONFIDENCE = "over-confidence"
    SCOPE_CREEP = "scope-creep"
    DEPENDENCY_BLINDNESS = "dependency-blindness"
    TEMPORAL_INCONSISTENCY = "temporal-inconsistency"
    CODE_DUPLICATION = "code-duplication"


class AnalysisMode(str, Enum):
    """Analysis depth modes."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class EvidenceType(str, Enum):
    """Types of evidence for findings."""

    LOGICAL_GAP = "logical_gap"
    FALLACY = "fallacy"
    CONTRADICTION = "contradiction"
    MISSING_STEP = "missing_step"
    HIDDEN_ASSUMPTION = "hidden_assumption"
    UNSTATED_CONSTRAINT = "unstated_constraint"
    ENVIRONMENTAL_DEPENDENCY = "environmental_dependency"


class MatchQuality(str, Enum):
    """Quote match quality for grounding assessments."""

    EXACT = "exact"
    CLOSE = "close"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    NOT_FOUND = "not_found"


class Likelihood(str, Enum):
    """Likelihood levels for impact assessment."""

    LIKELY = "likely"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"
