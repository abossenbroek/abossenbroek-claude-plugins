"""Tests for context engineering synthesis output validation."""

import pytest
from pydantic import ValidationError

from context_engineering.models import (
    BeforeAfterComparison,
    FileChange,
    ImprovementReport,
    TokenMetrics,
)
from context_engineering.models.synthesis_outputs import (
    AppliedImprovement,
    FileDiff,
    NextStep,
    PatternComplianceMetrics,
    TierCoverageMetrics,
)


class TestTokenMetricsModel:
    """Tests for TokenMetrics model."""

    def test_token_metrics_with_reduction(self):
        """Test TokenMetrics with positive reduction."""
        metrics = TokenMetrics(
            before=10000,
            after=4000,
            reduction=6000,
            reduction_percent=60.0,
        )
        assert metrics.before == 10000
        assert metrics.after == 4000
        assert metrics.reduction_percent == 60.0

    def test_token_metrics_minimal(self):
        """Test minimal TokenMetrics."""
        metrics = TokenMetrics(before=1000, after=1000)
        assert metrics.reduction == 0
        assert metrics.reduction_percent == 0.0

    def test_token_metrics_validation(self):
        """Test TokenMetrics validation."""
        # Invalid: negative before
        with pytest.raises(ValidationError):
            TokenMetrics(before=-100, after=100)

        # Invalid: negative after
        with pytest.raises(ValidationError):
            TokenMetrics(before=100, after=-100)


class TestBeforeAfterComparisonModel:
    """Tests for BeforeAfterComparison model."""

    def test_before_after_comparison_full(self):
        """Test full BeforeAfterComparison."""
        comparison = BeforeAfterComparison(
            total_tokens=TokenMetrics(
                before=50000,
                after=20000,
                reduction=30000,
                reduction_percent=60.0,
            ),
            pattern_compliance=PatternComplianceMetrics(
                before=0.4,
                after=0.9,
                improvement=0.5,
            ),
            tier_coverage=TierCoverageMetrics(
                before=0.2,
                after=0.95,
                improvement=0.75,
            ),
        )
        assert comparison.total_tokens.reduction_percent == 60.0
        assert comparison.pattern_compliance.after == 0.9
        assert comparison.tier_coverage.improvement == 0.75

    def test_before_after_comparison_defaults(self):
        """Test BeforeAfterComparison with defaults."""
        comparison = BeforeAfterComparison()
        assert comparison.total_tokens.before == 0
        assert comparison.pattern_compliance.before == 0.0
        assert comparison.tier_coverage.before == 0.0

    def test_pattern_compliance_metrics_range(self):
        """Test PatternComplianceMetrics range validation."""
        # Valid
        metrics = PatternComplianceMetrics(before=0.5, after=0.8, improvement=0.3)
        assert metrics.after == 0.8

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            PatternComplianceMetrics(before=0.5, after=1.5)

    def test_tier_coverage_metrics_range(self):
        """Test TierCoverageMetrics range validation."""
        # Valid
        metrics = TierCoverageMetrics(before=0.2, after=0.9, improvement=0.7)
        assert metrics.improvement == 0.7

        # Invalid: < 0.0
        with pytest.raises(ValidationError):
            TierCoverageMetrics(before=-0.1, after=0.5)


class TestFileChangeModel:
    """Tests for FileChange model."""

    def test_file_change_modify(self):
        """Test FileChange for modification."""
        change = FileChange(
            file_path="agents/coordinator.md",
            change_type="modify",
            description="Added context tier specification and NOT PASSED section",
            diff=FileDiff(
                before="## Input\nYou receive:\n- data",
                after="## Input\nYou receive (SELECTIVE):\n- summary\n\n**NOT PROVIDED**:\n- full data",
            ),
        )
        assert change.change_type == "modify"
        assert change.diff is not None
        assert "SELECTIVE" in change.diff.after

    def test_file_change_create(self):
        """Test FileChange for new file."""
        change = FileChange(
            file_path="coordinator-internal/new-agent.md",
            change_type="create",
            description="Created new sub-agent extracted from coordinator",
        )
        assert change.change_type == "create"
        assert change.diff is None

    def test_file_change_delete(self):
        """Test FileChange for deletion."""
        change = FileChange(
            file_path="agents/old-agent.md",
            change_type="delete",
            description="Removed deprecated agent",
        )
        assert change.change_type == "delete"


class TestAppliedImprovementModel:
    """Tests for AppliedImprovement model."""

    def test_applied_improvement_with_reduction(self):
        """Test AppliedImprovement with token reduction."""
        improvement = AppliedImprovement(
            improvement_id="CTX-001",
            description="Added context tier specification to analyzer",
            files_modified=["coordinator-internal/analyzer.md"],
            token_reduction=3000,
            risk_level="LOW",
        )
        assert improvement.token_reduction == 3000
        assert len(improvement.files_modified) == 1

    def test_applied_improvement_multiple_files(self):
        """Test AppliedImprovement affecting multiple files."""
        improvement = AppliedImprovement(
            improvement_id="ORCH-001",
            description="Implemented firewall architecture",
            files_modified=[
                "agents/main.md",
                "agents/coordinator.md",
                "coordinator-internal/analyzer.md",
            ],
            token_reduction=8000,
            risk_level="HIGH",
        )
        assert len(improvement.files_modified) == 3
        assert improvement.risk_level == "HIGH"


class TestNextStepModel:
    """Tests for NextStep model."""

    def test_next_step_high_priority(self):
        """Test high priority NextStep."""
        step = NextStep(
            description="Run validation tests to ensure changes don't break behavior",
            priority="HIGH",
            rationale="Changes affect core coordinator logic",
        )
        assert step.priority == "HIGH"
        assert step.rationale is not None

    def test_next_step_default_priority(self):
        """Test NextStep with default priority."""
        step = NextStep(description="Consider adding more tests")
        assert step.priority == "MEDIUM"


class TestImprovementReportModel:
    """Tests for ImprovementReport model."""

    def test_improvement_report_full(self):
        """Test full ImprovementReport."""
        report = ImprovementReport(
            executive_summary="Applied 3 improvements to red-agent achieving 45% token reduction. Added context tiers to 2 agents and implemented severity batching for grounding.",
            improvements_applied=[
                AppliedImprovement(
                    improvement_id="CTX-001",
                    description="Added context tier to analyzer",
                    files_modified=["coordinator-internal/analyzer.md"],
                    token_reduction=2500,
                    risk_level="LOW",
                ),
                AppliedImprovement(
                    improvement_id="CTX-002",
                    description="Added NOT PASSED section to coordinator",
                    files_modified=["agents/coordinator.md"],
                    token_reduction=1000,
                    risk_level="LOW",
                ),
                AppliedImprovement(
                    improvement_id="CTX-003",
                    description="Implemented severity batching",
                    files_modified=[
                        "agents/coordinator.md",
                        "coordinator-internal/grounding/checker.md",
                    ],
                    token_reduction=5000,
                    risk_level="MEDIUM",
                ),
            ],
            improvements_skipped=["CTX-004", "ORCH-001"],
            comparison=BeforeAfterComparison(
                total_tokens=TokenMetrics(
                    before=20000, after=11500, reduction=8500, reduction_percent=42.5
                ),
                pattern_compliance=PatternComplianceMetrics(
                    before=0.6, after=0.9, improvement=0.3
                ),
                tier_coverage=TierCoverageMetrics(
                    before=0.4, after=0.85, improvement=0.45
                ),
            ),
            files_modified=[
                FileChange(
                    file_path="coordinator-internal/analyzer.md",
                    change_type="modify",
                    description="Added tier spec",
                ),
                FileChange(
                    file_path="agents/coordinator.md",
                    change_type="modify",
                    description="Added NOT PASSED and severity batching",
                ),
            ],
            total_improvements=5,
            applied_count=3,
            skipped_count=2,
            next_steps=[
                NextStep(
                    description="Run uv run pytest to verify changes",
                    priority="HIGH",
                ),
                NextStep(
                    description="Consider implementing ORCH-001 for firewall pattern",
                    priority="MEDIUM",
                ),
            ],
            plugin_name="red-agent",
            analysis_mode="standard",
        )

        assert "45%" in report.executive_summary
        assert len(report.improvements_applied) == 3
        assert report.applied_count == 3
        assert report.skipped_count == 2
        assert report.comparison.total_tokens.reduction_percent == 42.5

    def test_improvement_report_no_improvements(self):
        """Test ImprovementReport with no improvements."""
        report = ImprovementReport(
            executive_summary="Plugin already follows all SOTA patterns. No improvements needed.",
            plugin_name="well-designed-plugin",
            analysis_mode="deep",
        )
        assert report.improvements_applied == []
        assert report.applied_count == 0
        assert report.files_modified == []

    def test_improvement_report_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            ImprovementReport(
                executive_summary="Test",
                unknown_field="should fail",
            )

    def test_improvement_report_metrics_integrity(self):
        """Test that report metrics are consistent."""
        # Create report with matching counts
        report = ImprovementReport(
            executive_summary="Applied 2 of 5 improvements.",
            improvements_applied=[
                AppliedImprovement(
                    improvement_id="CTX-001",
                    description="Test 1",
                ),
                AppliedImprovement(
                    improvement_id="CTX-002",
                    description="Test 2",
                ),
            ],
            improvements_skipped=["CTX-003", "CTX-004", "CTX-005"],
            total_improvements=5,
            applied_count=2,
            skipped_count=3,
        )

        # Verify counts match
        assert len(report.improvements_applied) == report.applied_count
        assert len(report.improvements_skipped) == report.skipped_count
        assert report.applied_count + report.skipped_count == report.total_improvements
