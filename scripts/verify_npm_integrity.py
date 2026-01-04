#!/usr/bin/env python3
"""Verify npm package-lock.json contains integrity hashes."""

import json
import sys
from pathlib import Path


def verify_integrity(lock_file: Path) -> bool:
    """Check all packages have integrity field."""
    with lock_file.open() as f:
        lock = json.load(f)

    missing = []
    for name, data in lock.get("packages", {}).items():
        if name == "":  # Root package
            continue
        if "integrity" not in data:
            missing.append(name)

    if missing:
        print(f"ERROR: Missing integrity hashes: {missing}")
        return False

    print("OK: All packages have integrity hashes")
    return True


if __name__ == "__main__":
    lock = Path("red-agent/package-lock.json")
    if not lock.exists():
        print("WARNING: package-lock.json not found (jscpd not installed)")
        sys.exit(0)

    sys.exit(0 if verify_integrity(lock) else 1)
