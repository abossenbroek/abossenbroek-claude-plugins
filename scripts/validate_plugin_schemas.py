#!/usr/bin/env python3
"""Validate plugin.json and marketplace.json against inferred schemas.

Note: These schemas are inferred from official Anthropic examples and
error-driven discovery. They may be incomplete or change as Claude Code evolves.
"""

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def load_json(path: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        sys.exit(1)


def validate_file(file_path: Path, schema_path: Path) -> list[str]:
    """Validate a JSON file against a schema. Returns list of errors."""
    data = load_json(file_path)
    schema = load_json(schema_path)

    validator = Draft7Validator(schema)
    return [f"{e.json_path}: {e.message}" for e in validator.iter_errors(data)]


def main() -> int:
    """Validate all plugin configuration files."""
    repo_root = Path(__file__).parent.parent
    schemas_dir = repo_root / "schemas"

    validations: list[tuple[Path, Path]] = [
        (
            repo_root / ".claude-plugin" / "marketplace.json",
            schemas_dir / "marketplace.schema.json",
        ),
    ]

    validations.extend(
        (plugin_json, schemas_dir / "plugin.schema.json")
        for plugin_json in repo_root.glob("*/.claude-plugin/plugin.json")
    )

    all_errors: list[tuple[Path, str]] = []

    for file_path, schema_path in validations:
        if not file_path.exists():
            continue
        if not schema_path.exists():
            print(f"Warning: Schema not found: {schema_path}")
            continue

        print(f"Validating {file_path.relative_to(repo_root)}...")
        errors = validate_file(file_path, schema_path)

        if errors:
            all_errors.extend((file_path, e) for e in errors)
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("  OK")

    if all_errors:
        print(f"\nValidation failed with {len(all_errors)} error(s)")
        return 1

    print("\nAll validations passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
