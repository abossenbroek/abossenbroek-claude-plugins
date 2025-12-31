#!/usr/bin/env python3
"""Development checks for config file hygiene.

Catches common red team issues:
- Missing hedging/uncertainty notes in config files
- Empirically-determined values without documentation
- Fields removed without explicit justification

Usage:
    python check_config_hygiene.py [--strict]
"""

import json
import re
import sys
from pathlib import Path


class CheckResult:
    """Result of hygiene checks."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, file: str, msg: str) -> None:
        self.errors.append(f"{file}: {msg}")

    def add_warning(self, file: str, msg: str) -> None:
        self.warnings.append(f"{file}: {msg}")

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines: list[str] = []
        if self.errors:
            lines.append(f"ERRORS ({len(self.errors)}):")
            lines.extend(f"  ✗ {e}" for e in self.errors)
        if self.warnings:
            lines.append(f"WARNINGS ({len(self.warnings)}):")
            lines.extend(f"  ⚠ {w}" for w in self.warnings)
        if not lines:
            lines.append("✓ All checks passed")
        return "\n".join(lines)


def check_hedging_note(
    file_path: Path,
    data: dict,
    result: CheckResult,
) -> None:
    """Check that config files have hedging notes."""
    rel_path = str(file_path)

    hedging_fields = ["_schema_note", "_note", "_inferred", "_empirical"]
    has_hedging = any(field in data for field in hedging_fields)

    if not has_hedging:
        result.add_warning(
            rel_path,
            "Missing hedging note (_schema_note). "
            "Config decisions should document their source.",
        )
    else:
        note = data.get("_schema_note", data.get("_note", ""))
        if isinstance(note, str) and not re.search(r"\d{4}-\d{2}-\d{2}", note):
            result.add_warning(
                rel_path,
                "Hedging note should include date (e.g., '2025-12-30')",
            )


def check_schema_reference(
    file_path: Path,
    data: dict,
    result: CheckResult,
) -> None:
    """Check that JSON files reference their schema."""
    rel_path = str(file_path)

    if "$schema" not in data:
        result.add_warning(
            rel_path,
            "Missing $schema reference. Consider adding schema URL.",
        )


def check_author_email(
    file_path: Path,
    data: dict,
    result: CheckResult,
) -> None:
    """Check that author fields have email (per official examples)."""
    rel_path = str(file_path)

    def check_person(person: dict, field_name: str) -> None:
        if isinstance(person, dict) and "name" in person and "email" not in person:
            result.add_warning(
                rel_path,
                f"{field_name} has 'name' but missing 'email'",
            )

    if "author" in data:
        check_person(data["author"], "author")
    if "owner" in data:
        check_person(data["owner"], "owner")

    if "plugins" in data and isinstance(data["plugins"], list):
        for idx, plugin in enumerate(data["plugins"]):
            if isinstance(plugin, dict) and "author" in plugin:
                check_person(plugin["author"], f"plugins[{idx}].author")


def check_empty_arrays(
    file_path: Path,
    data: dict,
    result: CheckResult,
) -> None:
    """Warn about empty arrays that might indicate removed content."""
    rel_path = str(file_path)

    def check_recursive(obj: dict, path: str = "") -> None:
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, list) and len(value) == 0:
                result.add_warning(
                    rel_path,
                    f"Empty array at '{current_path}' - document if removed",
                )
            elif isinstance(value, dict):
                check_recursive(value, current_path)

    check_recursive(data)


def check_config_file(file_path: Path, result: CheckResult) -> None:
    """Run all checks on a config file."""
    try:
        data = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        result.add_error(str(file_path), f"Invalid JSON: {e}")
        return
    except OSError as e:
        result.add_error(str(file_path), f"Could not read file: {e}")
        return

    check_hedging_note(file_path, data, result)
    check_schema_reference(file_path, data, result)
    check_author_email(file_path, data, result)
    check_empty_arrays(file_path, data, result)


def main() -> int:
    """Run hygiene checks on all config files."""
    import argparse

    parser = argparse.ArgumentParser(description="Check config file hygiene")
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to check (default: find all)",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    result = CheckResult()

    if args.files:
        config_files = [Path(f) for f in args.files]
    else:
        config_files = list(repo_root.glob("**/.claude-plugin/*.json"))
        config_files.extend(repo_root.glob("**/plugin.json"))
        config_files.extend(repo_root.glob("**/marketplace.json"))

    config_files = [
        f for f in config_files if "node_modules" not in str(f) and ".git" not in str(f)
    ]

    if not config_files:
        print("No config files found to check")
        return 0

    print(f"Checking {len(config_files)} config file(s)...\n")

    for file_path in config_files:
        check_config_file(file_path, result)

    print(result)

    if not result.is_clean:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
