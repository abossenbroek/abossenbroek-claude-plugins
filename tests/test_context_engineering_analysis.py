"""Tests for context engineering analysis output validation."""

import pytest
from pydantic import ValidationError

from context_engineering.models import (
    ContextFlowMap,
    ContextTier,
    PlanAnalysis,
    PluginAnalysis,
)
from context_engineering.models.analysis_outputs import (
    AgentAnalysis,
    ContextFlowMap,
    DetectedPattern,
    FlowEdge,
    ImprovementOpportunity,
    PatternViolation,
    PluginMetrics,
    RedundancyIssue,
)
from context_engineering.models.enums import PatternType, ViolationType
from context_engineering.models.improvement_outputs import (
    HandoffPoint,
    PlanPhase,
)


class TestPluginAnalysisModel:
    """Tests for PluginAnalysis model."""

    def test_full_plugin_analysis(self):
        """Test complete plugin analysis output."""
        analysis = PluginAnalysis(
            plugin_name="red-agent",
            plugin_version="1.2.0",
            current_patterns=[
                DetectedPattern(
                    pattern_type=PatternType.FIREWALL,
                    confidence=0.95,
                    evidence=[
                        "Entry agent is thin router",
                        "Work happens in coordinator-internal/",
                    ],
                    files=["agents/red-team-coordinator.md"],
                ),
                DetectedPattern(
                    pattern_type=PatternType.HIERARCHICAL,
                    confidence=0.85,
                    evidence=["Clear parent-child hierarchy"],
                ),
            ],
            violations=[
                PatternViolation(
                    violation_type=ViolationType.MISSING_TIER,
                    file="coordinator-internal/analyzer.md",
                    description="No context tier specified in Input section",
                    recommendation="Add: You receive (SELECTIVE context):",
                    severity="MEDIUM",
                )
            ],
            agents=[
                AgentAnalysis(
                    file="agents/red-team-coordinator.md",
                    agent_type="entry",
                    tools=["Task", "Read"],
                    context_tier=None,  # Firewall doesn't process data
                ),
                AgentAnalysis(
                    file="coordinator-internal/analyzer.md",
                    agent_type="coordinator-internal",
                    tools=["Read"],
                    context_tier=ContextTier.FULL,
                    receives=["full_snapshot"],
                    estimated_tokens=15000,
                ),
            ],
            opportunities=[
                ImprovementOpportunity(
                    category="context",
                    description="Add tier specifications to 3 agents",
                    files_affected=[
                        "coordinator-internal/analyzer.md",
                        "coordinator-internal/attacker.md",
                    ],
                    estimated_reduction=0.35,
                    priority="HIGH",
                    improvement_type="TIER_SPEC",
                )
            ],
            metrics=PluginMetrics(
                total_files=15,
                agent_count=14,
                entry_agents=3,
                sub_agents=11,
                command_count=2,
                skill_count=2,
                estimated_total_tokens=50000,
                tier_compliance=0.7,
            ),
            summary="Well-structured plugin using firewall pattern. 3 agents missing tier specs.",
        )

        assert analysis.plugin_name == "red-agent"
        assert len(analysis.current_patterns) == 2
        assert analysis.metrics.agent_count == 14
        assert analysis.metrics.tier_compliance == 0.7

    def test_plugin_analysis_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            PluginAnalysis(
                plugin_name="test",
                unknown_field="should fail",
            )

    def test_plugin_analysis_tier_compliance_range(self):
        """Test tier_compliance must be 0.0-1.0."""
        # Valid
        metrics = PluginMetrics(tier_compliance=0.5)
        assert metrics.tier_compliance == 0.5

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            PluginMetrics(tier_compliance=1.5)

        # Invalid: < 0.0
        with pytest.raises(ValidationError):
            PluginMetrics(tier_compliance=-0.1)


class TestContextFlowMapModel:
    """Tests for ContextFlowMap model."""

    def test_full_context_flow_map(self):
        """Test complete context flow map output."""
        flow_map = ContextFlowMap(
            flows=[
                FlowEdge(
                    from_agent="coordinator",
                    to_agent="analyzer",
                    data_passed=["plugin_manifest", "agent_files", "mode"],
                    data_size_estimate="large",
                    context_tier=ContextTier.FULL,
                    is_redundant=False,
                ),
                FlowEdge(
                    from_agent="coordinator",
                    to_agent="optimizer",
                    data_passed=["analysis_summary", "relevant_files", "focus"],
                    data_size_estimate="medium",
                    context_tier=ContextTier.SELECTIVE,
                    is_redundant=False,
                ),
                FlowEdge(
                    from_agent="optimizer",
                    to_agent="pattern-checker",
                    data_passed=["improvements", "focus", "analysis_summary"],
                    context_tier=ContextTier.FILTERED,
                    is_redundant=True,
                    redundancy_reason="analysis_summary already passed once",
                ),
            ],
            redundancies=[
                RedundancyIssue(
                    description="analysis_summary passed multiple times",
                    agents_affected=["coordinator", "optimizer", "pattern-checker"],
                    data_duplicated=["analysis_summary"],
                    estimated_waste="~500 tokens",
                )
            ],
            missing_tiers=["coordinator-internal/analyzer.md"],
            total_flows=3,
            redundant_flows=1,
            agents_mapped=4,
        )

        assert len(flow_map.flows) == 3
        assert flow_map.redundant_flows == 1
        assert len(flow_map.missing_tiers) == 1

    def test_flow_edge_data_size_values(self):
        """Test FlowEdge data_size_estimate values."""
        for size in ["small", "medium", "large"]:
            edge = FlowEdge(
                from_agent="a",
                to_agent="b",
                data_size_estimate=size,
            )
            assert edge.data_size_estimate == size

    def test_flow_edge_redundancy(self):
        """Test FlowEdge redundancy detection."""
        edge = FlowEdge(
            from_agent="coordinator",
            to_agent="validator",
            data_passed=["data"],
            is_redundant=True,
            redundancy_reason="Same data passed through coordinator",
        )
        assert edge.is_redundant
        assert edge.redundancy_reason is not None


class TestPlanAnalysisModel:
    """Tests for PlanAnalysis model."""

    def test_full_plan_analysis(self):
        """Test complete plan analysis output."""
        analysis = PlanAnalysis(
            plan_name="implementation-plan",
            phases=[
                PlanPhase(
                    name="Analysis",
                    description="Analyze current plugin structure",
                    agents_involved=["plugin-analyzer"],
                    context_received=["full_plugin"],
                    context_tier=ContextTier.FULL,
                ),
                PlanPhase(
                    name="Improvement",
                    description="Generate improvements",
                    agents_involved=["context-optimizer", "orchestration-improver"],
                    context_received=["analysis_summary", "relevant_files"],
                    context_tier=ContextTier.SELECTIVE,
                ),
                PlanPhase(
                    name="Grounding",
                    description="Validate improvements",
                    agents_involved=["pattern-checker"],
                    context_received=["high_priority_improvements"],
                    context_tier=ContextTier.FILTERED,
                    issues=["Could batch by severity"],
                ),
            ],
            context_per_phase={
                "Analysis": ["full_plugin"],
                "Improvement": ["analysis_summary", "relevant_files"],
                "Grounding": ["high_priority_improvements"],
            },
            handoff_points=[
                HandoffPoint(
                    from_phase="Analysis",
                    to_phase="Improvement",
                    data_transferred=["analysis_results"],
                    potential_issues=["Full results passed, could use summary"],
                )
            ],
            violations=["Phase 3 could use severity batching"],
            total_phases=3,
            phases_with_tier_spec=3,
            estimated_total_context="medium",
        )

        assert analysis.plan_name == "implementation-plan"
        assert len(analysis.phases) == 3
        assert analysis.phases_with_tier_spec == 3

    def test_plan_phase_with_issues(self):
        """Test PlanPhase with issues."""
        phase = PlanPhase(
            name="Grounding",
            agents_involved=["all_validators"],
            issues=[
                "Runs all validators for all items",
                "Should use severity batching",
            ],
        )
        assert len(phase.issues) == 2

    def test_handoff_point_potential_issues(self):
        """Test HandoffPoint with potential issues."""
        handoff = HandoffPoint(
            from_phase="Analysis",
            to_phase="Work",
            data_transferred=["full_analysis", "all_files"],
            potential_issues=[
                "Full analysis passed when summary would suffice",
                "All files included, should filter by relevance",
            ],
        )
        assert len(handoff.potential_issues) == 2


class TestAgentAnalysis:
    """Tests for AgentAnalysis model."""

    def test_agent_analysis_with_all_fields(self):
        """Test AgentAnalysis with all fields."""
        agent = AgentAnalysis(
            file="agents/coordinator.md",
            agent_type="entry",
            tools=["Task", "Read", "AskUserQuestion"],
            context_tier=None,
            receives=["plugin_path", "mode"],
            not_provided=["full_analysis", "intermediate_results"],
            estimated_tokens=500,
            issues=["Could document context tier"],
        )
        assert agent.agent_type == "entry"
        assert len(agent.tools) == 3
        assert agent.context_tier is None

    def test_agent_analysis_minimal(self):
        """Test minimal AgentAnalysis."""
        agent = AgentAnalysis(
            file="analyzer.md",
            agent_type="coordinator-internal",
        )
        assert agent.tools == []
        assert agent.receives == []


class TestImprovementOpportunity:
    """Tests for ImprovementOpportunity model."""

    def test_improvement_opportunity_with_reduction(self):
        """Test ImprovementOpportunity with estimated reduction."""
        opportunity = ImprovementOpportunity(
            category="context",
            description="Add tier specs to agents",
            files_affected=["agent1.md", "agent2.md", "agent3.md"],
            estimated_reduction=0.45,
            priority="HIGH",
            improvement_type="TIER_SPEC",
        )
        assert opportunity.estimated_reduction == 0.45
        assert len(opportunity.files_affected) == 3

    def test_improvement_opportunity_reduction_range(self):
        """Test estimated_reduction must be 0.0-1.0."""
        # Valid
        opportunity = ImprovementOpportunity(
            category="context",
            description="Test",
            improvement_type="TEST",
            estimated_reduction=0.5,
        )
        assert opportunity.estimated_reduction == 0.5

        # Invalid
        with pytest.raises(ValidationError):
            ImprovementOpportunity(
                category="context",
                description="Test",
                improvement_type="TEST",
                estimated_reduction=1.5,
            )
