"""Pydantic models for analysis sub-agent outputs.

These models define the output schemas for:
- plugin-analyzer: Deep analysis of plugin structure
- plan-analyzer: Deep analysis of plan structure
- context-flow-mapper: Maps data flows between agents
"""

from pydantic import BaseModel, ConfigDict, Field

from .enums import ContextTier, PatternType, ViolationType


# =============================================================================
# Plugin Analysis Models (plugin-analyzer output)
# =============================================================================


class PatternViolation(BaseModel):
    """A Four Laws violation detected in the plugin."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    violation_type: ViolationType
    file: str
    line: int | None = None
    description: str
    current_code: str | None = None
    recommendation: str
    severity: str = "MEDIUM"  # HIGH, MEDIUM, LOW


class DetectedPattern(BaseModel):
    """An orchestration pattern detected in the plugin."""

    pattern_type: PatternType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)


class AgentAnalysis(BaseModel):
    """Analysis of a single agent file."""

    file: str
    agent_type: str  # entry, coordinator-internal, grounding, etc.
    tools: list[str] = Field(default_factory=list)
    context_tier: ContextTier | None = None
    receives: list[str] = Field(default_factory=list)
    not_provided: list[str] = Field(default_factory=list)
    estimated_tokens: int | None = None
    issues: list[str] = Field(default_factory=list)


class PluginMetrics(BaseModel):
    """Quantitative metrics for a plugin."""

    total_files: int = 0
    agent_count: int = 0
    entry_agents: int = 0
    sub_agents: int = 0
    command_count: int = 0
    skill_count: int = 0
    estimated_total_tokens: int | None = None
    tier_compliance: float = Field(
        default=0.0, ge=0.0, le=1.0
    )  # % of agents with tier spec


class ImprovementOpportunity(BaseModel):
    """An opportunity for improvement in the plugin."""

    category: str  # context, orchestration, handoff
    description: str
    files_affected: list[str] = Field(default_factory=list)
    estimated_reduction: float | None = Field(
        default=None, ge=0.0, le=1.0
    )  # Token reduction %
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    improvement_type: str  # Maps to ImprovementType enum value


class PluginAnalysis(BaseModel):
    """Complete analysis output from plugin-analyzer.

    This is the root output structure for the plugin-analyzer sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    plugin_name: str
    plugin_version: str | None = None

    # Detected patterns
    current_patterns: list[DetectedPattern] = Field(default_factory=list)

    # Violations found
    violations: list[PatternViolation] = Field(default_factory=list)

    # Agent-level analysis
    agents: list[AgentAnalysis] = Field(default_factory=list)

    # Improvement opportunities
    opportunities: list[ImprovementOpportunity] = Field(default_factory=list)

    # Metrics
    metrics: PluginMetrics = Field(default_factory=PluginMetrics)

    # Summary
    summary: str | None = None


# =============================================================================
# Context Flow Map Models (context-flow-mapper output)
# =============================================================================


class FlowEdge(BaseModel):
    """A data flow edge between two agents."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    from_agent: str
    to_agent: str
    data_passed: list[str] = Field(default_factory=list)
    data_size_estimate: str | None = None  # "small", "medium", "large"
    context_tier: ContextTier | None = None
    is_redundant: bool = False
    redundancy_reason: str | None = None


class RedundancyIssue(BaseModel):
    """A redundancy issue in context flow."""

    description: str
    agents_affected: list[str] = Field(default_factory=list)
    data_duplicated: list[str] = Field(default_factory=list)
    estimated_waste: str | None = None


class ContextFlowMap(BaseModel):
    """Complete context flow map from context-flow-mapper.

    This is the root output structure for the context-flow-mapper sub-agent.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # All flow edges
    flows: list[FlowEdge] = Field(default_factory=list)

    # Identified redundancies
    redundancies: list[RedundancyIssue] = Field(default_factory=list)

    # Agents without tier specification
    missing_tiers: list[str] = Field(default_factory=list)

    # Summary statistics
    total_flows: int = 0
    redundant_flows: int = 0
    agents_mapped: int = 0
