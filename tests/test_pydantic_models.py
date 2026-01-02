"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from red_agent.models import (
    AnalysisMode,
    AttackerFinding,
    AttackerOutput,
    Confidence,
    Evidence,
    Finding,
    FindingSeverity,
    GroundingAssessment,
    GroundingNotes,
    GroundingOutput,
    Pattern,
    RedTeamReport,
    RiskCategory,
    RiskCategoryName,
    RiskOverview,
    Severity,
)


class TestEnums:
    """Tests for enum types."""

    def test_severity_values(self):
        """Test severity enum has expected values."""
        assert Severity.CRITICAL == "CRITICAL"
        assert Severity.HIGH == "HIGH"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.LOW == "LOW"
        assert Severity.INFO == "INFO"

    def test_finding_severity_excludes_info(self):
        """Test finding severity excludes INFO and NONE."""
        values = [e.value for e in FindingSeverity]
        assert "INFO" not in values
        assert "NONE" not in values

    def test_confidence_levels(self):
        """Test confidence enum has expected values."""
        assert Confidence.EXPLORING == "exploring"
        assert Confidence.CERTAIN == "certain"
        assert len(Confidence) == 7

    def test_risk_category_names(self):
        """Test all 10 risk categories exist."""
        assert len(RiskCategoryName) == 10
        assert RiskCategoryName.REASONING_FLAWS == "reasoning-flaws"

    def test_analysis_modes(self):
        """Test analysis mode enum."""
        assert AnalysisMode.QUICK == "quick"
        assert AnalysisMode.STANDARD == "standard"
        assert AnalysisMode.DEEP == "deep"


class TestEvidenceModel:
    """Tests for Evidence model."""

    def test_valid_evidence(self):
        """Test creating valid evidence."""
        evidence = Evidence(quote="test quote", source="test.md")
        assert evidence.quote == "test quote"
        assert evidence.source == "test.md"
        assert evidence.message_num is None

    def test_evidence_with_message_num(self):
        """Test evidence with message number."""
        evidence = Evidence(quote="test", source="test.md", message_num=5)
        assert evidence.message_num == 5


class TestGroundingNotesModel:
    """Tests for GroundingNotes model."""

    def test_valid_grounding_notes(self):
        """Test creating valid grounding notes."""
        notes = GroundingNotes(evidence_strength=0.85)
        assert notes.evidence_strength == 0.85

    def test_evidence_strength_out_of_range(self):
        """Test that evidence_strength must be 0-1."""
        with pytest.raises(ValidationError):
            GroundingNotes(evidence_strength=1.5)

        with pytest.raises(ValidationError):
            GroundingNotes(evidence_strength=-0.1)


class TestFindingModel:
    """Tests for Finding model."""

    def test_valid_finding(self):
        """Test creating valid finding."""
        finding = Finding(
            id="RF-001",
            category="reasoning-flaws",
            severity=FindingSeverity.HIGH,
            title="Test finding title",
            confidence="85%",
        )
        assert finding.id == "RF-001"
        assert finding.severity == FindingSeverity.HIGH

    def test_invalid_id_format(self):
        """Test that invalid ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Finding(
                id="invalid",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Test title here",
                confidence="85%",
            )
        assert "XX-NNN" in str(exc_info.value)

    def test_three_letter_id(self):
        """Test that 3-letter IDs are valid."""
        finding = Finding(
            id="ABC-123",
            category="test",
            severity=FindingSeverity.HIGH,
            title="Test title here",
            confidence="85%",
        )
        assert finding.id == "ABC-123"

    def test_invalid_confidence_format(self):
        """Test that invalid confidence format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Finding(
                id="RF-001",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Test title here",
                confidence="85",  # Missing %
            )
        assert "percentage" in str(exc_info.value).lower()

    def test_title_too_short(self):
        """Test that title must be at least 10 characters."""
        with pytest.raises(ValidationError):
            Finding(
                id="RF-001",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Short",  # Less than 10 chars
                confidence="85%",
            )


class TestPatternModel:
    """Tests for Pattern model."""

    def test_valid_pattern(self):
        """Test creating valid pattern."""
        pattern = Pattern(name="Test Pattern", description="A test pattern")
        assert pattern.name == "Test Pattern"
        assert pattern.instances == 1  # Default

    def test_instances_must_be_positive(self):
        """Test that instances must be >= 1."""
        with pytest.raises(ValidationError):
            Pattern(name="Test", description="Test", instances=0)


class TestRiskCategoryModel:
    """Tests for RiskCategory model."""

    def test_valid_risk_category(self):
        """Test creating valid risk category."""
        cat = RiskCategory(
            category=RiskCategoryName.REASONING_FLAWS, severity=Severity.HIGH
        )
        assert cat.category == RiskCategoryName.REASONING_FLAWS
        assert cat.count == 0  # Default

    def test_confidence_percentage_format(self):
        """Test that confidence must be percentage format."""
        cat = RiskCategory(
            category=RiskCategoryName.REASONING_FLAWS,
            severity=Severity.HIGH,
            confidence="85%",
        )
        assert cat.confidence == "85%"

    def test_invalid_confidence_format(self):
        """Test that invalid confidence format is rejected."""
        with pytest.raises(ValidationError):
            RiskCategory(
                category=RiskCategoryName.REASONING_FLAWS,
                severity=Severity.HIGH,
                confidence="invalid",
            )


class TestAttackerFindingModel:
    """Tests for AttackerFinding model."""

    def test_valid_attacker_finding_numeric_confidence(self):
        """Test attacker finding with numeric confidence."""
        finding = AttackerFinding(
            id="RF-001",
            severity="HIGH",
            title="Test",
            confidence=0.85,
            category="reasoning-flaws",
            target={"claim_id": "C-001"},
            evidence={"type": "logical_gap"},
            attack_applied={"style": "questioning", "probe": "Test probe"},
            impact={"if_exploited": "Test impact"},
            recommendation="Test recommendation text",
        )
        assert finding.confidence == 0.85

    def test_valid_attacker_finding_percentage_confidence(self):
        """Test attacker finding with percentage confidence."""
        finding = AttackerFinding(
            id="RF-001",
            severity="HIGH",
            title="Test",
            confidence="85%",
            category="reasoning-flaws",
            target={"claim_id": "C-001"},
            evidence={"type": "logical_gap"},
            attack_applied={"style": "questioning", "probe": "Test probe"},
            impact={"if_exploited": "Test impact"},
            recommendation="Test recommendation text",
        )
        assert finding.confidence == "85%"

    def test_numeric_confidence_out_of_range(self):
        """Test that numeric confidence must be 0-1."""
        with pytest.raises(ValidationError):
            AttackerFinding(
                id="RF-001",
                severity="HIGH",
                title="Test",
                confidence=2.0,
                category="reasoning-flaws",
                target={"claim_id": "C-001"},
                evidence={"type": "logical_gap"},
                attack_applied={"style": "questioning", "probe": "Test probe"},
                impact={"if_exploited": "Test impact"},
                recommendation="Test recommendation text",
            )

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError):
            AttackerFinding(id="RF-001", severity="HIGH", title="Test", confidence=0.85)


class TestAttackerOutputModel:
    """Tests for AttackerOutput model."""

    def test_valid_attacker_output(self, valid_attacker_output):
        """Test creating valid attacker output."""
        output = AttackerOutput.model_validate(valid_attacker_output)
        assert output.attack_results.attack_type == "reasoning-attacker"

    def test_missing_attack_results(self):
        """Test that missing attack_results is rejected."""
        with pytest.raises(ValidationError):
            AttackerOutput.model_validate({})


class TestGroundingAssessmentModel:
    """Tests for GroundingAssessment model."""

    def test_valid_assessment(self):
        """Test creating valid grounding assessment."""
        assessment = GroundingAssessment(
            finding_id="RF-001",
            evidence_strength=0.85,
            original_confidence=0.90,
            evidence_review={"evidence_exists": True},
            quote_verification={"match_quality": "exact"},
            inference_validity={"valid": True},
            adjusted_confidence=0.80,
        )
        assert assessment.evidence_strength == 0.85

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError):
            GroundingAssessment(
                finding_id="RF-001", evidence_strength=0.85, adjusted_confidence=0.80
            )


class TestGroundingOutputModel:
    """Tests for GroundingOutput model."""

    def test_valid_grounding_output(self, valid_grounding_output):
        """Test creating valid grounding output."""
        output = GroundingOutput.model_validate(valid_grounding_output)
        assert output.grounding_results.agent == "evidence-checker"


class TestRedTeamReportModel:
    """Tests for RedTeamReport model."""

    def test_valid_report(self, valid_report_output):
        """Test creating valid report."""
        report = RedTeamReport.model_validate(valid_report_output)
        assert report.risk_overview.overall_risk_level == Severity.HIGH

    def test_executive_summary_too_short(self):
        """Test that executive summary must be at least 50 chars."""
        with pytest.raises(ValidationError):
            RedTeamReport(
                executive_summary="Too short",
                risk_overview=RiskOverview(
                    overall_risk_level=Severity.LOW, categories=[]
                ),
                findings={},
            )
