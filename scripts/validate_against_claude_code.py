#!/usr/bin/env python3
"""Validate plugins and marketplace against Claude Code's internal schemas.

Uses `claude plugin validate` to ensure configs match Claude Code's expectations.
This catches schema issues BEFORE runtime, using the same validation Claude Code uses.

Usage:
    python validate_against_claude_code.py [--strict]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Claude Code output markers (Unicode escape sequences)
MARKER_ARROW = "\u276f"
MARKER_CHECK = "\u2714"
MARKER_WARN = "\u26a0"


def find_claude_cli() -> str | None:
    """Find the claude CLI executable."""
    return shutil.which("claude")


def parse_output_lines(output: str) -> list[str]:
    """Extract message lines from Claude Code output."""
    messages = []
    skip_prefixes = ("Validating", MARKER_CHECK, MARKER_WARN, "Found")
    for raw_line in output.split("\n"):
        stripped = raw_line.strip()
        if (
            stripped
            and not stripped.startswith(skip_prefixes)
            and MARKER_ARROW in stripped
        ):
            messages.append(stripped.replace(MARKER_ARROW, "").strip())
    return messages


def validate_path(path: Path) -> tuple[bool, list[str], list[str]]:
    """Validate a plugin or marketplace path using Claude Code CLI.

    Returns:
        Tuple of (passed, errors, warnings)
    """
    result = subprocess.run(
        ["claude", "plugin", "validate", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout + result.stderr

    # Check for failure
    if "Validation failed" in output or result.returncode != 0:
        errors = parse_output_lines(output)
        return False, errors, []

    # Check for warnings
    warnings = parse_output_lines(output) if "warning" in output.lower() else []
    return True, [], warnings


def validate_marketplace(repo_root: Path) -> tuple[bool, list[str]]:
    """Validate marketplace if it exists. Returns (passed, warnings)."""
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        return True, []

    print(f"Validating marketplace: {repo_root}")
    passed, errors, warnings = validate_path(repo_root)

    if not passed:
        print("  [ERROR] Marketplace validation failed:")
        for error in errors:
            print(f"    - {error}")
        return False, []

    if warnings:
        for warning in warnings:
            print(f"  [WARN] {warning}")
    else:
        print("  [OK] Marketplace valid")

    return True, warnings


def validate_plugins(repo_root: Path) -> tuple[bool, list[str]]:
    """Validate all plugins. Returns (all_passed, warnings)."""
    plugin_dirs = [
        p.parent.parent
        for p in repo_root.glob("**/.claude-plugin/plugin.json")
        if ".git" not in str(p) and "node_modules" not in str(p)
    ]

    all_passed = True
    all_warnings: list[str] = []

    for plugin_dir in plugin_dirs:
        print(f"Validating plugin: {plugin_dir.name}")
        passed, errors, warnings = validate_path(plugin_dir)

        if not passed:
            print("  [ERROR] Plugin validation failed:")
            for error in errors:
                print(f"    - {error}")
            all_passed = False
        elif warnings:
            for warning in warnings:
                print(f"  [WARN] {warning}")
            all_warnings.extend(warnings)
        else:
            print("  [OK] Plugin valid")

    return all_passed, all_warnings


def main() -> int:
    """Validate all plugins and marketplace against Claude Code."""
    parser = argparse.ArgumentParser(description="Validate against Claude Code schemas")
    parser.add_argument(
        "--strict", "-s", action="store_true", help="Treat warnings as errors"
    )
    args = parser.parse_args()

    if not find_claude_cli():
        print("[SKIP] Claude CLI not found - skipping Claude Code validation")
        print("       Install with: npm install -g @anthropic-ai/claude-code")
        return 0

    repo_root = Path(__file__).parent.parent

    marketplace_passed, marketplace_warnings = validate_marketplace(repo_root)
    plugins_passed, plugin_warnings = validate_plugins(repo_root)

    all_passed = marketplace_passed and plugins_passed
    total_warnings = marketplace_warnings + plugin_warnings

    print()
    if not all_passed:
        print("[FAILED] Claude Code validation failed")
        return 1

    if total_warnings:
        print(f"[OK] Validation passed with {len(total_warnings)} warning(s)")
        if args.strict:
            print("[FAILED] --strict mode: warnings treated as errors")
            return 1
    else:
        print("[OK] All validations passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
