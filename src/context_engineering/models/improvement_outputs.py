"""Pydantic models for improvement sub-agent outputs.

These models define the output schemas for:
- context-optimizer: Applies Four Laws optimizations
- orchestration-improver: Improves agent hierarchy
- handoff-improver: Optimizes agent communication
- plan-analyzer: Deep analysis of plan structure
"""

from pydantic import BaseModel, ConfigDict, Field

from .enums import ContextTier, ImprovementType


# =============================================================================
# Context Improvement Models (context-optimizer output)
# =============================================================================


class CodeChange(BaseModel):
    """A specific code change for an improvement."""

    before: str
    after: str
    explanation: str | None = None


class ContextImprovement(BaseModel):
    """A single context improvement recommendation.

    Output from context-optimizer sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str  # Format: CTX-NNN
    file: str
    improvement_type: ImprovementType
    description: str
    code_change: CodeChange | None = None
    estimated_reduction: float | None = Field(
        default=None, ge=0.0, le=1.0
    )  # Token reduction %
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW

    # For TIER_SPEC improvements
    recommended_tier: ContextTier | None = None

    # For NOT_PASSED improvements
    fields_to_exclude: list[str] = Field(default_factory=list)


# =============================================================================
# Orchestration Improvement Models (orchestration-improver output)
# =============================================================================


class AgentStructure(BaseModel):
    """Current or proposed agent structure."""

    agents: list[str] = Field(default_factory=list)
    hierarchy: dict[str, list[str]] = Field(
        default_factory=dict
    )  # parent -> children
    entry_points: list[str] = Field(default_factory=list)


class MigrationStep(BaseModel):
    """A step in the migration process."""

    order: int
    description: str
    files_affected: list[str] = Field(default_factory=list)
    is_breaking: bool = False


class OrchestrationImprovement(BaseModel):
    """A single orchestration improvement recommendation.

    Output from orchestration-improver sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str  # Format: ORCH-NNN
    improvement_type: ImprovementType
    description: str

    current_structure: AgentStructure | None = None
    proposed_structure: AgentStructure | None = None

    files_affected: list[str] = Field(default_factory=list)
    migration_steps: list[MigrationStep] = Field(default_factory=list)

    estimated_complexity: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    priority: str = "MEDIUM"


# =============================================================================
# Handoff Improvement Models (handoff-improver output)
# =============================================================================


class HandoffTransition(BaseModel):
    """A transition point between agents."""

    from_agent: str
    to_agent: str


class HandoffPayload(BaseModel):
    """Payload specification for a handoff."""

    fields: list[str] = Field(default_factory=list)
    excluded_fields: list[str] = Field(default_factory=list)
    context_tier: ContextTier


class HandoffImprovement(BaseModel):
    """A single handoff improvement recommendation.

    Output from handoff-improver sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str  # Format: HO-NNN
    transition: HandoffTransition
    description: str

    current_handoff: list[str] = Field(default_factory=list)  # What's passed now
    optimized_handoff: HandoffPayload | None = None

    # Generated artifacts
    yaml_schema: str | None = None  # Generated YAML handoff spec
    pydantic_model: str | None = None  # Generated Pydantic model code

    estimated_reduction: float | None = Field(default=None, ge=0.0, le=1.0)
    priority: str = "MEDIUM"


# =============================================================================
# Plan Analysis Models (plan-analyzer output)
# =============================================================================


class PlanPhase(BaseModel):
    """A phase in the plan."""

    name: str
    description: str | None = None
    agents_involved: list[str] = Field(default_factory=list)
    context_received: list[str] = Field(default_factory=list)
    context_tier: ContextTier | None = None
    issues: list[str] = Field(default_factory=list)


class HandoffPoint(BaseModel):
    """A handoff point in the plan."""

    from_phase: str
    to_phase: str
    data_transferred: list[str] = Field(default_factory=list)
    potential_issues: list[str] = Field(default_factory=list)


class PlanAnalysis(BaseModel):
    """Complete analysis output from plan-analyzer.

    This is the root output structure for the plan-analyzer sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    plan_name: str | None = None

    # Detected phases
    phases: list[PlanPhase] = Field(default_factory=list)

    # Context per phase
    context_per_phase: dict[str, list[str]] = Field(default_factory=dict)

    # Handoff points
    handoff_points: list[HandoffPoint] = Field(default_factory=list)

    # Violations
    violations: list[str] = Field(default_factory=list)  # Over-sharing, missing tiers

    # Summary
    total_phases: int = 0
    phases_with_tier_spec: int = 0
    estimated_total_context: str | None = None
