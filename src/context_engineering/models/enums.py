"""Enumeration types for context engineering agent outputs."""

from enum import Enum


class ContextTier(str, Enum):
    """Context fidelity tiers based on the Four Laws of Context Management.

    From highest to lowest context:
    - FULL: Complete data, used for initial analysis
    - SELECTIVE: Relevant subset for domain workers
    - FILTERED: Criteria-matched for validators
    - MINIMAL: Mode + counts for strategy/routing
    - METADATA: Scope stats only for report synthesis
    """

    FULL = "FULL"
    SELECTIVE = "SELECTIVE"
    FILTERED = "FILTERED"
    MINIMAL = "MINIMAL"
    METADATA = "METADATA"


class ImprovementType(str, Enum):
    """Types of improvements that can be applied to plugins."""

    # Context improvements
    TIER_SPEC = "TIER_SPEC"  # Add context tier specification
    NOT_PASSED = "NOT_PASSED"  # Add explicit "NOT PASSED" documentation
    REFERENCE_PATTERN = "REFERENCE_PATTERN"  # Use reference instead of embedding
    LAZY_LOAD = "LAZY_LOAD"  # Implement lazy loading pattern

    # Orchestration improvements
    FIREWALL = "FIREWALL"  # Add firewall coordinator
    PHASE_SPLIT = "PHASE_SPLIT"  # Split into distinct phases
    SUBAGENT_EXTRACT = "SUBAGENT_EXTRACT"  # Extract sub-agent

    # Handoff improvements
    HANDOFF_SCHEMA = "HANDOFF_SCHEMA"  # Add YAML handoff schema
    PYDANTIC_MODEL = "PYDANTIC_MODEL"  # Generate Pydantic model
    VALIDATION_HOOK = "VALIDATION_HOOK"  # Add PostToolUse hook

    # General
    SEVERITY_BATCH = "SEVERITY_BATCH"  # Add severity-based batching


class PatternType(str, Enum):
    """SOTA orchestration patterns."""

    HIERARCHICAL = "HIERARCHICAL"  # Clear decomposition, audit trails
    SWARM = "SWARM"  # Parallel exploration, diverse perspectives
    REACT = "REACT"  # Dynamic adaptation, tool-heavy workflows
    PLAN_EXECUTE = "PLAN_EXECUTE"  # Clear sequence, predictability
    REFLECTION = "REFLECTION"  # Quality refinement, self-correction
    HYBRID = "HYBRID"  # Multiple coordination needs
    FIREWALL = "FIREWALL"  # Coordinator isolation for context control


class RiskLevel(str, Enum):
    """Risk levels for improvement assessments."""

    CRITICAL = "CRITICAL"  # Breaking changes, requires immediate attention
    HIGH = "HIGH"  # Significant changes, needs careful review
    MEDIUM = "MEDIUM"  # Moderate changes, standard review
    LOW = "LOW"  # Minor changes, safe to apply


class ViolationType(str, Enum):
    """Types of Four Laws violations."""

    # Law 1: Selective Projection violations
    FULL_SNAPSHOT = "FULL_SNAPSHOT"  # Passing full context everywhere
    UNNECESSARY_FIELDS = "UNNECESSARY_FIELDS"  # Including fields not needed

    # Law 2: Tiered Context Fidelity violations
    MISSING_TIER = "MISSING_TIER"  # No tier specification
    WRONG_TIER = "WRONG_TIER"  # Tier too high for agent role

    # Law 3: Reference vs Embedding violations
    LARGE_EMBEDDING = "LARGE_EMBEDDING"  # Embedding large data instead of reference
    REPEATED_CONTEXT = "REPEATED_CONTEXT"  # Same data passed multiple times

    # Law 4: Lazy Loading violations
    UPFRONT_LOAD = "UPFRONT_LOAD"  # Loading all data upfront

    # Anti-patterns
    SNAPSHOT_BROADCAST = "SNAPSHOT_BROADCAST"  # Full context to every agent
    DEFENSIVE_INCLUSION = "DEFENSIVE_INCLUSION"  # "Maybe they need this"
    GROUNDING_EVERYTHING = "GROUNDING_EVERYTHING"  # Validating low-priority items
