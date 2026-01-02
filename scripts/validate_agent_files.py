#!/usr/bin/env python3
"""Validate that files referenced in plugin.json actually exist.

Checks:
- Agent files (.md) referenced in the agents array
- Command files (.md) referenced in commands
- Hook files (.json) referenced in hooks
"""

import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict | None:
    """Load JSON file, returning None on error."""
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def validate_plugin_references(plugin_json: Path) -> list[str]:  # noqa: PLR0912
    """Validate all file references in a plugin.json.

    Returns:
        List of error messages (empty if all files exist).
    """
    errors: list[str] = []
    data = load_json(plugin_json)

    if data is None:
        return [f"Could not load {plugin_json}"]

    plugin_dir = plugin_json.parent.parent  # Go up from .claude-plugin/

    # Validate agents
    agents = data.get("agents", [])
    if isinstance(agents, list):
        for agent_path in agents:
            if not isinstance(agent_path, str):
                errors.append(f"Invalid agent path type: {type(agent_path).__name__}")
                continue

            if not agent_path.endswith(".md"):
                errors.append(f"Agent path must end with .md: {agent_path}")
                continue

            full_path = plugin_dir / agent_path
            if not full_path.exists():
                errors.append(f"Agent file not found: {agent_path}")
    elif isinstance(agents, str):
        errors.append(f"agents must be an array, not a string: {agents}")

    # Validate commands
    commands = data.get("commands", {})
    if isinstance(commands, dict):
        for cmd_name, cmd_def in commands.items():
            if isinstance(cmd_def, dict) and "source" in cmd_def:
                source = cmd_def["source"]
                full_path = plugin_dir / source
                if not full_path.exists():
                    errors.append(
                        f"Command file not found: {source} (command: {cmd_name})"
                    )

    # Validate hooks
    hooks = data.get("hooks")
    if hooks and isinstance(hooks, str):
        full_path = plugin_dir / hooks
        if not full_path.exists():
            errors.append(f"Hooks file not found: {hooks}")

    return errors


def main() -> int:
    """Validate all plugin file references."""
    repo_root = Path(__file__).parent.parent

    plugin_files = list(repo_root.glob("*/.claude-plugin/plugin.json"))

    if not plugin_files:
        print("No plugin.json files found")
        return 0

    all_errors: list[tuple[Path, str]] = []

    for plugin_json in plugin_files:
        plugin_name = plugin_json.parent.parent.name
        print(f"Validating {plugin_name} file references...")

        errors = validate_plugin_references(plugin_json)

        if errors:
            all_errors.extend((plugin_json, e) for e in errors)
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("  OK")

    if all_errors:
        print(f"\nValidation failed with {len(all_errors)} error(s)")
        return 1

    print("\nAll file references valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
