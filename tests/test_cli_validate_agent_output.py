"""CLI integration tests for validate_agent_output."""

from pathlib import Path
from typing import Any

import pytest
import yaml


class TestValidateAgentOutputCLI:
    """CLI integration tests for validate_agent_output script."""

    def test_valid_attacker_output_file(
        self,
        yaml_fixture_path,
        valid_attacker_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI with valid attacker output file."""
        path = yaml_fixture_path(valid_attacker_output, "attacker.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        assert result.returncode == 0
        assert "passed" in result.stdout.lower() or "valid" in result.stdout.lower()

    def test_valid_grounding_output_file(
        self,
        yaml_fixture_path,
        valid_grounding_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI with valid grounding output file."""
        path = yaml_fixture_path(valid_grounding_output, "grounding.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "grounding", "--input", str(path)],
        )
        assert result.returncode == 0

    def test_valid_context_output_file(
        self,
        yaml_fixture_path,
        valid_context_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI with valid context output file."""
        path = yaml_fixture_path(valid_context_output, "context.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "context", "--input", str(path)],
        )
        assert result.returncode == 0

    def test_valid_report_output_file(
        self,
        yaml_fixture_path,
        valid_report_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI with valid report output file."""
        path = yaml_fixture_path(valid_report_output, "report.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "report", "--input", str(path)],
        )
        assert result.returncode == 0

    def test_valid_strategy_output_file(
        self,
        yaml_fixture_path,
        valid_strategy_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI with valid strategy output file."""
        path = yaml_fixture_path(valid_strategy_output, "strategy.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "strategy", "--input", str(path)],
        )
        assert result.returncode == 0

    def test_missing_required_field(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test CLI with invalid output missing required field."""
        path = yaml_fixture_path({"wrong": "data"}, "invalid.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower()

    def test_file_not_found(self, run_cli):
        """Test CLI with nonexistent file."""
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", "/nonexistent/file.yaml"],
        )
        assert result.returncode == 1
        assert "not found" in result.stdout.lower()

    def test_stdin_input(
        self,
        valid_attacker_output: dict[str, Any],
        run_cli,
    ):
        """Test CLI reading from stdin."""
        yaml_str = yaml.dump(valid_attacker_output)
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", "-"],
            input_text=yaml_str,
        )
        assert result.returncode == 0

    def test_stdin_invalid_yaml(self, run_cli):
        """Test CLI with invalid YAML from stdin."""
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", "-"],
            input_text="invalid: yaml: content: [",
        )
        assert result.returncode == 1
        assert "yaml" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_strict_mode_with_warnings(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test --strict flag treats warnings as errors."""
        # Create output with empty findings (produces warning)
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        path = yaml_fixture_path(data, "warning.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path), "--strict"],
        )
        # With --strict, warnings become errors -> returncode 1
        assert result.returncode == 1

    def test_strict_mode_without_warnings(
        self,
        yaml_fixture_path,
        valid_attacker_output: dict[str, Any],
        run_cli,
    ):
        """Test --strict flag passes when no warnings."""
        path = yaml_fixture_path(valid_attacker_output, "valid.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path), "--strict"],
        )
        assert result.returncode == 0

    def test_short_flag_t(
        self,
        yaml_fixture_path,
        valid_attacker_output: dict[str, Any],
        run_cli,
    ):
        """Test -t short flag for type."""
        path = yaml_fixture_path(valid_attacker_output, "test.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["-t", "attacker", "-i", str(path)],
        )
        assert result.returncode == 0

    def test_short_flag_s(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test -s short flag for strict."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        path = yaml_fixture_path(data, "warning.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["-t", "attacker", "-i", str(path), "-s"],
        )
        assert result.returncode == 1

    def test_missing_required_args(self, run_cli):
        """Test CLI fails without required arguments."""
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            [],
        )
        assert result.returncode != 0

    def test_invalid_type_argument(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test CLI fails with invalid type argument."""
        path = yaml_fixture_path({"test": "data"}, "test.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "invalid_type", "--input", str(path)],
        )
        assert result.returncode != 0


class TestValidateAgentOutputCLIValidationDetails:
    """Tests for specific validation error messages in CLI output."""

    def test_invalid_finding_id_format_message(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that invalid finding ID format shows in CLI output."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "invalid-format",
                        "severity": "HIGH",
                        "title": "Test title that is long enough",
                        "confidence": 0.5,
                        "category": "test",
                        "target": {},
                        "evidence": {"type": "test"},
                        "attack_applied": {"style": "test", "probe": "test"},
                        "impact": {},
                        "recommendation": "Test recommendation that is long enough",
                    }
                ],
                "summary": {"total_findings": 1},
            }
        }
        path = yaml_fixture_path(data, "invalid_id.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        assert result.returncode == 1
        assert "XX-NNN" in result.stdout or "format" in result.stdout.lower()

    def test_invalid_severity_message(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that invalid severity shows in CLI output."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "INVALID_SEVERITY",
                        "title": "Test title that is long enough",
                        "confidence": 0.5,
                        "category": "test",
                        "target": {},
                        "evidence": {"type": "test"},
                        "attack_applied": {"style": "test", "probe": "test"},
                        "impact": {},
                        "recommendation": "Test recommendation that is long enough",
                    }
                ],
                "summary": {"total_findings": 1},
            }
        }
        path = yaml_fixture_path(data, "invalid_severity.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        assert result.returncode == 1

    def test_confidence_out_of_range_message(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that out-of-range confidence shows in CLI output."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "HIGH",
                        "title": "Test title that is long enough",
                        "confidence": 2.5,  # Out of range
                        "category": "test",
                        "target": {},
                        "evidence": {"type": "test"},
                        "attack_applied": {"style": "test", "probe": "test"},
                        "impact": {},
                        "recommendation": "Test recommendation that is long enough",
                    }
                ],
                "summary": {"total_findings": 1},
            }
        }
        path = yaml_fixture_path(data, "invalid_confidence.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        assert result.returncode == 1

    def test_grounding_missing_agent_message(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that missing grounding agent shows in CLI output."""
        data = {"grounding_results": {"assessments": []}}
        path = yaml_fixture_path(data, "missing_agent.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "grounding", "--input", str(path)],
        )
        assert result.returncode == 1
        assert "agent" in result.stdout.lower()

    def test_report_missing_executive_summary(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that missing executive_summary shows in CLI output."""
        data = {
            "risk_overview": {"overall_risk_level": "LOW", "categories": []},
            "findings": {},
        }
        path = yaml_fixture_path(data, "missing_summary.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "report", "--input", str(path)],
        )
        assert result.returncode == 1
        assert "executive_summary" in result.stdout.lower()

    def test_strategy_missing_mode(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that missing strategy mode shows in CLI output."""
        data = {"attack_strategy": {"total_vectors": 5}}
        path = yaml_fixture_path(data, "missing_mode.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "strategy", "--input", str(path)],
        )
        assert result.returncode == 1
        assert "mode" in result.stdout.lower()


class TestValidateAgentOutputCLIWarnings:
    """Tests for warning generation in CLI output."""

    def test_empty_findings_warning(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that empty findings list produces warning in CLI output."""
        data = {
            "attack_results": {
                "attack_type": "test",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        path = yaml_fixture_path(data, "empty_findings.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "attacker", "--input", str(path)],
        )
        # Should pass but with warnings
        assert result.returncode == 0
        assert "warning" in result.stdout.lower()

    def test_short_summary_warning(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that short executive summary produces warning."""
        data = {
            "executive_summary": "Too short",
            "risk_overview": {"overall_risk_level": "LOW", "categories": []},
            "findings": {"critical": [], "high": [], "medium": [], "low": []},
        }
        path = yaml_fixture_path(data, "short_summary.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "report", "--input", str(path)],
        )
        assert "warning" in result.stdout.lower() or "short" in result.stdout.lower()

    def test_missing_limitations_warning(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that missing limitations produces warning."""
        data = {
            "executive_summary": "A" * 60,  # Long enough
            "risk_overview": {"overall_risk_level": "LOW", "categories": []},
            "findings": {"critical": [], "high": [], "medium": [], "low": []},
        }
        path = yaml_fixture_path(data, "no_limitations.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "report", "--input", str(path)],
        )
        assert "warning" in result.stdout.lower()

    def test_empty_vectors_warning(
        self,
        yaml_fixture_path,
        run_cli,
    ):
        """Test that empty selected_vectors produces warning."""
        data = {
            "attack_strategy": {
                "mode": "quick",
                "total_vectors": 0,
                "selected_vectors": [],
            }
        }
        path = yaml_fixture_path(data, "empty_vectors.yaml")
        result = run_cli(
            "red_agent.scripts.validate_agent_output",
            ["--type", "strategy", "--input", str(path)],
        )
        assert result.returncode == 0
        assert "warning" in result.stdout.lower()
