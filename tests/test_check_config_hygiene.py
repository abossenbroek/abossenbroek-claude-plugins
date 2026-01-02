"""Tests for check_config_hygiene.py."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_config_hygiene import (
    CheckResult,
    check_author_email,
    check_config_file,
    check_empty_arrays,
    check_hedging_note,
    check_schema_reference,
)


class TestCheckResult:
    """Tests for CheckResult class."""

    def test_empty_result_is_clean(self):
        """Test that empty result is clean."""
        result = CheckResult()
        assert result.is_clean
        assert "[OK]" in str(result)

    def test_error_makes_result_not_clean(self):
        """Test that errors make result not clean."""
        result = CheckResult()
        result.add_error("test.json", "Test error")
        assert not result.is_clean
        assert "[ERROR]" in str(result)

    def test_warning_keeps_result_clean(self):
        """Test that warnings keep result clean."""
        result = CheckResult()
        result.add_warning("test.json", "Test warning")
        assert result.is_clean
        assert "[WARN]" in str(result)

    def test_no_emojis_in_output(self):
        """Test that output contains no emoji characters."""
        result = CheckResult()
        result.add_error("test.json", "Error message")
        result.add_warning("test.json", "Warning message")
        output = str(result)
        # Check that old emojis are not present
        assert "✗" not in output
        assert "⚠" not in output
        assert "✓" not in output


class TestCheckHedgingNote:
    """Tests for check_hedging_note function."""

    def test_missing_hedging_note_warning(self, tmp_path):
        """Test that missing hedging note produces warning."""
        file_path = tmp_path / "test.json"
        data = {"name": "test"}
        result = CheckResult()
        check_hedging_note(file_path, data, result)
        assert len(result.warnings) == 1
        assert "_schema_note" in result.warnings[0]

    def test_present_hedging_note_no_warning(self, tmp_path):
        """Test that present hedging note produces no warning."""
        file_path = tmp_path / "test.json"
        data = {"name": "test", "_schema_note": "Inferred 2025-12-30"}
        result = CheckResult()
        check_hedging_note(file_path, data, result)
        assert len(result.warnings) == 0

    def test_hedging_note_without_date_warning(self, tmp_path):
        """Test that hedging note without date produces warning."""
        file_path = tmp_path / "test.json"
        data = {"name": "test", "_schema_note": "No date here"}
        result = CheckResult()
        check_hedging_note(file_path, data, result)
        assert len(result.warnings) == 1
        assert "date" in result.warnings[0]

    def test_alternate_hedging_fields(self, tmp_path):
        """Test that alternate hedging fields are accepted."""
        file_path = tmp_path / "test.json"
        for field in ["_note", "_inferred", "_empirical"]:
            data = {"name": "test", field: "Test 2025-12-30"}
            result = CheckResult()
            check_hedging_note(file_path, data, result)
            # Should only have date warning if applicable, not missing note
            assert not any("Missing hedging" in w for w in result.warnings)


class TestCheckSchemaReference:
    """Tests for check_schema_reference function."""

    def test_missing_schema_warning(self, tmp_path):
        """Test that missing $schema produces warning."""
        file_path = tmp_path / "test.json"
        data = {"name": "test"}
        result = CheckResult()
        check_schema_reference(file_path, data, result)
        assert len(result.warnings) == 1
        assert "$schema" in result.warnings[0]

    def test_present_schema_no_warning(self, tmp_path):
        """Test that present $schema produces no warning."""
        file_path = tmp_path / "test.json"
        data = {"$schema": "https://example.com/schema.json", "name": "test"}
        result = CheckResult()
        check_schema_reference(file_path, data, result)
        assert len(result.warnings) == 0


class TestCheckAuthorEmail:
    """Tests for check_author_email function."""

    def test_author_without_email_warning(self, tmp_path):
        """Test that author without email produces warning."""
        file_path = tmp_path / "test.json"
        data = {"author": {"name": "Test Author"}}
        result = CheckResult()
        check_author_email(file_path, data, result)
        assert len(result.warnings) == 1
        assert "email" in result.warnings[0]

    def test_author_with_email_no_warning(self, tmp_path):
        """Test that author with email produces no warning."""
        file_path = tmp_path / "test.json"
        data = {"author": {"name": "Test", "email": "test@example.com"}}
        result = CheckResult()
        check_author_email(file_path, data, result)
        assert len(result.warnings) == 0

    def test_owner_without_email_warning(self, tmp_path):
        """Test that owner without email produces warning."""
        file_path = tmp_path / "test.json"
        data = {"owner": {"name": "Test Owner"}}
        result = CheckResult()
        check_author_email(file_path, data, result)
        assert len(result.warnings) == 1
        assert "email" in result.warnings[0]

    def test_plugins_author_without_email(self, tmp_path):
        """Test that plugin author without email produces warning."""
        file_path = tmp_path / "test.json"
        data = {"plugins": [{"author": {"name": "Plugin Author"}}]}
        result = CheckResult()
        check_author_email(file_path, data, result)
        assert len(result.warnings) == 1
        assert "plugins[0].author" in result.warnings[0]


class TestCheckEmptyArrays:
    """Tests for check_empty_arrays function."""

    def test_empty_array_warning(self, tmp_path):
        """Test that empty array produces warning."""
        file_path = tmp_path / "test.json"
        data = {"items": []}
        result = CheckResult()
        check_empty_arrays(file_path, data, result)
        assert len(result.warnings) == 1
        assert "items" in result.warnings[0]

    def test_nested_empty_array_warning(self, tmp_path):
        """Test that nested empty array produces warning."""
        file_path = tmp_path / "test.json"
        data = {"level1": {"level2": {"items": []}}}
        result = CheckResult()
        check_empty_arrays(file_path, data, result)
        assert len(result.warnings) == 1
        assert "level1.level2.items" in result.warnings[0]

    def test_non_empty_array_no_warning(self, tmp_path):
        """Test that non-empty array produces no warning."""
        file_path = tmp_path / "test.json"
        data = {"items": ["item1", "item2"]}
        result = CheckResult()
        check_empty_arrays(file_path, data, result)
        assert len(result.warnings) == 0


class TestCheckConfigFile:
    """Tests for check_config_file function."""

    def test_invalid_json_error(self, tmp_path):
        """Test that invalid JSON produces error."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{invalid json")
        result = CheckResult()
        check_config_file(file_path, result)
        assert not result.is_clean
        assert any("Invalid JSON" in e for e in result.errors)

    def test_valid_config_all_checks(self, tmp_path):
        """Test that valid config passes all checks."""
        file_path = tmp_path / "test.json"
        data = {
            "$schema": "https://example.com/schema.json",
            "_schema_note": "Test note 2025-12-30",
            "name": "test",
            "author": {"name": "Test", "email": "test@example.com"},
            "items": ["item1"],
        }
        file_path.write_text(json.dumps(data))
        result = CheckResult()
        check_config_file(file_path, result)
        assert result.is_clean
        assert len(result.warnings) == 0
