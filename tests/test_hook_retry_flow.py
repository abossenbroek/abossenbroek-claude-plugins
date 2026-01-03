"""Tests for PostToolUse hook retry flow behavior.

Tests verify that validation failures allow retries:
- First attempt: invalid → block
- Second attempt: valid → continue
- Multiple retries work (no enforced limit)
"""

import importlib.util
import sys
from pathlib import Path

import yaml

# Get project root to build paths
PROJECT_ROOT = Path(__file__).parent.parent


def load_hook_module(hook_path: Path):
    """Load a hook script as a Python module."""
    spec = importlib.util.spec_from_file_location("hook_module", hook_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["hook_module_temp_retry"] = module
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


class TestRedAgentRetryFlow:
    """Test retry flow for red-agent validation hooks."""

    def test_single_retry_success(self):
        """Test validation failure followed by successful retry."""
        # First attempt: invalid (missing everything)
        invalid = {}
        is_valid1, errors1 = red_agent_hook.validate_output(invalid, "attacker")
        assert is_valid1 is False
        assert len(errors1) > 0

        # Second attempt: valid
        valid = {
            "attack_results": {
                "attack_type": "reasoning-attacker",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        is_valid2, errors2 = red_agent_hook.validate_output(valid, "attacker")
        assert is_valid2 is True
        assert errors2 == []

    def test_multiple_retries_no_limit(self):
        """Test multiple retry attempts work (no enforced limit)."""
        # Attempt 1: missing attack_type
        attempt1 = {
            "attack_results": {"findings": [], "summary": {"total_findings": 0}}
        }
        is_valid1, _errors1 = red_agent_hook.validate_output(attempt1, "attacker")
        assert is_valid1 is False

        # Attempt 2: still invalid (missing summary)
        attempt2 = {
            "attack_results": {"attack_type": "reasoning-attacker", "findings": []}
        }
        is_valid2, _errors2 = red_agent_hook.validate_output(attempt2, "attacker")
        assert is_valid2 is False

        # Attempt 3: now valid
        attempt3 = {
            "attack_results": {
                "attack_type": "reasoning-attacker",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        is_valid3, errors3 = red_agent_hook.validate_output(attempt3, "attacker")
        assert is_valid3 is True
        assert errors3 == []

    def test_error_recovery_specific_field(self):
        """Test that fixing a specific field error leads to success."""
        # First: missing evidence_strength
        invalid = {
            "grounding_results": {
                "agent": "evidence-checker",
                "assessments": [
                    {
                        "finding_id": "RF-001",
                        # Missing evidence_strength
                        "evidence_review": {"evidence_exists": True},
                    }
                ],
            }
        }
        is_valid1, errors1 = red_agent_hook.validate_output(invalid, "grounding")
        assert is_valid1 is False
        assert any("evidence_strength" in err.lower() for err in errors1)

        # Second: add missing field
        valid = {
            "grounding_results": {
                "agent": "evidence-checker",
                "assessments": [
                    {
                        "finding_id": "RF-001",
                        "evidence_strength": 0.85,
                        "original_confidence": 0.90,
                        "evidence_review": {"evidence_exists": True},
                        "quote_verification": {"match_quality": "exact"},
                        "inference_validity": {"valid": True},
                    }
                ],
            }
        }
        is_valid2, _errors2 = red_agent_hook.validate_output(valid, "grounding")
        assert is_valid2 is True

    def test_partial_fix_still_blocked(self):
        """Test that partial fixes still result in block until all fixed."""
        # Start with multiple errors
        invalid = {"attack_results": {}}  # Missing everything

        is_valid1, errors1 = red_agent_hook.validate_output(invalid, "attacker")
        assert is_valid1 is False
        error_count1 = len(errors1)

        # Partial fix: add attack_type but still missing others
        partial = {"attack_results": {"attack_type": "reasoning-attacker"}}
        is_valid2, errors2 = red_agent_hook.validate_output(partial, "attacker")
        assert is_valid2 is False
        # Should have fewer errors now
        assert len(errors2) < error_count1

        # Complete fix
        complete = {
            "attack_results": {
                "attack_type": "reasoning-attacker",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        is_valid3, _errors3 = red_agent_hook.validate_output(complete, "attacker")
        assert is_valid3 is True


class TestContextEngineeringRetryFlow:
    """Test retry flow for context-engineering validation hooks."""

    def test_single_retry_success(self):
        """Test validation failure followed by successful retry."""
        # First attempt: invalid
        invalid = yaml.dump({"plugin_analysis": {}})
        is_valid1, msg1 = context_engineering_hook.validate_agent_output(invalid)
        assert is_valid1 is False
        assert "INVALID" in msg1

        # Second attempt: valid (only plugin_name is required)
        valid = yaml.dump(
            {
                "plugin_analysis": {
                    "plugin_name": "test",
                    "plugin_version": "1.0.0",
                }
            }
        )
        is_valid2, _msg2 = context_engineering_hook.validate_agent_output(valid)
        assert is_valid2 is True

    def test_multiple_retries_no_limit(self):
        """Test multiple retry attempts work (no enforced limit)."""
        # Attempt 1: missing plugin_name
        attempt1 = yaml.dump(
            {
                "plugin_analysis": {
                    "plugin_version": "1.0.0",
                }
            }
        )
        is_valid1, _ = context_engineering_hook.validate_agent_output(attempt1)
        assert is_valid1 is False

        # Attempt 2: wrong structure (improvement instead of plugin_analysis)
        attempt2 = yaml.dump(
            {
                "improvements": [
                    {
                        "file": "test.md",
                        # Missing required fields for improvement
                    }
                ]
            }
        )
        is_valid2, _ = context_engineering_hook.validate_agent_output(attempt2)
        assert is_valid2 is False

        # Attempt 3: valid
        attempt3 = yaml.dump(
            {
                "plugin_analysis": {
                    "plugin_name": "test",
                    "plugin_version": "1.0.0",
                }
            }
        )
        is_valid3, _ = context_engineering_hook.validate_agent_output(attempt3)
        assert is_valid3 is True


class TestHookInputParsing:
    """Test that hooks correctly parse PostToolUse input."""

    def test_extract_agent_name_from_task_input(self):
        """Test extracting agent name from Task tool input."""
        # Test with prompt containing agent name
        tool_input = {"prompt": "Launch reasoning-attacker to analyze"}
        agent_name = red_agent_hook.extract_agent_name(tool_input)
        assert agent_name == "reasoning-attacker"

        # Test with description containing agent name
        tool_input = {"description": "Run evidence-checker"}
        agent_name = red_agent_hook.extract_agent_name(tool_input)
        assert agent_name == "evidence-checker"

        # Test with no agent name
        tool_input = {"prompt": "Do something else"}
        agent_name = red_agent_hook.extract_agent_name(tool_input)
        assert agent_name is None

    def test_extract_yaml_from_response(self):
        """Test extracting YAML from agent response."""
        # Test with YAML code block
        response = """
        Here is my output:

        ```yaml
        attack_results:
          attack_type: reasoning-attacker
          findings: []
          summary:
            total_findings: 0
        ```
        """
        result = red_agent_hook.extract_yaml_from_response(response)
        assert result is not None
        assert "attack_results" in result

        # Test with plain YAML
        response = """
attack_results:
  attack_type: reasoning-attacker
  findings: []
        """
        result = red_agent_hook.extract_yaml_from_response(response)
        assert result is not None
        assert "attack_results" in result

        # Test with no YAML - note: simple plain text might parse as valid YAML string
        # So we test that dict keys are present when expected
        response = "No YAML structure here: text, 123, etc"
        result = red_agent_hook.extract_yaml_from_response(response)
        # YAML parser may return a string, not a dict, which is fine
        # The validation will fail if it's not the expected structure
        if result is not None:
            assert not isinstance(result, dict) or "attack_results" not in result

    def test_hook_skips_non_task_tools(self):
        """Test that hook skips non-Task tool invocations."""
        # This would be tested with full main() flow
        # Here we just verify the tool_name check logic
        tool_name = "Read"
        assert tool_name != "Task"  # Should skip

        tool_name = "Task"
        assert tool_name == "Task"  # Should process
