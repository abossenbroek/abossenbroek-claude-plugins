"""Test jscpd availability and basic functionality."""

from pathlib import Path


def test_jscpd_binary_exists():
    """Test that jscpd binary exists after npm install."""
    jscpd_bin = Path("red-agent/node_modules/.bin/jscpd")
    assert (
        jscpd_bin.exists()
    ), "jscpd binary not found - run 'cd red-agent && npm install'"


def test_package_json_exists():
    """Test that package.json exists."""
    package_json = Path("red-agent/package.json")
    assert package_json.exists(), "red-agent/package.json not found"


def test_package_lock_json_exists():
    """Test that package-lock.json exists for security."""
    package_lock = Path("red-agent/package-lock.json")
    assert (
        package_lock.exists()
    ), "red-agent/package-lock.json not found - required for security"


def test_jscpd_config_exists():
    """Test that .jscpd.json config exists."""
    jscpd_config = Path("red-agent/.jscpd.json")
    assert jscpd_config.exists(), "red-agent/.jscpd.json not found"
