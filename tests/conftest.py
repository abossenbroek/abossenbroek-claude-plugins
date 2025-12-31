"""Pytest fixtures for validation tests."""

import pytest


@pytest.fixture
def valid_attacker_output():
    """Valid attacker output data."""
    return {
        "attack_results": {
            "attack_type": "reasoning-attacker",
            "categories_probed": ["reasoning-flaws", "assumption-gaps"],
            "findings": [
                {
                    "id": "RF-001",
                    "severity": "HIGH",
                    "title": "Test finding with sufficient length",
                    "confidence": 0.85,
                    "evidence": {"quote": "test", "source": "test.md"},
                    "recommendation": "Fix this issue",
                }
            ],
        }
    }


@pytest.fixture
def invalid_attacker_output_missing_root():
    """Attacker output missing attack_results root."""
    return {"wrong_key": {}}


@pytest.fixture
def invalid_attacker_output_bad_finding():
    """Attacker output with invalid finding."""
    return {
        "attack_results": {
            "attack_type": "test",
            "findings": [
                {
                    "id": "INVALID",  # Wrong format
                    "severity": "WRONG",  # Invalid enum
                    "title": "Short",  # Too short
                    "confidence": 2.0,  # Out of range
                }
            ],
        }
    }


@pytest.fixture
def valid_grounding_output():
    """Valid grounding output data."""
    return {
        "grounding_results": {
            "agent": "evidence-checker",
            "assessments": [
                {
                    "finding_id": "RF-001",
                    "evidence_strength": 0.85,
                    "adjusted_confidence": 0.80,
                    "notes": "Strong evidence from context",
                }
            ],
        }
    }


@pytest.fixture
def invalid_grounding_output_missing_agent():
    """Grounding output missing agent field."""
    return {
        "grounding_results": {
            "assessments": [{"finding_id": "RF-001", "evidence_strength": 0.5}]
        }
    }


@pytest.fixture
def valid_context_output():
    """Valid context analysis output."""
    return {
        "context_analysis": {
            "claim_analysis": [
                {"claim_id": "C-001", "risk_level": "HIGH", "content": "Test claim"}
            ],
            "risk_surface": {"areas": ["auth", "data"], "exposure_level": "medium"},
        }
    }


@pytest.fixture
def valid_report_output():
    """Valid final report output."""
    return {
        "executive_summary": "This is a comprehensive executive summary that meets the minimum length requirement for validation.",
        "risk_overview": {
            "overall_risk_level": "HIGH",
            "categories": [
                {"category": "reasoning-flaws", "severity": "HIGH", "count": 2}
            ],
        },
        "findings": {
            "critical": [],
            "high": [
                {
                    "id": "RF-001",
                    "category": "reasoning-flaws",
                    "severity": "HIGH",
                    "title": "Test finding with proper length",
                    "confidence": "85%",
                }
            ],
            "medium": [],
            "low": [],
        },
        "limitations": {
            "scope": "Limited to current context",
            "coverage": "Not exhaustive",
        },
    }


@pytest.fixture
def invalid_report_output_short_summary():
    """Report with too short executive summary."""
    return {
        "executive_summary": "Too short",
        "risk_overview": {"overall_risk_level": "LOW", "categories": []},
        "findings": {"critical": [], "high": [], "medium": [], "low": []},
    }


@pytest.fixture
def valid_plugin_json():
    """Valid plugin.json content."""
    return {
        "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
        "_schema_note": "Test note 2025-12-30",
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin description",
        "commands": {"test": {"source": "./commands/test.md"}},
    }


@pytest.fixture
def valid_marketplace_json():
    """Valid marketplace.json content."""
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "_schema_note": "Test note 2025-12-30",
        "name": "test-marketplace",
        "description": "Test marketplace",
        "owner": {"name": "Test Owner", "email": "test@example.com"},
        "plugins": [
            {
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "author": {"name": "Test", "email": "test@example.com"},
                "source": "./test-plugin",
                "category": "testing",
            }
        ],
    }
