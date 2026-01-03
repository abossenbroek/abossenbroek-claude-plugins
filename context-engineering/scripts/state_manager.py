#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pydantic>=2.0", "pyyaml"]
# ///
"""State manager CLI for context engineering plugin.

This script provides commands for initializing, reading, and updating
shared state across context engineering sub-agents.
"""

import argparse
import fcntl
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

# Import from src package - adjust path if needed
try:
    from src.context_engineering.models.state import (
        AnalysisMode,
        ContextEngineeringState,
        FocusArea,
        ImmutableState,
        MutableState,
    )
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.context_engineering.models.state import (
        AnalysisMode,
        ContextEngineeringState,
        FocusArea,
        ImmutableState,
        MutableState,
    )


STATE_FILENAME = ".context-engineering-state.yaml"


class StateManager:
    """Manager for file-based state with locking."""

    def __init__(self, plugin_path: Path) -> None:
        """Initialize state manager.

        Args:
            plugin_path: Path to plugin directory
        """
        self.plugin_path = plugin_path
        self.state_file = plugin_path / STATE_FILENAME

    def _acquire_lock(self, file_handle: Any) -> None:
        """Acquire exclusive lock on state file.

        Args:
            file_handle: Open file handle

        Raises:
            BlockingIOError: If lock cannot be acquired
        """
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(self, file_handle: Any) -> None:
        """Release lock on state file.

        Args:
            file_handle: Open file handle
        """
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)

    def init(
        self,
        focus_area: FocusArea,
        mode: AnalysisMode,
        user_request: str = "",
    ) -> None:
        """Initialize new state file.

        Args:
            focus_area: Analysis focus area
            mode: Analysis mode
            user_request: Original user request
        """
        if self.state_file.exists():
            print(f"[ERROR] State file already exists: {self.state_file}")
            sys.exit(1)

        session_id = str(uuid.uuid4())
        state = ContextEngineeringState(
            immutable=ImmutableState(
                plugin_path=str(self.plugin_path.absolute()),
                focus_area=focus_area,
                mode=mode,
                user_request=user_request,
                session_id=session_id,
            ),
            mutable=MutableState(),
        )

        # Write state file
        with self.state_file.open("w") as f:
            self._acquire_lock(f)
            try:
                yaml.dump(
                    state.model_dump(mode="json"),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )
            finally:
                self._release_lock(f)

        print(f"[OK] Initialized state file: {self.state_file}")
        print(f"[OK] Session ID: {session_id}")

    def read(self, field: str | None = None) -> None:
        """Read and display state.

        Args:
            field: Optional field to read (immutable, mutable, or all)
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        with self.state_file.open("r") as f:
            self._acquire_lock(f)
            try:
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                if field == "immutable":
                    print(
                        yaml.dump(
                            state.immutable.model_dump(mode="json"),
                            sort_keys=False,
                        )
                    )
                elif field == "mutable":
                    print(
                        yaml.dump(
                            state.mutable.model_dump(mode="json"),
                            sort_keys=False,
                        )
                    )
                else:
                    print(yaml.dump(state.model_dump(mode="json"), sort_keys=False))
            finally:
                self._release_lock(f)

    def update(self, field: str, value_json: str) -> None:
        """Update mutable state field.

        Args:
            field: Field name in mutable state
            value_json: JSON-encoded value
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        try:
            value = json.loads(value_json)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON: {e}")
            sys.exit(1)

        with self.state_file.open("r+") as f:
            self._acquire_lock(f)
            try:
                # Read current state
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                # Update field
                if not hasattr(state.mutable, field):
                    print(f"[ERROR] Unknown mutable field: {field}")
                    sys.exit(1)

                setattr(state.mutable, field, value)
                state.version += 1

                # Write back
                f.seek(0)
                f.truncate()
                yaml.dump(
                    state.model_dump(mode="json"),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )

                print(f"[OK] Updated {field}")
                print(f"[OK] New version: {state.version}")
            finally:
                self._release_lock(f)

    def lock(self, holder: str | None = None) -> None:
        """Acquire lock on state.

        Args:
            holder: Optional agent name holding the lock
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        with self.state_file.open("r+") as f:
            self._acquire_lock(f)
            try:
                # Read current state
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                if state.lock_holder:
                    print(f"[ERROR] Lock already held by: {state.lock_holder}")
                    sys.exit(1)

                # Acquire lock
                state.lock_holder = holder or "unknown"
                state.version += 1

                # Write back
                f.seek(0)
                f.truncate()
                yaml.dump(
                    state.model_dump(mode="json"),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )

                print(f"[OK] Lock acquired by: {state.lock_holder}")
            finally:
                self._release_lock(f)

    def unlock(self) -> None:
        """Release lock on state."""
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        with self.state_file.open("r+") as f:
            self._acquire_lock(f)
            try:
                # Read current state
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                if not state.lock_holder:
                    print("[WARN] No lock to release")
                    return

                # Release lock
                holder = state.lock_holder
                state.lock_holder = None
                state.version += 1

                # Write back
                f.seek(0)
                f.truncate()
                yaml.dump(
                    state.model_dump(mode="json"),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )

                print(f"[OK] Lock released from: {holder}")
            finally:
                self._release_lock(f)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="State manager for context engineering"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize state file")
    init_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    init_parser.add_argument(
        "--focus",
        type=str,
        choices=["all", "context", "orchestration", "handoff"],
        default="all",
        help="Analysis focus area",
    )
    init_parser.add_argument(
        "--mode",
        type=str,
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Analysis mode",
    )
    init_parser.add_argument(
        "--request", type=str, default="", help="User request description"
    )

    # Read command
    read_parser = subparsers.add_parser("read", help="Read state")
    read_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    read_parser.add_argument(
        "--field",
        type=str,
        choices=["immutable", "mutable", "all"],
        help="Field to read",
    )

    # Update command
    update_parser = subparsers.add_parser("update", help="Update mutable state field")
    update_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    update_parser.add_argument("field", type=str, help="Field name")
    update_parser.add_argument("value", type=str, help="JSON value")

    # Lock command
    lock_parser = subparsers.add_parser("lock", help="Acquire lock")
    lock_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    lock_parser.add_argument("--holder", type=str, help="Agent name holding lock")

    # Unlock command
    unlock_parser = subparsers.add_parser("unlock", help="Release lock")
    unlock_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = StateManager(args.plugin_path)

    try:
        if args.command == "init":
            manager.init(
                focus_area=FocusArea(args.focus),
                mode=AnalysisMode(args.mode),
                user_request=args.request,
            )
        elif args.command == "read":
            manager.read(field=args.field)
        elif args.command == "update":
            manager.update(field=args.field, value_json=args.value)
        elif args.command == "lock":
            manager.lock(holder=args.holder)
        elif args.command == "unlock":
            manager.unlock()
    except ValidationError as e:
        print(f"[ERROR] Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
