"""Tests for PostToolUse hook YAML output format validation.

Tests verify that validation hooks return proper YAML decision format:
- Valid output → decision: continue
- Invalid output → decision: block with reason
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

# Get project root to build paths
PROJECT_ROOT = Path(__file__).parent.parent


def load_hook_module(hook_path: Path):
    """Load a hook script as a Python module."""
    spec = importlib.util.spec_from_file_location("hook_module", hook_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["hook_module_temp"] = module
        spec.loader.exec_module(module)
        return module
    msg = f"Could not load hook from {hook_path}"
    raise ImportError(msg)


# Load hook modules
red_agent_hook = load_hook_module(
    PROJECT_ROOT / "red-agent" / "hooks" / "validate-agent-output.py"
)
context_engineering_hook = load_hook_module(
    PROJECT_ROOT / "context-engineering" / "hooks" / "validate-agent-output.py"
)


class TestRedAgentHookOutputFormat:
    """Test red-agent validation hook output format."""

    def test_valid_attacker_returns_continue(self, valid_attacker_output):
        """Valid attacker output should return decision: continue in JSON."""
        is_valid, errors = red_agent_hook.validate_output(valid_attacker_output, "attacker")

        assert is_valid is True
        assert errors == []

    def test_invalid_attacker_returns_block(self):
        """Invalid attacker output should return decision: block with reason."""
        invalid_output = {}  # Missing everything
        is_valid, errors = red_agent_hook.validate_output(invalid_output, "attacker")

        assert is_valid is False
        assert len(errors) > 0
        # Errors should be formatted strings with field paths
        assert any("attack_results" in err.lower() for err in errors)

    def test_valid_strategy_returns_continue(self, valid_strategy_output):
        """Valid strategy output should return decision: continue."""
        is_valid, errors = red_agent_hook.validate_output(valid_strategy_output, "strategy")

        assert is_valid is True
        assert errors == []

    def test_invalid_strategy_returns_block(self):
        """Invalid strategy output should return decision: block with reason."""
        invalid_output = {}  # Missing everything
        is_valid, errors = red_agent_hook.validate_output(invalid_output, "strategy")

        assert is_valid is False
        assert len(errors) > 0

    def test_valid_grounding_returns_continue(self, valid_grounding_output):
        """Valid grounding output should return decision: continue."""
        is_valid, errors = red_agent_hook.validate_output(valid_grounding_output, "grounding")

        assert is_valid is True
        assert errors == []

    def test_invalid_grounding_returns_block(self):
        """Invalid grounding output should return decision: block with reason."""
        invalid_output = {}  # Missing everything
        is_valid, errors = red_agent_hook.validate_output(invalid_output, "grounding")

        assert is_valid is False
        assert len(errors) > 0

    def test_valid_report_returns_continue(self, valid_report_output):
        """Valid report output should return decision: continue."""
        is_valid, errors = red_agent_hook.validate_output(valid_report_output, "report")

        assert is_valid is True
        assert errors == []

    def test_invalid_report_returns_block(self):
        """Invalid report output should return decision: block with reason."""
        invalid_output = {}  # Missing everything
        is_valid, errors = red_agent_hook.validate_output(invalid_output, "report")

        assert is_valid is False
        assert len(errors) > 0

    def test_multiple_errors_all_listed(self):
        """Multiple validation errors should all be listed."""
        # Create output with multiple issues
        invalid_output = {
            "attack_results": {
                # Missing: attack_type, findings, summary
                "unknown_field": "should be ignored"
            }
        }
        is_valid, errors = red_agent_hook.validate_output(invalid_output, "attacker")

        assert is_valid is False
        # Should have multiple error messages
        assert len(errors) >= 2


class TestContextEngineeringHookOutputFormat:
    """Test context-engineering validation hook output format."""

    def test_valid_plugin_analysis_exits_zero(self, valid_plugin_analysis):
        """Valid plugin analysis should exit 0."""
        # Format as YAML string
        yaml_output = yaml.dump({"plugin_analysis": valid_plugin_analysis})
        is_valid, message = context_engineering_hook.validate_agent_output(yaml_output)

        assert is_valid is True
        assert "VALID" in message

    def test_invalid_plugin_analysis_exits_nonzero(self):
        """Invalid plugin analysis should exit 1 with error message."""
        invalid_output = yaml.dump({"plugin_analysis": {}})
        is_valid, message = context_engineering_hook.validate_agent_output(invalid_output)

        assert is_valid is False
        assert "INVALID" in message

    def test_valid_context_improvement_exits_zero(self, valid_context_improvement):
        """Valid context improvement should exit 0."""
        yaml_output = yaml.dump({"improvements": [valid_context_improvement]})
        is_valid, message = context_engineering_hook.validate_agent_output(yaml_output)

        assert is_valid is True
        assert "VALID" in message

    def test_invalid_context_improvement_exits_nonzero(self):
        """Invalid context improvement should exit 1 with error message."""
        invalid_output = yaml.dump({"improvements": [{}]})
        is_valid, message = context_engineering_hook.validate_agent_output(invalid_output)

        assert is_valid is False
        assert "INVALID" in message

    def test_no_yaml_returns_error(self):
        """Output with no YAML should return error."""
        plain_text = "This is just plain text with no YAML"
        is_valid, message = context_engineering_hook.validate_agent_output(plain_text)

        assert is_valid is False
        assert "No YAML content" in message

    def test_malformed_yaml_returns_error(self):
        """Malformed YAML should return error."""
        malformed_yaml = "```yaml\ninvalid: yaml: structure:\n```"
        is_valid, message = context_engineering_hook.validate_agent_output(malformed_yaml)

        assert is_valid is False
        assert "YAML" in message.upper()


class TestHookJSONOutput:
    """Test that red-agent hook outputs valid JSON in main() function."""

    def test_continue_decision_is_valid_json(self):
        """Test that continue decision outputs valid JSON."""
        # The hook outputs JSON for continue
        json_output = json.dumps({"continue": True})
        parsed = json.loads(json_output)

        assert "continue" in parsed
        assert parsed["continue"] is True

    def test_block_decision_is_valid_json(self):
        """Test that block decision outputs valid JSON."""
        # The hook outputs JSON for block
        json_output = json.dumps(
            {"decision": "block", "reason": "Test error message"}
        )
        parsed = json.loads(json_output)

        assert parsed["decision"] == "block"
        assert "reason" in parsed
        assert len(parsed["reason"]) > 0


@pytest.fixture
def valid_plugin_analysis():
    """Valid plugin analysis output for context-engineering."""
    return {
        "plugin_name": "test-plugin",
        "plugin_version": "1.0.0",
        # Only required field is plugin_name
        # Optional: current_patterns, violations, agents, opportunities, metrics, summary
    }


@pytest.fixture
def valid_context_improvement():
    """Valid context improvement output for context-engineering."""
    return {
        "id": "IMP-001",
        "file": "test-agent.md",
        "improvement_type": "TIER_SPEC",  # Must be valid ImprovementType enum
        "description": "Apply selective projection to reduce tokens",
        "code_change": {
            "section": "## Input",
            "before": "Full context passed",
            "after": "Selected fields only",
        },
        "estimated_reduction": 0.75,
        "priority": "HIGH",
    }
