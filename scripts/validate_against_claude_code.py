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


def find_claude_cli() -> str | None:
    """Find the claude CLI executable."""
    return shutil.which("claude")


def validate_path(path: Path) -> tuple[bool, list[str], list[str]]:
    """Validate a plugin or marketplace path using Claude Code CLI.

    Returns:
        Tuple of (passed, errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    result = subprocess.run(
        ["claude", "plugin", "validate", str(path)],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Parse output for errors and warnings
    if "Validation failed" in output or result.returncode != 0:
        # Extract error messages
        for line in output.split("\n"):
            line = line.strip()
            if line and not line.startswith(("Validating", "✔", "⚠", "Found")):
                if "❯" in line:
                    errors.append(line.replace("❯", "").strip())
        return False, errors, warnings

    # Check for warnings
    if "warning" in output.lower():
        for line in output.split("\n"):
            line = line.strip()
            if "❯" in line:
                warnings.append(line.replace("❯", "").strip())

    return True, errors, warnings


def main() -> int:
    """Validate all plugins and marketplace against Claude Code."""
    parser = argparse.ArgumentParser(
        description="Validate against Claude Code schemas"
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    # Check claude CLI is available
    if not find_claude_cli():
        print("[SKIP] Claude CLI not found - skipping Claude Code validation")
        print("       Install with: npm install -g @anthropic-ai/claude-code")
        return 0

    repo_root = Path(__file__).parent.parent
    all_passed = True
    total_warnings: list[str] = []

    # Find marketplace (repo root)
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    if marketplace_path.exists():
        print(f"Validating marketplace: {repo_root}")
        passed, errors, warnings = validate_path(repo_root)
        if not passed:
            print(f"  [ERROR] Marketplace validation failed:")
            for error in errors:
                print(f"    - {error}")
            all_passed = False
        elif warnings:
            for warning in warnings:
                print(f"  [WARN] {warning}")
            total_warnings.extend(warnings)
        else:
            print("  [OK] Marketplace valid")

    # Find all plugin directories
    plugin_dirs = [
        p.parent.parent
        for p in repo_root.glob("**/.claude-plugin/plugin.json")
        if ".git" not in str(p) and "node_modules" not in str(p)
    ]

    for plugin_dir in plugin_dirs:
        print(f"Validating plugin: {plugin_dir.name}")
        passed, errors, warnings = validate_path(plugin_dir)
        if not passed:
            print(f"  [ERROR] Plugin validation failed:")
            for error in errors:
                print(f"    - {error}")
            all_passed = False
        elif warnings:
            for warning in warnings:
                print(f"  [WARN] {warning}")
            total_warnings.extend(warnings)
        else:
            print("  [OK] Plugin valid")

    # Summary
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
