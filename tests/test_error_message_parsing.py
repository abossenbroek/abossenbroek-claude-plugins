"""Tests for error message quality and parseability.

Tests verify that validation error messages are:
- Actionable (contain field paths and hints)
- Parseable (structured format)
- Complete (all errors shown, no masking)
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
        sys.modules["hook_module_temp_errors"] = module
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


class TestRedAgentErrorMessages:
    """Test red-agent validation error message quality."""

    def test_field_path_in_error(self):
        """Test error messages contain field paths."""
        invalid = {}
        is_valid, errors = red_agent_hook.validate_output(invalid, "attacker")

        assert is_valid is False
        # Errors should reference specific field paths
        assert any("attack_results" in err for err in errors)

    def test_hints_are_actionable(self):
        """Test each error has actionable hint."""
        # Test missing field hint
        error = {"loc": ("agent_type",), "msg": "Field required", "type": "missing"}
        formatted = red_agent_hook.format_validation_error(error)

        assert "agent_type" in formatted
        assert "Hint:" in formatted
        assert "Add" in formatted

    def test_enum_error_has_hint(self):
        """Test enum validation errors have hints about valid values."""
        error = {
            "loc": ("severity",),
            "msg": "Input should be 'HIGH', 'MEDIUM', 'LOW'",
            "type": "enum",
        }
        formatted = red_agent_hook.format_validation_error(error)

        assert "severity" in formatted
        assert "Hint:" in formatted
        assert "valid values" in formatted.lower()

    def test_multiple_errors_separately_listed(self):
        """Test multiple errors are independently parseable."""
        # Create output with nested structure to trigger multiple errors
        invalid = {
            "attack_results": {
                # Missing attack_type, findings, summary
            }
        }
        is_valid, errors = red_agent_hook.validate_output(invalid, "attacker")

        assert is_valid is False
        # Should have multiple distinct error messages for missing fields
        assert len(errors) >= 2

        # Each error should be on its own line/item
        for error in errors:
            assert isinstance(error, str)
            assert len(error) > 0

    def test_different_error_types_have_hints(self):
        """Test different validation errors have appropriate hints."""
        # Missing field
        missing_error = {
            "loc": ("field",),
            "msg": "Field required",
            "type": "missing",
        }
        missing_formatted = red_agent_hook.format_validation_error(missing_error)
        assert "Add" in missing_formatted

        # Invalid enum
        enum_error = {"loc": ("field",), "msg": "Invalid enum", "type": "enum"}
        enum_formatted = red_agent_hook.format_validation_error(enum_error)
        assert "valid values" in enum_formatted.lower()

        # String too short
        short_error = {
            "loc": ("field",),
            "msg": "String too short",
            "type": "string_too_short",
        }
        short_formatted = red_agent_hook.format_validation_error(short_error)
        assert "more content" in short_formatted.lower()

        # All should have hints
        assert "Hint:" in missing_formatted
        assert "Hint:" in enum_formatted
        assert "Hint:" in short_formatted

    def test_nested_field_paths(self):
        """Test that nested field paths are shown correctly."""
        # Create invalid output with nested issue
        invalid = {
            "attack_results": {
                "attack_type": "reasoning-attacker",
                "findings": [
                    {
                        "id": "RF-001",
                        "severity": "INVALID",  # Invalid enum
                        # Missing other required fields
                    }
                ],
                "summary": {"total_findings": 1},
            }
        }

        is_valid, errors = red_agent_hook.validate_output(invalid, "attacker")
        assert is_valid is False

        # Should show nested paths like "findings.0.severity"
        error_text = " ".join(errors)
        assert "findings" in error_text.lower() or "severity" in error_text.lower()

    def test_no_generic_validation_failed_message(self):
        """Test that error messages are specific, not generic."""
        invalid = {}
        is_valid, errors = red_agent_hook.validate_output(invalid, "attacker")

        assert is_valid is False
        # Should not have generic messages
        for error in errors:
            # Should contain specific field names, not just "validation failed"
            assert (
                "attack_results" in error
                or "findings" in error
                or "summary" in error
                or any(field in error for field in ["agent", "type", "field"])
            )

    def test_error_count_limit(self):
        """Test that error messages don't overwhelm with too many errors."""
        # Create deeply invalid output with many errors
        invalid = {}
        is_valid, errors = red_agent_hook.validate_output(invalid, "attacker")

        assert is_valid is False
        # Errors should be limited to reasonable count (or paginated)
        # Current implementation shows all errors, but this tests it's manageable
        assert len(errors) > 0
        assert len(errors) < 100  # Sanity check


class TestContextEngineeringErrorMessages:
    """Test context-engineering validation error message quality."""

    def test_field_path_in_error(self):
        """Test error messages contain field paths."""
        invalid = yaml.dump({"plugin_analysis": {}})
        is_valid, message = context_engineering_hook.validate_agent_output(invalid)

        assert is_valid is False
        assert "INVALID" in message
        # Should reference specific fields
        assert any(
            field in message.lower()
            for field in ["plugin_name", "version", "tier", "agents"]
        )

    def test_hints_are_present(self):
        """Test error messages include hints."""
        error = {
            "loc": ("context_tier",),
            "msg": "Field required",
            "type": "missing",
        }
        formatted = context_engineering_hook.format_validation_error(error)

        assert "context_tier" in formatted
        assert "Hint:" in formatted
        assert "Add" in formatted

    def test_enum_error_shows_valid_values_hint(self):
        """Test enum errors have hints about valid values."""
        error = {
            "loc": ("context_tier",),
            "msg": "Invalid literal",
            "type": "literal_error",
        }
        formatted = context_engineering_hook.format_validation_error(error)

        assert "Hint:" in formatted
        assert "valid values" in formatted.lower()

    def test_multiple_errors_independently_listed(self):
        """Test multiple errors are shown independently."""
        # Create output with multiple issues
        invalid = yaml.dump(
            {
                "plugin_analysis": {
                    # Missing plugin_name, plugin_version, context_tier, agents, etc
                    "unknown_field": "value"
                }
            }
        )
        is_valid, message = context_engineering_hook.validate_agent_output(invalid)

        assert is_valid is False
        # Should list multiple errors
        assert "\n" in message  # Multiple lines
        error_indicators = message.count("-")  # Count bullet points
        assert error_indicators >= 2  # Multiple errors

    def test_agent_type_detection_failure_message(self):
        """Test clear message when agent type cannot be detected."""
        # YAML with unrecognized structure
        invalid = yaml.dump({"unknown_root": {"data": "value"}})
        is_valid, message = context_engineering_hook.validate_agent_output(invalid)

        assert is_valid is False
        assert "Cannot detect agent type" in message or "Root keys" in message

    def test_yaml_parse_error_message(self):
        """Test clear message for YAML parsing errors."""
        # Invalid YAML syntax
        invalid = "```yaml\ninvalid: yaml: :\n```"
        is_valid, message = context_engineering_hook.validate_agent_output(invalid)

        assert is_valid is False
        assert "YAML" in message.upper() or "yaml" in message.lower()


class TestErrorMessageFormatting:
    """Test general error message formatting utilities."""

    def test_format_validation_error_structure(self):
        """Test validation error formatting produces consistent structure."""
        error = {
            "loc": ("field", "nested"),
            "msg": "Test error message",
            "type": "test_error",
        }

        formatted = red_agent_hook.format_validation_error(error)

        # Should have field path
        assert "field.nested" in formatted
        # Should have error message
        assert "Test error message" in formatted
        # Should start with dash (bullet point)
        assert formatted.startswith("- ")

    def test_location_path_formatting(self):
        """Test that location paths are formatted correctly."""
        # Simple path
        error1 = {"loc": ("field",), "msg": "Error", "type": "test"}
        formatted1 = red_agent_hook.format_validation_error(error1)
        assert "field:" in formatted1

        # Nested path
        error2 = {
            "loc": ("parent", "child", "grandchild"),
            "msg": "Error",
            "type": "test",
        }
        formatted2 = red_agent_hook.format_validation_error(error2)
        assert "parent.child.grandchild" in formatted2

        # Array index path
        error3 = {"loc": ("items", 0, "field"), "msg": "Error", "type": "test"}
        formatted3 = red_agent_hook.format_validation_error(error3)
        assert "items.0.field" in formatted3
