"""Tests for validate_plugin_schemas.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_plugin_schemas import LoadError, load_json, validate_file


class TestLoadJson:
    """Tests for load_json function."""

    def test_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"name": "test"}')
        data = load_json(file_path)
        assert data == {"name": "test"}

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises LoadError."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{invalid json")
        with pytest.raises(LoadError) as exc_info:
            load_json(file_path)
        assert "Invalid JSON" in str(exc_info.value)

    def test_empty_json(self, tmp_path):
        """Test loading empty JSON object."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")
        data = load_json(file_path)
        assert data == {}


class TestValidateFile:
    """Tests for validate_file function."""

    def test_valid_file_against_schema(self, tmp_path):
        """Test validating a file that matches schema."""
        # Create a simple schema
        schema_path = tmp_path / "schema.json"
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        schema_path.write_text(json.dumps(schema))

        # Create a valid file
        file_path = tmp_path / "test.json"
        file_path.write_text('{"name": "test"}')

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 0

    def test_invalid_file_against_schema(self, tmp_path):
        """Test validating a file that doesn't match schema."""
        # Create a simple schema
        schema_path = tmp_path / "schema.json"
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        schema_path.write_text(json.dumps(schema))

        # Create an invalid file (missing required field)
        file_path = tmp_path / "test.json"
        file_path.write_text('{"other": "value"}')

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_multiple_validation_errors(self, tmp_path):
        """Test that multiple errors are all reported."""
        # Create a schema requiring multiple fields
        schema_path = tmp_path / "schema.json"
        schema = {
            "type": "object",
            "required": ["name", "version", "description"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
            },
        }
        schema_path.write_text(json.dumps(schema))

        # Create a file missing all required fields
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 3

    def test_invalid_json_in_file(self, tmp_path):
        """Test that invalid JSON in file returns error."""
        schema_path = tmp_path / "schema.json"
        schema_path.write_text('{"type": "object"}')

        file_path = tmp_path / "test.json"
        file_path.write_text("{invalid}")

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]

    def test_invalid_json_in_schema(self, tmp_path):
        """Test that invalid JSON in schema returns error."""
        schema_path = tmp_path / "schema.json"
        schema_path.write_text("{invalid schema}")

        file_path = tmp_path / "test.json"
        file_path.write_text('{"name": "test"}')

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 1
        assert "Schema error" in errors[0]

    def test_type_mismatch_error(self, tmp_path):
        """Test that type mismatch is caught."""
        schema_path = tmp_path / "schema.json"
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        schema_path.write_text(json.dumps(schema))

        file_path = tmp_path / "test.json"
        file_path.write_text('{"count": "not an integer"}')

        errors = validate_file(file_path, schema_path)
        assert len(errors) == 1
        assert "count" in errors[0]
