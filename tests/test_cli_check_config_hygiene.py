"""CLI integration tests for check_config_hygiene.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the check_config_hygiene.py script
SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "check_config_hygiene.py"


@pytest.fixture
def run_hygiene_cli():
    """Factory fixture: runs check_config_hygiene CLI and captures output."""

    def _run(
        args: list[str],
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(SCRIPT_PATH), *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_text,
            check=False,
        )

    return _run


@pytest.fixture
def json_fixture_path(tmp_path: Path):
    """Factory fixture: creates JSON file from Python dict."""

    def _create_json(data: dict, filename: str = "test.json") -> Path:
        path = tmp_path / filename
        path.write_text(json.dumps(data, indent=2))
        return path

    return _create_json


class TestCheckConfigHygieneCLI:
    """CLI integration tests for check_config_hygiene script."""

    def test_valid_config_passes(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test valid config passes hygiene checks."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "version": "1.0.0",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Should pass (no errors)
        assert result.returncode == 0

    def test_config_without_schema_note_passes(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test config without _schema_note passes (Claude Code rejects it)."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "version": "1.0.0",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Should pass - _schema_note is no longer required
        assert result.returncode == 0

    def test_missing_schema_reference_warning(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test missing $schema produces warning."""
        data = {
            "name": "test-plugin",
            "version": "1.0.0",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Missing $schema is a warning
        assert "warning" in result.stdout.lower() or "schema" in result.stdout.lower()

    def test_missing_author_email_warning(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test missing author email produces warning."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "author": {"name": "Test"},  # Has name but missing email
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Missing email is a warning, not an error
        assert result.returncode == 0  # Warnings don't fail
        assert "email" in result.stdout.lower()

    def test_empty_array_warning(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test empty array produces warning."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "plugins": [],
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Empty array is a warning
        assert "warning" in result.stdout.lower() or "empty" in result.stdout.lower()

    def test_invalid_json_error(
        self,
        tmp_path: Path,
        run_hygiene_cli,
    ):
        """Test invalid JSON produces error."""
        path = tmp_path / "invalid.json"
        path.write_text("{ invalid json content")
        result = run_hygiene_cli([str(path)])
        assert result.returncode == 1
        assert "json" in result.stdout.lower()

    def test_strict_mode_with_warnings(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test --strict flag treats warnings as errors."""
        data = {
            # Missing $schema triggers warning
            "name": "test-plugin",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli(["--strict", str(path)])
        # With --strict, warnings become errors
        assert result.returncode == 1

    def test_strict_short_flag(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test -s short flag for strict."""
        data = {
            # Missing $schema triggers warning
            "name": "test-plugin",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli(["-s", str(path)])
        assert result.returncode == 1

    def test_multiple_files(
        self,
        run_hygiene_cli,
        tmp_path: Path,
    ):
        """Test checking multiple files at once."""
        data1 = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "plugin1",
        }
        data2 = {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "marketplace",
        }
        path1 = tmp_path / "plugin1.json"
        path2 = tmp_path / "plugin2.json"
        path1.write_text(json.dumps(data1))
        path2.write_text(json.dumps(data2))
        result = run_hygiene_cli([str(path1), str(path2)])
        assert "2" in result.stdout  # Should say checking 2 files


class TestCheckConfigHygieneValidation:
    """Tests for specific validation scenarios."""

    def test_nested_empty_array(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test nested empty array produces warning."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "nested": {"items": []},
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Nested empty array should be caught
        assert "empty" in result.stdout.lower() or "warning" in result.stdout.lower()

    def test_plugins_author_missing_email(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test plugins author missing email produces warning."""
        data = {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "test-marketplace",
            "plugins": [
                {"name": "plugin1", "author": {"name": "Test"}}  # Missing email
            ],
        }
        path = json_fixture_path(data, "marketplace.json")
        result = run_hygiene_cli([str(path)])
        # Missing email in plugins author is a warning
        assert "email" in result.stdout.lower() or "warning" in result.stdout.lower()

    def test_valid_non_placeholder_email(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test valid non-placeholder email passes."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
            "author": {"name": "Test", "email": "real@company.com"},
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        # Real email should pass
        assert result.returncode == 0


class TestCheckConfigHygieneOutput:
    """Tests for CLI output formatting."""

    def test_output_shows_file_count(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test output shows number of files being checked."""
        data = {
            "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
            "name": "test-plugin",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        assert "1" in result.stdout and "file" in result.stdout.lower()

    def test_output_shows_errors_clearly(
        self,
        tmp_path: Path,
        run_hygiene_cli,
    ):
        """Test error output is clearly formatted."""
        # Invalid JSON produces an actual error
        path = tmp_path / "invalid.json"
        path.write_text("{ invalid json }")
        result = run_hygiene_cli([str(path)])
        assert result.returncode == 1
        assert "error" in result.stdout.lower()

    def test_output_shows_warnings_clearly(
        self,
        json_fixture_path,
        run_hygiene_cli,
    ):
        """Test warning output is clearly formatted."""
        data = {
            # Missing $schema triggers warning
            "name": "test-plugin",
        }
        path = json_fixture_path(data, "plugin.json")
        result = run_hygiene_cli([str(path)])
        assert "warning" in result.stdout.lower()
