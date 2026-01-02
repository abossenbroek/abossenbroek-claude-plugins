"""Tests for validate_agent_files.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_agent_files import load_json, validate_plugin_references


class TestLoadJson:
    """Tests for load_json function."""

    def test_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"name": "test"}')
        data = load_json(file_path)
        assert data == {"name": "test"}

    def test_invalid_json_returns_none(self, tmp_path):
        """Test that invalid JSON returns None."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{invalid json")
        assert load_json(file_path) is None

    def test_missing_file_returns_none(self, tmp_path):
        """Test that missing file returns None."""
        file_path = tmp_path / "nonexistent.json"
        assert load_json(file_path) is None


class TestValidatePluginReferences:
    """Tests for validate_plugin_references function."""

    @pytest.fixture
    def plugin_structure(self, tmp_path):
        """Create a basic plugin directory structure."""
        plugin_dir = tmp_path / "test-plugin"
        claude_plugin_dir = plugin_dir / ".claude-plugin"
        agents_dir = plugin_dir / "agents"
        commands_dir = plugin_dir / "commands"
        hooks_dir = plugin_dir / "hooks"

        claude_plugin_dir.mkdir(parents=True)
        agents_dir.mkdir()
        commands_dir.mkdir()
        hooks_dir.mkdir()

        return {
            "plugin_dir": plugin_dir,
            "plugin_json": claude_plugin_dir / "plugin.json",
            "agents_dir": agents_dir,
            "commands_dir": commands_dir,
            "hooks_dir": hooks_dir,
        }

    def test_valid_plugin_with_all_files(self, plugin_structure):
        """Test plugin where all referenced files exist."""
        # Create agent file
        agent_file = plugin_structure["agents_dir"] / "my-agent.md"
        agent_file.write_text("# Agent")

        # Create command file
        cmd_file = plugin_structure["commands_dir"] / "cmd.md"
        cmd_file.write_text("# Command")

        # Create hooks file
        hooks_file = plugin_structure["hooks_dir"] / "hooks.json"
        hooks_file.write_text("{}")

        # Create plugin.json
        plugin_data = {
            "name": "test-plugin",
            "agents": ["./agents/my-agent.md"],
            "commands": {"cmd": {"source": "./commands/cmd.md"}},
            "hooks": "./hooks/hooks.json",
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 0

    def test_missing_agent_file(self, plugin_structure):
        """Test error when agent file doesn't exist."""
        plugin_data = {
            "name": "test-plugin",
            "agents": ["./agents/missing-agent.md"],
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 1
        assert "Agent file not found" in errors[0]
        assert "missing-agent.md" in errors[0]

    def test_agent_not_ending_with_md(self, plugin_structure):
        """Test error when agent path doesn't end with .md."""
        plugin_data = {
            "name": "test-plugin",
            "agents": ["./agents/"],
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 1
        assert "must end with .md" in errors[0]

    def test_agents_as_string_error(self, plugin_structure):
        """Test error when agents is a string instead of array."""
        plugin_data = {
            "name": "test-plugin",
            "agents": "./agents/",
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 1
        assert "must be an array" in errors[0]

    def test_missing_command_file(self, plugin_structure):
        """Test error when command file doesn't exist."""
        plugin_data = {
            "name": "test-plugin",
            "commands": {"test": {"source": "./commands/missing.md"}},
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 1
        assert "Command file not found" in errors[0]

    def test_missing_hooks_file(self, plugin_structure):
        """Test error when hooks file doesn't exist."""
        plugin_data = {
            "name": "test-plugin",
            "hooks": "./hooks/missing.json",
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 1
        assert "Hooks file not found" in errors[0]

    def test_multiple_missing_files(self, plugin_structure):
        """Test that multiple missing files are all reported."""
        plugin_data = {
            "name": "test-plugin",
            "agents": ["./agents/a.md", "./agents/b.md"],
            "commands": {"cmd": {"source": "./commands/c.md"}},
            "hooks": "./hooks/missing.json",
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 4

    def test_empty_agents_array(self, plugin_structure):
        """Test that empty agents array is valid."""
        plugin_data = {
            "name": "test-plugin",
            "agents": [],
        }
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 0

    def test_no_optional_fields(self, plugin_structure):
        """Test plugin with only required name field."""
        plugin_data = {"name": "minimal-plugin"}
        plugin_structure["plugin_json"].write_text(json.dumps(plugin_data))

        errors = validate_plugin_references(plugin_structure["plugin_json"])
        assert len(errors) == 0

    def test_invalid_json_file(self, tmp_path):
        """Test handling of invalid JSON plugin file."""
        plugin_json = tmp_path / "plugin.json"
        plugin_json.write_text("{invalid")

        errors = validate_plugin_references(plugin_json)
        assert len(errors) == 1
        assert "Could not load" in errors[0]
