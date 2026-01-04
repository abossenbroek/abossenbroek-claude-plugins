#!/usr/bin/env python3
"""Verify npm package-lock.json contains integrity hashes."""

import json
import sys
from pathlib import Path


def verify_integrity(lock_file: Path) -> bool:
    """Check all packages have integrity field."""
    try:
        with lock_file.open() as f:
            lock = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in package-lock.json: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read package-lock.json: {e}")
        return False

    missing = []
    for name, data in lock.get("packages", {}).items():
        if name == "":  # Root package
            continue
        if "integrity" not in data:
            missing.append(name)

    if missing:
        print(f"ERROR: Missing integrity hashes in {len(missing)} package(s)")
        print(f"First few: {missing[:5]}")
        return False

    total_packages = len(lock.get("packages", {})) - 1  # Exclude root
    print(f"OK: All {total_packages} packages have integrity hashes")
    return True


if __name__ == "__main__":
    lock = Path("red-agent/package-lock.json")
    if not lock.exists():
        print("INFO: package-lock.json not found (jscpd not installed)")
        sys.exit(0)

    sys.exit(0 if verify_integrity(lock) else 1)
