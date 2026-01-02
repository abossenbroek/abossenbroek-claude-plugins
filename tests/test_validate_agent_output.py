"""Tests for validate_agent_output.py."""

from red_agent.scripts.validate_agent_output import (
    validate_attacker_output,
    validate_context_analysis,
    validate_final_report,
    validate_grounding_output,
    validate_output,
    validate_strategy_output,
)


class TestValidateAttackerOutput:
    """Tests for attacker output validation."""

    def test_valid_output(self, valid_attacker_output):
        """Test that valid attacker output passes validation."""
        result = validate_attacker_output(valid_attacker_output)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_attack_results(self, invalid_attacker_output_missing_root):
        """Test that missing attack_results is an error."""
        result = validate_attacker_output(invalid_attacker_output_missing_root)
        assert not result.is_valid
        assert any("attack_results" in e for e in result.errors)

    def test_invalid_finding_id_format(self):
        """Test that invalid finding ID format is an error."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "invalid-format",
                        "severity": "HIGH",
                        "title": "Test title here",
                        "confidence": 0.5,
                    }
                ],
            }
        }
        result = validate_attacker_output(data)
        assert not result.is_valid
        assert any("XX-NNN" in e or "format" in e.lower() for e in result.errors)

    def test_invalid_severity(self):
        """Test that invalid severity is an error."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "INVALID",
                        "title": "Test title here",
                        "confidence": 0.5,
                    }
                ],
            }
        }
        result = validate_attacker_output(data)
        assert not result.is_valid

    def test_confidence_out_of_range(self):
        """Test that confidence out of range is an error."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "HIGH",
                        "title": "Test title here",
                        "confidence": 2.0,  # Out of range
                    }
                ],
            }
        }
        result = validate_attacker_output(data)
        assert not result.is_valid

    def test_empty_findings_warning(self):
        """Test that empty findings list produces a warning."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        result = validate_attacker_output(data)
        assert result.is_valid  # Empty findings is a warning, not error
        assert any("No findings" in w for w in result.warnings)

    def test_missing_required_fields_is_error(self):
        """Test that missing required fields in findings causes validation error."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "HIGH",
                        "title": "Test title here",
                        "confidence": 0.5,
                        # Missing required fields
                    }
                ],
                "summary": {"total_findings": 1},
            }
        }
        result = validate_attacker_output(data)
        # Should have errors for missing required fields
        assert not result.is_valid
        assert any("category" in e.lower() for e in result.errors)

    def test_unknown_risk_category_warning(self):
        """Test that unknown risk category produces a warning."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "categories_probed": ["unknown-category"],
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        result = validate_attacker_output(data)
        assert any("Unknown risk category" in w for w in result.warnings)


class TestValidateGroundingOutput:
    """Tests for grounding output validation."""

    def test_valid_output(self, valid_grounding_output):
        """Test that valid grounding output passes validation."""
        result = validate_grounding_output(valid_grounding_output)
        assert result.is_valid

    def test_missing_grounding_results(self):
        """Test that missing grounding_results is an error."""
        result = validate_grounding_output({})
        assert not result.is_valid
        assert any("grounding_results" in e for e in result.errors)

    def test_missing_agent(self, invalid_grounding_output_missing_agent):
        """Test that missing agent field is an error."""
        result = validate_grounding_output(invalid_grounding_output_missing_agent)
        assert not result.is_valid
        assert any("agent" in e for e in result.errors)

    def test_evidence_strength_out_of_range(self):
        """Test that evidence_strength out of range is an error."""
        data = {
            "grounding_results": {
                "agent": "test",
                "assessments": [
                    {
                        "finding_id": "RF-001",
                        "evidence_strength": 1.5,
                        "original_confidence": 0.9,
                        "evidence_review": {"evidence_exists": True},
                        "quote_verification": {"match_quality": "exact"},
                        "inference_validity": {"valid": True},
                    }
                ],
            }
        }
        result = validate_grounding_output(data)
        assert not result.is_valid

    def test_missing_notes_warning(self):
        """Test that missing notes produces a warning."""
        data = {
            "grounding_results": {
                "agent": "test",
                "assessments": [
                    {
                        "finding_id": "RF-001",
                        "evidence_strength": 0.5,
                        "original_confidence": 0.8,
                        "evidence_review": {"evidence_exists": True},
                        "quote_verification": {"match_quality": "exact"},
                        "inference_validity": {"valid": True},
                    }
                ],
            }
        }
        result = validate_grounding_output(data)
        assert any("notes" in w for w in result.warnings)


class TestValidateContextAnalysis:
    """Tests for context analysis validation."""

    def test_valid_output(self, valid_context_output):
        """Test that valid context output passes validation."""
        result = validate_context_analysis(valid_context_output)
        assert result.is_valid

    def test_missing_context_analysis(self):
        """Test that missing context_analysis is an error."""
        result = validate_context_analysis({})
        assert not result.is_valid
        assert any("context_analysis" in e for e in result.errors)

    def test_missing_claim_id(self):
        """Test that missing claim_id is an error."""
        data = {"context_analysis": {"claim_analysis": [{"content": "test"}]}}
        result = validate_context_analysis(data)
        assert not result.is_valid


class TestValidateFinalReport:
    """Tests for final report validation."""

    def test_valid_output(self, valid_report_output):
        """Test that valid report passes validation."""
        result = validate_final_report(valid_report_output)
        assert result.is_valid

    def test_missing_executive_summary(self):
        """Test that missing executive_summary is an error."""
        data = {
            "risk_overview": {"overall_risk_level": "LOW", "categories": []},
            "findings": {},
        }
        result = validate_final_report(data)
        assert not result.is_valid
        assert any("executive_summary" in e for e in result.errors)

    def test_short_executive_summary_warning(self, invalid_report_output_short_summary):
        """Test that short executive summary produces a warning."""
        result = validate_final_report(invalid_report_output_short_summary)
        assert any("too short" in w for w in result.warnings)

    def test_invalid_risk_level(self):
        """Test that invalid risk level is an error."""
        data = {
            "executive_summary": "A" * 60,
            "risk_overview": {"overall_risk_level": "INVALID", "categories": []},
            "findings": {"critical": [], "high": [], "medium": [], "low": []},
        }
        result = validate_final_report(data)
        assert not result.is_valid

    def test_missing_limitations_warning(self):
        """Test that missing limitations produces a warning."""
        data = {
            "executive_summary": "A" * 60,
            "risk_overview": {"overall_risk_level": "LOW", "categories": []},
            "findings": {"critical": [], "high": [], "medium": [], "low": []},
        }
        result = validate_final_report(data)
        assert any("limitations" in w for w in result.warnings)


class TestValidateStrategyOutput:
    """Tests for strategy output validation."""

    def test_valid_output(self, valid_strategy_output):
        """Test that valid strategy output passes validation."""
        result = validate_strategy_output(valid_strategy_output)
        assert result.is_valid

    def test_missing_attack_strategy(self):
        """Test that missing attack_strategy is an error."""
        result = validate_strategy_output({})
        assert not result.is_valid
        assert any("attack_strategy" in e for e in result.errors)

    def test_missing_mode(self):
        """Test that missing mode is an error."""
        data = {"attack_strategy": {"total_vectors": 5}}
        result = validate_strategy_output(data)
        assert not result.is_valid
        assert any("mode" in e for e in result.errors)

    def test_empty_vectors_warning(self):
        """Test that empty selected_vectors produces a warning."""
        data = {
            "attack_strategy": {
                "mode": "quick",
                "total_vectors": 0,
                "selected_vectors": [],
            }
        }
        result = validate_strategy_output(data)
        assert result.is_valid  # Valid but with warning
        assert any("No attack vectors" in w for w in result.warnings)

    def test_minimal_valid_output(self, minimal_strategy_output):
        """Test that minimal strategy output passes validation."""
        result = validate_strategy_output(minimal_strategy_output)
        assert result.is_valid


class TestValidateOutput:
    """Tests for the generic validate_output function."""

    def test_unknown_output_type(self):
        """Test that unknown output type is an error."""
        result = validate_output({}, "unknown")
        assert not result.is_valid
        assert any("Unknown output type" in e for e in result.errors)

    def test_valid_types(
        self, valid_attacker_output, valid_grounding_output, valid_strategy_output
    ):
        """Test that valid types are accepted."""
        assert validate_output(valid_attacker_output, "attacker").is_valid
        assert validate_output(valid_grounding_output, "grounding").is_valid
        assert validate_output(valid_strategy_output, "strategy").is_valid
