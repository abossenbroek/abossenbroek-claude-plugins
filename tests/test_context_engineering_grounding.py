"""Tests for context engineering grounding output validation."""

import pytest
from pydantic import ValidationError

from context_engineering.models import (
    ChallengeAssessment,
    ChallengeValidity,
    ConsistencyCheck,
    PatternCompliance,
    PatternType,
    RiskAssessment,
    RiskLevel,
    TokenEstimate,
)
from context_engineering.models.grounding_outputs import (
    BreakingChange,
    ConflictDetail,
    DependencyDetail,
    GroundedImprovement,
    PatternViolationDetail,
    TokenBreakdown,
)


class TestPatternComplianceModel:
    """Tests for PatternCompliance model."""

    def test_pattern_compliance_compliant(self):
        """Test fully compliant PatternCompliance."""
        compliance = PatternCompliance(
            improvement_id="CTX-001",
            pattern_compliant=True,
            patterns_checked=[
                PatternType.FIREWALL,
                PatternType.HIERARCHICAL,
            ],
            confidence=0.95,
        )
        assert compliance.pattern_compliant
        assert len(compliance.patterns_checked) == 2
        assert compliance.confidence == 0.95

    def test_pattern_compliance_with_violations(self):
        """Test PatternCompliance with violations."""
        compliance = PatternCompliance(
            improvement_id="CTX-002",
            pattern_compliant=False,
            patterns_checked=[PatternType.FIREWALL],
            violations=[
                PatternViolationDetail(
                    pattern=PatternType.FIREWALL,
                    violation="Coordinator performs analysis",
                    location="lines 45-60",
                    suggestion="Extract analysis to sub-agent",
                )
            ],
            suggestions=[
                "Consider creating analyzer sub-agent",
                "Move analysis logic out of coordinator",
            ],
            confidence=0.85,
        )
        assert not compliance.pattern_compliant
        assert len(compliance.violations) == 1
        assert len(compliance.suggestions) == 2

    def test_pattern_compliance_confidence_range(self):
        """Test confidence must be 0.0-1.0."""
        # Valid
        compliance = PatternCompliance(
            improvement_id="CTX-001",
            pattern_compliant=True,
            confidence=0.5,
        )
        assert compliance.confidence == 0.5

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            PatternCompliance(
                improvement_id="CTX-001",
                pattern_compliant=True,
                confidence=1.5,
            )

    def test_pattern_violation_detail(self):
        """Test PatternViolationDetail model."""
        violation = PatternViolationDetail(
            pattern=PatternType.HIERARCHICAL,
            violation="Flat agent structure",
            location="plugin structure",
            suggestion="Add coordinator layer",
        )
        assert violation.pattern == PatternType.HIERARCHICAL


class TestTokenEstimateModel:
    """Tests for TokenEstimate model."""

    def test_token_estimate_full(self):
        """Test full TokenEstimate."""
        estimate = TokenEstimate(
            improvement_id="CTX-001",
            before_tokens=10000,
            after_tokens=4000,
            reduction_tokens=6000,
            reduction_percent=60.0,
            confidence=0.85,
            breakdown=[
                TokenBreakdown(
                    component="agent_prompt",
                    before=5000,
                    after=2000,
                    reduction=3000,
                    reduction_percent=60.0,
                ),
                TokenBreakdown(
                    component="handoff_payload",
                    before=5000,
                    after=2000,
                    reduction=3000,
                    reduction_percent=60.0,
                ),
            ],
            method="direct_count",
            notes="High confidence based on code comparison",
        )
        assert estimate.reduction_percent == 60.0
        assert len(estimate.breakdown) == 2
        assert estimate.method == "direct_count"

    def test_token_estimate_minimal(self):
        """Test minimal TokenEstimate."""
        estimate = TokenEstimate(
            improvement_id="CTX-001",
            before_tokens=1000,
            after_tokens=500,
        )
        assert estimate.reduction_tokens == 0  # Default
        assert estimate.confidence == 0.7  # Default

    def test_token_estimate_validation(self):
        """Test TokenEstimate validation."""
        # Invalid: negative tokens
        with pytest.raises(ValidationError):
            TokenEstimate(
                improvement_id="CTX-001",
                before_tokens=-100,
                after_tokens=500,
            )

    def test_token_breakdown(self):
        """Test TokenBreakdown model."""
        breakdown = TokenBreakdown(
            component="context_payload",
            before=2000,
            after=800,
            reduction=1200,
            reduction_percent=60.0,
        )
        assert breakdown.reduction == 1200


class TestConsistencyCheckModel:
    """Tests for ConsistencyCheck model."""

    def test_consistency_check_consistent(self):
        """Test fully consistent improvement."""
        check = ConsistencyCheck(
            improvement_id="CTX-001",
            is_internally_consistent=True,
            recommended_order=1,
        )
        assert check.is_internally_consistent
        assert check.conflicts_with == []
        assert check.depends_on == []

    def test_consistency_check_with_conflicts(self):
        """Test ConsistencyCheck with conflicts."""
        check = ConsistencyCheck(
            improvement_id="CTX-002",
            is_internally_consistent=True,
            conflicts_with=[
                ConflictDetail(
                    with_improvement_id="CTX-003",
                    conflict_type="overwrite",
                    description="Both modify same lines in coordinator.md",
                    resolution="Apply CTX-002 first, then adapt CTX-003",
                )
            ],
        )
        assert len(check.conflicts_with) == 1
        assert check.conflicts_with[0].conflict_type == "overwrite"

    def test_consistency_check_with_dependencies(self):
        """Test ConsistencyCheck with dependencies."""
        check = ConsistencyCheck(
            improvement_id="ORCH-002",
            is_internally_consistent=True,
            depends_on=[
                DependencyDetail(
                    requires_improvement_id="ORCH-001",
                    reason="ORCH-002 references sub-agent created by ORCH-001",
                    is_hard_dependency=True,
                )
            ],
            recommended_order=2,
        )
        assert len(check.depends_on) == 1
        assert check.depends_on[0].is_hard_dependency

    def test_consistency_check_internal_issues(self):
        """Test ConsistencyCheck with internal issues."""
        check = ConsistencyCheck(
            improvement_id="HO-001",
            is_internally_consistent=False,
            consistency_issues=[
                "before/after code doesn't match description",
                "Referenced file doesn't exist",
            ],
        )
        assert not check.is_internally_consistent
        assert len(check.consistency_issues) == 2


class TestRiskAssessmentModel:
    """Tests for RiskAssessment model."""

    def test_risk_assessment_low_risk(self):
        """Test low risk assessment."""
        assessment = RiskAssessment(
            improvement_id="CTX-001",
            risk_level=RiskLevel.LOW,
            rollback_possible=True,
            rollback_complexity="simple",
            confidence=0.9,
        )
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.rollback_possible

    def test_risk_assessment_high_risk(self):
        """Test high risk assessment with breaking changes."""
        assessment = RiskAssessment(
            improvement_id="ORCH-001",
            risk_level=RiskLevel.HIGH,
            breaking_changes=[
                BreakingChange(
                    description="Entry point renamed from main.md to coordinator.md",
                    affected_component="agents/main.md",
                    mitigation="Update all invocations to use new name",
                ),
                BreakingChange(
                    description="Sub-agent files moved to coordinator-internal/",
                    affected_component="agents/analyzer.md",
                    mitigation="Update import paths",
                ),
            ],
            rollback_possible=True,
            rollback_complexity="moderate",
            mitigation_strategy="Apply changes incrementally with feature flags",
            testing_required=[
                "Test all command invocations",
                "Verify sub-agent calls work",
                "Run full integration test",
            ],
            confidence=0.8,
        )
        assert assessment.risk_level == RiskLevel.HIGH
        assert len(assessment.breaking_changes) == 2
        assert len(assessment.testing_required) == 3

    def test_risk_assessment_critical(self):
        """Test critical risk assessment."""
        assessment = RiskAssessment(
            improvement_id="ORCH-002",
            risk_level=RiskLevel.CRITICAL,
            breaking_changes=[
                BreakingChange(
                    description="Changes plugin manifest structure",
                    affected_component="plugin.json",
                )
            ],
            rollback_possible=False,
            notes="Requires manual intervention to rollback",
        )
        assert assessment.risk_level == RiskLevel.CRITICAL
        assert not assessment.rollback_possible


class TestGroundedImprovementModel:
    """Tests for GroundedImprovement model."""

    def test_grounded_improvement_full(self):
        """Test fully grounded improvement."""
        grounded = GroundedImprovement(
            improvement_id="CTX-001",
            improvement_description="Add context tier specification",
            improvement_type="TIER_SPEC",
            pattern_compliance=PatternCompliance(
                improvement_id="CTX-001",
                pattern_compliant=True,
            ),
            token_estimate=TokenEstimate(
                improvement_id="CTX-001",
                before_tokens=5000,
                after_tokens=2000,
            ),
            consistency_check=ConsistencyCheck(
                improvement_id="CTX-001",
                is_internally_consistent=True,
            ),
            risk_assessment=RiskAssessment(
                improvement_id="CTX-001",
                risk_level=RiskLevel.LOW,
            ),
            is_approved=True,
        )
        assert grounded.is_approved
        assert grounded.pattern_compliance is not None
        assert grounded.token_estimate is not None

    def test_grounded_improvement_partial(self):
        """Test partially grounded improvement (severity batching)."""
        # For MEDIUM priority, only pattern and token checked
        grounded = GroundedImprovement(
            improvement_id="CTX-002",
            improvement_description="Add NOT PASSED section",
            improvement_type="NOT_PASSED",
            pattern_compliance=PatternCompliance(
                improvement_id="CTX-002",
                pattern_compliant=True,
            ),
            token_estimate=TokenEstimate(
                improvement_id="CTX-002",
                before_tokens=1000,
                after_tokens=950,
            ),
            # consistency_check and risk_assessment are None (not checked)
            is_approved=True,
        )
        assert grounded.consistency_check is None
        assert grounded.risk_assessment is None

    def test_grounded_improvement_rejected(self):
        """Test rejected improvement."""
        grounded = GroundedImprovement(
            improvement_id="ORCH-003",
            improvement_description="Restructure all agents",
            improvement_type="FIREWALL",
            pattern_compliance=PatternCompliance(
                improvement_id="ORCH-003",
                pattern_compliant=False,
                violations=[
                    PatternViolationDetail(
                        pattern=PatternType.FIREWALL,
                        violation="Proposed structure breaks isolation",
                    )
                ],
            ),
            is_approved=False,
            approval_notes="Pattern compliance failed - revise approach",
        )
        assert not grounded.is_approved
        assert grounded.approval_notes is not None


class TestChallengeAssessmentModel:
    """Tests for ChallengeAssessment model."""

    def test_challenge_validity_enum(self):
        """Test ChallengeValidity enum has expected values."""
        assert ChallengeValidity.SUPPORTED == "SUPPORTED"
        assert ChallengeValidity.UNSUPPORTED == "UNSUPPORTED"
        assert ChallengeValidity.UNCERTAIN == "UNCERTAIN"
        # Verify only 3 values
        assert len(ChallengeValidity) == 3

    def test_challenge_assessment_supported(self):
        """Test challenge assessment with supported claim."""
        assessment = ChallengeAssessment(
            improvement_id="CTX-001",
            claim="Will reduce tokens by 30%",
            validity=ChallengeValidity.SUPPORTED,
            evidence_strength=0.85,
            gaps=[],
            alternatives=[],
            required_evidence=[],
        )
        assert assessment.validity == ChallengeValidity.SUPPORTED
        assert assessment.evidence_strength == 0.85
        assert assessment.gaps == []

    def test_challenge_assessment_unsupported(self):
        """Test challenge assessment with unsupported claim."""
        assessment = ChallengeAssessment(
            improvement_id="CTX-002",
            claim="Will eliminate all context pollution",
            validity=ChallengeValidity.UNSUPPORTED,
            evidence_strength=0.2,
            gaps=[
                "No baseline measurement provided",
                "No after measurement methodology",
            ],
            alternatives=[
                "May reduce some pollution but not all",
                "Improvement may be marginal",
            ],
            required_evidence=[
                "Token counts before/after",
                "Context flow analysis",
            ],
        )
        assert assessment.validity == ChallengeValidity.UNSUPPORTED
        assert assessment.evidence_strength == 0.2
        assert len(assessment.gaps) == 2
        assert len(assessment.alternatives) == 2
        assert len(assessment.required_evidence) == 2

    def test_challenge_assessment_uncertain(self):
        """Test challenge assessment with uncertain claim."""
        assessment = ChallengeAssessment(
            improvement_id="ORCH-001",
            claim="Will improve agent hierarchy",
            validity=ChallengeValidity.UNCERTAIN,
            evidence_strength=0.5,
            gaps=["Unclear success criteria", "No comparison provided"],
            alternatives=["May improve or may not change behavior"],
            required_evidence=["Hierarchy diagrams before/after"],
        )
        assert assessment.validity == ChallengeValidity.UNCERTAIN
        assert assessment.evidence_strength == 0.5

    def test_evidence_strength_range(self):
        """Test evidence_strength must be 0.0-1.0."""
        # Test minimum valid value (0.0)
        assessment = ChallengeAssessment(
            improvement_id="CTX-001",
            claim="Test claim",
            validity=ChallengeValidity.UNCERTAIN,
            evidence_strength=0.0,
            gaps=[],
            alternatives=[],
            required_evidence=[],
        )
        assert assessment.evidence_strength == 0.0

        # Test maximum valid value (1.0)
        assessment = ChallengeAssessment(
            improvement_id="CTX-002",
            claim="Test claim",
            validity=ChallengeValidity.SUPPORTED,
            evidence_strength=1.0,
            gaps=[],
            alternatives=[],
            required_evidence=[],
        )
        assert assessment.evidence_strength == 1.0

        # Test invalid value below minimum
        with pytest.raises(ValidationError):
            ChallengeAssessment(
                improvement_id="CTX-003",
                claim="Test claim",
                validity=ChallengeValidity.UNCERTAIN,
                evidence_strength=-0.1,
                gaps=[],
                alternatives=[],
                required_evidence=[],
            )

        # Test invalid value above maximum
        with pytest.raises(ValidationError):
            ChallengeAssessment(
                improvement_id="CTX-004",
                claim="Test claim",
                validity=ChallengeValidity.SUPPORTED,
                evidence_strength=1.5,
                gaps=[],
                alternatives=[],
                required_evidence=[],
            )

    def test_challenge_assessment_all_fields(self):
        """Test challenge assessment with all fields populated."""
        assessment = ChallengeAssessment(
            improvement_id="HO-001",
            claim="Will standardize handoff schemas across all agents",
            validity=ChallengeValidity.SUPPORTED,
            evidence_strength=0.9,
            gaps=["Testing methodology not specified"],
            alternatives=[],
            required_evidence=["Integration test results"],
        )
        assert assessment.improvement_id == "HO-001"
        assert "standardize handoff schemas" in assessment.claim
        assert assessment.validity == ChallengeValidity.SUPPORTED
        assert assessment.evidence_strength == 0.9
        assert len(assessment.gaps) == 1
        assert assessment.alternatives == []
        assert len(assessment.required_evidence) == 1
