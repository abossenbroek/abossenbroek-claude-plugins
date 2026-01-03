#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pydantic>=2.0", "pyyaml"]
# ///
"""File cache CLI for context engineering plugin.

This script provides commands for discovering files, caching references,
and lazy loading content to reduce context pollution in sub-agents.
"""

import argparse
import fcntl
import hashlib
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

# Import from src package - adjust path if needed
try:
    from src.context_engineering.models.state import (
        ContextEngineeringState,
        FileRef,
    )
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.context_engineering.models.state import (
        ContextEngineeringState,
        FileRef,
    )


STATE_FILENAME = ".context-engineering-state.yaml"


class FileCache:
    """Manager for file cache operations."""

    def __init__(self, plugin_path: Path) -> None:
        """Initialize file cache manager.

        Args:
            plugin_path: Path to plugin directory
        """
        self.plugin_path = plugin_path
        self.state_file = plugin_path / STATE_FILENAME

    def _acquire_lock(self, file_handle) -> None:
        """Acquire exclusive lock on state file.

        Args:
            file_handle: Open file handle

        Raises:
            BlockingIOError: If lock cannot be acquired
        """
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(self, file_handle) -> None:
        """Release lock on state file.

        Args:
            file_handle: Open file handle
        """
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)

    def _generate_file_id(self, path: str) -> str:
        """Generate unique file ID from path.

        Args:
            path: Absolute file path

        Returns:
            MD5 hash prefix (8 chars) of path
        """
        return hashlib.md5(path.encode()).hexdigest()[:8]

    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count from content.

        Args:
            content: File content

        Returns:
            Rough token count (chars/4 estimate)
        """
        return len(content) // 4

    def discover(self, pattern: str = "**/*.md") -> None:
        """Discover files matching pattern and add to cache.

        Args:
            pattern: Glob pattern for file discovery (default: **/*.md)
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            print("[ERROR] Run 'state_manager.py init' first")
            sys.exit(1)

        # Find matching files
        discovered = list(self.plugin_path.glob(pattern))
        if not discovered:
            print(f"[WARN] No files found matching pattern: {pattern}")
            return

        print(f"[OK] Found {len(discovered)} files matching {pattern}")

        # Read current state
        with self.state_file.open("r+") as f:
            self._acquire_lock(f)
            try:
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                # Add new files to cache
                added = 0
                for file_path in discovered:
                    abs_path = str(file_path.absolute())
                    file_id = self._generate_file_id(abs_path)

                    if file_id not in state.mutable.file_cache:
                        # Create unloaded file reference
                        file_ref = FileRef(
                            id=file_id,
                            path=abs_path,
                            loaded=False,
                            content=None,
                            token_estimate=0,
                        )
                        state.mutable.file_cache[file_id] = file_ref
                        added += 1
                        print(f"[OK] Added: {file_path.name} (id: {file_id})")

                if added > 0:
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

                print(f"[OK] Added {added} new files to cache")
                print(f"[OK] Total cached files: {len(state.mutable.file_cache)}")
            finally:
                self._release_lock(f)

    def fetch(self, file_id: str) -> None:
        """Load content for a specific file ID.

        Args:
            file_id: File ID to fetch content for
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        with self.state_file.open("r+") as f:
            self._acquire_lock(f)
            try:
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                if file_id not in state.mutable.file_cache:
                    print(f"[ERROR] File ID not found in cache: {file_id}")
                    sys.exit(1)

                file_ref = state.mutable.file_cache[file_id]

                if file_ref.loaded:
                    print(f"[WARN] File already loaded: {file_ref.path}")
                    print(f"[OK] Token estimate: {file_ref.token_estimate}")
                    return

                # Load content
                try:
                    file_path = Path(file_ref.path)
                    content = file_path.read_text()
                    token_estimate = self._estimate_tokens(content)

                    # Update file ref
                    file_ref.loaded = True
                    file_ref.content = content
                    file_ref.token_estimate = token_estimate
                    state.mutable.file_cache[file_id] = file_ref
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

                    print(f"[OK] Loaded: {file_path.name}")
                    print(f"[OK] Token estimate: {token_estimate}")
                except FileNotFoundError:
                    print(f"[ERROR] File not found: {file_ref.path}")
                    sys.exit(1)
                except Exception as e:
                    print(f"[ERROR] Failed to load file: {e}")
                    sys.exit(1)
            finally:
                self._release_lock(f)

    def refs(self, loaded_only: bool = False, unloaded_only: bool = False) -> None:
        """List file references from cache.

        Args:
            loaded_only: Show only loaded files
            unloaded_only: Show only unloaded files
        """
        if not self.state_file.exists():
            print(f"[ERROR] State file not found: {self.state_file}")
            sys.exit(1)

        with self.state_file.open("r") as f:
            self._acquire_lock(f)
            try:
                data = yaml.safe_load(f)
                state = ContextEngineeringState(**data)

                if not state.mutable.file_cache:
                    print("[WARN] No files in cache")
                    return

                # Filter based on flags
                refs = state.mutable.file_cache.values()
                if loaded_only:
                    refs = [r for r in refs if r.loaded]
                elif unloaded_only:
                    refs = [r for r in refs if not r.loaded]
                else:
                    refs = list(refs)

                if not refs:
                    if loaded_only:
                        print("[WARN] No loaded files in cache")
                    elif unloaded_only:
                        print("[WARN] No unloaded files in cache")
                    return

                print(f"[OK] Found {len(refs)} file references:")
                print()

                total_tokens = 0
                for ref in refs:
                    path = Path(ref.path)
                    status = "loaded" if ref.loaded else "unloaded"
                    token_info = (
                        f" ({ref.token_estimate} tokens)"
                        if ref.loaded
                        else " (not loaded)"
                    )
                    print(f"  {ref.id}: {path.name} [{status}]{token_info}")
                    print(f"    Path: {ref.path}")

                    if ref.loaded:
                        total_tokens += ref.token_estimate

                print()
                if loaded_only or not unloaded_only:
                    print(f"[OK] Total tokens (loaded): {total_tokens}")
            finally:
                self._release_lock(f)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="File cache manager for context engineering"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Discover files and add to cache"
    )
    discover_parser.add_argument(
        "plugin_path", type=Path, help="Plugin directory path"
    )
    discover_parser.add_argument(
        "--pattern",
        type=str,
        default="**/*.md",
        help="Glob pattern for file discovery (default: **/*.md)",
    )

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Load content for file ID")
    fetch_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    fetch_parser.add_argument("file_id", type=str, help="File ID to fetch")

    # Refs command
    refs_parser = subparsers.add_parser("refs", help="List file references")
    refs_parser.add_argument("plugin_path", type=Path, help="Plugin directory path")
    refs_parser.add_argument(
        "--loaded-only", action="store_true", help="Show only loaded files"
    )
    refs_parser.add_argument(
        "--unloaded-only", action="store_true", help="Show only unloaded files"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cache = FileCache(args.plugin_path)

    try:
        if args.command == "discover":
            cache.discover(pattern=args.pattern)
        elif args.command == "fetch":
            cache.fetch(file_id=args.file_id)
        elif args.command == "refs":
            if args.loaded_only and args.unloaded_only:
                print("[ERROR] Cannot use --loaded-only and --unloaded-only together")
                sys.exit(1)
            cache.refs(loaded_only=args.loaded_only, unloaded_only=args.unloaded_only)
    except ValidationError as e:
        print(f"[ERROR] Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
