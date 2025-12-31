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


class AnalysisMode(str, Enum):
    """Analysis depth modes."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
