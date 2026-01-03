"""Tests for context engineering Pydantic models."""

import pytest
from pydantic import ValidationError

from context_engineering.models import (
    ContextImprovement,
    ContextTier,
    HandoffImprovement,
    ImprovementType,
    OrchestrationImprovement,
    PatternCompliance,
    PatternType,
    PluginAnalysis,
    RiskAssessment,
    RiskLevel,
    TokenEstimate,
)
from context_engineering.models.analysis_outputs import (
    DetectedPattern,
    FlowEdge,
    PatternViolation,
)
from context_engineering.models.enums import ViolationType
from context_engineering.models.improvement_outputs import (
    AgentStructure,
    CodeChange,
    HandoffPayload,
    HandoffTransition,
    MigrationStep,
)


class TestEnums:
    """Test enum definitions."""

    def test_context_tier_values(self):
        """Test ContextTier has all expected values."""
        assert ContextTier.FULL == "FULL"
        assert ContextTier.SELECTIVE == "SELECTIVE"
        assert ContextTier.FILTERED == "FILTERED"
        assert ContextTier.MINIMAL == "MINIMAL"
        assert ContextTier.METADATA == "METADATA"

    def test_improvement_type_values(self):
        """Test ImprovementType has expected values."""
        assert ImprovementType.TIER_SPEC == "TIER_SPEC"
        assert ImprovementType.NOT_PASSED == "NOT_PASSED"
        assert ImprovementType.FIREWALL == "FIREWALL"

    def test_pattern_type_values(self):
        """Test PatternType has expected values."""
        assert PatternType.HIERARCHICAL == "HIERARCHICAL"
        assert PatternType.FIREWALL == "FIREWALL"

    def test_risk_level_values(self):
        """Test RiskLevel has expected values."""
        assert RiskLevel.CRITICAL == "CRITICAL"
        assert RiskLevel.HIGH == "HIGH"
        assert RiskLevel.MEDIUM == "MEDIUM"
        assert RiskLevel.LOW == "LOW"


class TestAnalysisOutputs:
    """Tests for analysis output models."""

    def test_plugin_analysis_valid(self):
        """Test valid PluginAnalysis model."""
        data = {
            "plugin_name": "test-plugin",
            "plugin_version": "1.0.0",
            "current_patterns": [
                {
                    "pattern_type": "FIREWALL",
                    "confidence": 0.9,
                    "evidence": ["entry agent routes to sub-agents"],
                    "files": ["agents/coordinator.md"],
                }
            ],
            "violations": [
                {
                    "violation_type": "MISSING_TIER",
                    "file": "agents/analyzer.md",
                    "description": "No context tier specified",
                    "recommendation": "Add tier spec",
                }
            ],
            "agents": [
                {
                    "file": "agents/coordinator.md",
                    "agent_type": "entry",
                    "tools": ["Task", "Read"],
                }
            ],
            "opportunities": [
                {
                    "category": "context",
                    "description": "Add tier spec",
                    "files_affected": ["agents/analyzer.md"],
                    "improvement_type": "TIER_SPEC",
                }
            ],
            "metrics": {
                "total_files": 5,
                "agent_count": 3,
                "tier_compliance": 0.5,
            },
        }
        analysis = PluginAnalysis(**data)
        assert analysis.plugin_name == "test-plugin"
        assert len(analysis.current_patterns) == 1
        assert len(analysis.violations) == 1

    def test_plugin_analysis_minimal(self):
        """Test minimal PluginAnalysis."""
        analysis = PluginAnalysis(plugin_name="test")
        assert analysis.plugin_name == "test"
        assert analysis.current_patterns == []
        assert analysis.violations == []

    def test_detected_pattern(self):
        """Test DetectedPattern model."""
        pattern = DetectedPattern(
            pattern_type=PatternType.FIREWALL,
            confidence=0.95,
            evidence=["entry routes to internal"],
            files=["coordinator.md"],
        )
        assert pattern.pattern_type == PatternType.FIREWALL
        assert pattern.confidence == 0.95

    def test_pattern_violation(self):
        """Test PatternViolation model."""
        violation = PatternViolation(
            violation_type=ViolationType.FULL_SNAPSHOT,
            file="coordinator.md",
            line=42,
            description="Passing full snapshot",
            recommendation="Use selective projection",
        )
        assert violation.violation_type == ViolationType.FULL_SNAPSHOT
        assert violation.line == 42

    def test_flow_edge(self):
        """Test FlowEdge model."""
        edge = FlowEdge(
            from_agent="coordinator",
            to_agent="analyzer",
            data_passed=["manifest", "files"],
            context_tier=ContextTier.FULL,
        )
        assert edge.from_agent == "coordinator"
        assert edge.context_tier == ContextTier.FULL


class TestImprovementOutputs:
    """Tests for improvement output models."""

    def test_context_improvement_valid(self):
        """Test valid ContextImprovement."""
        improvement = ContextImprovement(
            id="CTX-001",
            file="agents/analyzer.md",
            improvement_type=ImprovementType.TIER_SPEC,
            description="Add context tier specification",
            estimated_reduction=0.4,
            priority="HIGH",
            recommended_tier=ContextTier.SELECTIVE,
        )
        assert improvement.id == "CTX-001"
        assert improvement.improvement_type == ImprovementType.TIER_SPEC

    def test_context_improvement_with_code_change(self):
        """Test ContextImprovement with code change."""
        improvement = ContextImprovement(
            id="CTX-002",
            file="agents/analyzer.md",
            improvement_type=ImprovementType.NOT_PASSED,
            description="Add NOT PASSED section",
            code_change=CodeChange(
                before="## Input\nYou receive:\n- data",
                after="## Input\nYou receive (SELECTIVE):\n- summary\n\n**NOT PROVIDED**:\n- full data",
            ),
        )
        assert improvement.code_change is not None
        assert "NOT PROVIDED" in improvement.code_change.after

    def test_orchestration_improvement_valid(self):
        """Test valid OrchestrationImprovement."""
        improvement = OrchestrationImprovement(
            id="ORCH-001",
            improvement_type=ImprovementType.FIREWALL,
            description="Add firewall coordinator",
            current_structure=AgentStructure(
                agents=["main.md"],
                hierarchy={},
                entry_points=["main.md"],
            ),
            proposed_structure=AgentStructure(
                agents=["coordinator.md", "analyzer.md"],
                hierarchy={"coordinator.md": ["analyzer.md"]},
                entry_points=["coordinator.md"],
            ),
            migration_steps=[
                MigrationStep(
                    order=1,
                    description="Create coordinator",
                    files_affected=["coordinator.md"],
                )
            ],
        )
        assert improvement.id == "ORCH-001"
        assert len(improvement.migration_steps) == 1

    def test_handoff_improvement_valid(self):
        """Test valid HandoffImprovement."""
        improvement = HandoffImprovement(
            id="HO-001",
            transition=HandoffTransition(
                from_agent="coordinator",
                to_agent="analyzer",
            ),
            description="Add handoff schema",
            current_handoff=["full_data", "config"],
            optimized_handoff=HandoffPayload(
                fields=["summary", "mode"],
                excluded_fields=["full_data"],
                context_tier=ContextTier.SELECTIVE,
            ),
            yaml_schema="handoff:\n  context_level: SELECTIVE",
        )
        assert improvement.transition.from_agent == "coordinator"
        assert improvement.optimized_handoff.context_tier == ContextTier.SELECTIVE

    def test_estimated_reduction_range(self):
        """Test estimated_reduction validation."""
        # Valid range
        improvement = ContextImprovement(
            id="CTX-001",
            file="test.md",
            improvement_type=ImprovementType.TIER_SPEC,
            description="Test",
            estimated_reduction=0.5,
        )
        assert improvement.estimated_reduction == 0.5

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            ContextImprovement(
                id="CTX-001",
                file="test.md",
                improvement_type=ImprovementType.TIER_SPEC,
                description="Test",
                estimated_reduction=1.5,
            )


class TestGroundingOutputs:
    """Tests for grounding output models."""

    def test_pattern_compliance_valid(self):
        """Test valid PatternCompliance."""
        compliance = PatternCompliance(
            improvement_id="CTX-001",
            pattern_compliant=True,
            patterns_checked=[PatternType.FIREWALL, PatternType.HIERARCHICAL],
            confidence=0.9,
        )
        assert compliance.pattern_compliant is True
        assert len(compliance.patterns_checked) == 2

    def test_pattern_compliance_with_violations(self):
        """Test PatternCompliance with violations."""
        from context_engineering.models.grounding_outputs import PatternViolationDetail

        compliance = PatternCompliance(
            improvement_id="CTX-001",
            pattern_compliant=False,
            violations=[
                PatternViolationDetail(
                    pattern=PatternType.FIREWALL,
                    violation="Coordinator does analysis",
                    suggestion="Extract to sub-agent",
                )
            ],
        )
        assert not compliance.pattern_compliant
        assert len(compliance.violations) == 1

    def test_token_estimate_valid(self):
        """Test valid TokenEstimate."""
        estimate = TokenEstimate(
            improvement_id="CTX-001",
            before_tokens=5000,
            after_tokens=2000,
            reduction_tokens=3000,
            reduction_percent=60.0,
            confidence=0.8,
            method="pattern_based",
        )
        assert estimate.reduction_percent == 60.0
        assert estimate.method == "pattern_based"

    def test_token_estimate_validation(self):
        """Test TokenEstimate field validation."""
        # Valid
        estimate = TokenEstimate(
            improvement_id="CTX-001",
            before_tokens=1000,
            after_tokens=500,
            confidence=0.5,
        )
        assert estimate.before_tokens >= 0

        # Invalid: negative tokens
        with pytest.raises(ValidationError):
            TokenEstimate(
                improvement_id="CTX-001",
                before_tokens=-100,
                after_tokens=500,
            )

    def test_risk_assessment_valid(self):
        """Test valid RiskAssessment."""
        from context_engineering.models.grounding_outputs import BreakingChange

        assessment = RiskAssessment(
            improvement_id="ORCH-001",
            risk_level=RiskLevel.HIGH,
            breaking_changes=[
                BreakingChange(
                    description="Entry point changes",
                    affected_component="agents/main.md",
                    mitigation="Update invocations",
                )
            ],
            rollback_possible=True,
            rollback_complexity="moderate",
        )
        assert assessment.risk_level == RiskLevel.HIGH
        assert len(assessment.breaking_changes) == 1


class TestSynthesisOutputs:
    """Tests for synthesis output models."""

    def test_improvement_report_valid(self):
        """Test valid ImprovementReport."""
        from context_engineering.models.synthesis_outputs import (
            AppliedImprovement,
            BeforeAfterComparison,
            FileChange,
            ImprovementReport,
            NextStep,
        )

        report = ImprovementReport(
            executive_summary="Applied 2 improvements achieving 45% token reduction.",
            improvements_applied=[
                AppliedImprovement(
                    improvement_id="CTX-001",
                    description="Added context tier",
                    files_modified=["agents/analyzer.md"],
                    token_reduction=2000,
                )
            ],
            comparison=BeforeAfterComparison(),
            files_modified=[
                FileChange(
                    file_path="agents/analyzer.md",
                    change_type="modify",
                    description="Added tier spec",
                )
            ],
            total_improvements=5,
            applied_count=2,
            next_steps=[
                NextStep(
                    description="Run tests",
                    priority="HIGH",
                )
            ],
            plugin_name="test-plugin",
        )
        assert "45%" in report.executive_summary
        assert len(report.improvements_applied) == 1
        assert report.applied_count == 2

    def test_improvement_report_minimal(self):
        """Test minimal ImprovementReport."""
        from context_engineering.models.synthesis_outputs import ImprovementReport

        report = ImprovementReport(executive_summary="No improvements needed.")
        assert report.improvements_applied == []
        assert report.total_improvements == 0
