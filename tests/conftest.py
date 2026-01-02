"""Pytest fixtures for validation tests."""

import pytest


@pytest.fixture
def valid_attacker_output():
    """Valid attacker output data with all required fields."""
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
                    "category": "reasoning-flaws",
                    "target": {
                        "claim_id": "C-001",
                        "claim_text": "Test claim being attacked",
                        "message_num": 1,
                    },
                    "evidence": {
                        "type": "logical_gap",
                        "description": "Missing logical step in the reasoning chain",
                        "quote": "The system will always work correctly",
                    },
                    "attack_applied": {
                        "style": "socratic-questioning",
                        "probe": "What happens when the external API is unavailable?",
                    },
                    "impact": {
                        "if_exploited": (
                            "System may fail silently without user notification"
                        ),
                        "affected_claims": ["C-002", "C-003"],
                    },
                    "recommendation": "Add explicit error handling for API failures",
                }
            ],
            "patterns_detected": [
                {
                    "pattern": "Missing error handling",
                    "instances": 3,
                    "description": "Multiple claims assume happy path",
                }
            ],
            "summary": {
                "total_findings": 1,
                "by_severity": {
                    "critical": 0,
                    "high": 1,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                },
                "highest_risk_claim": "C-001",
                "primary_weakness": "Insufficient error handling assumptions",
            },
        }
    }


@pytest.fixture
def minimal_attacker_finding():
    """Minimal valid attacker finding with all required fields."""
    return {
        "id": "RF-001",
        "severity": "MEDIUM",
        "title": "Test finding title",
        "confidence": 0.75,
        "category": "reasoning-flaws",
        "target": {"claim_id": "C-001"},
        "evidence": {"type": "logical_gap"},
        "attack_applied": {"style": "questioning", "probe": "Test probe question"},
        "impact": {"if_exploited": "Potential issue if exploited"},
        "recommendation": "Recommend fixing this issue promptly",
    }


@pytest.fixture
def invalid_attacker_output_missing_root():
    """Attacker output missing attack_results root."""
    return {"wrong_key": {}}


@pytest.fixture
def invalid_attacker_output_bad_finding():
    """Attacker output with invalid finding (missing required fields)."""
    return {
        "attack_results": {
            "attack_type": "test",
            "findings": [
                {
                    "id": "INVALID",  # Wrong format
                    "severity": "WRONG",  # Invalid enum
                    "title": "Short",  # Too short
                    "confidence": 2.0,  # Out of range
                    # Missing required fields
                }
            ],
            "summary": {"total_findings": 1},
        }
    }


@pytest.fixture
def valid_grounding_output():
    """Valid grounding output data with all required fields."""
    return {
        "grounding_results": {
            "agent": "evidence-checker",
            "assessments": [
                {
                    "finding_id": "RF-001",
                    "evidence_strength": 0.85,
                    "original_confidence": 0.90,
                    "evidence_review": {
                        "evidence_exists": True,
                        "evidence_accurate": True,
                        "evidence_sufficient": True,
                    },
                    "quote_verification": {
                        "original_quote": "The system will always work",
                        "actual_source": (
                            "Message 3: The system will always work correctly"
                        ),
                        "match_quality": "close",
                    },
                    "inference_validity": {
                        "valid": True,
                        "reasoning": (
                            "The inference follows logically from the evidence"
                        ),
                    },
                    "issues_found": [],
                    "adjusted_confidence": 0.80,
                    "notes": (
                        "Strong evidence from context, minor paraphrase difference"
                    ),
                }
            ],
        }
    }


@pytest.fixture
def minimal_grounding_assessment():
    """Minimal valid grounding assessment with all required fields."""
    return {
        "finding_id": "RF-001",
        "evidence_strength": 0.75,
        "original_confidence": 0.80,
        "evidence_review": {"evidence_exists": True},
        "quote_verification": {"match_quality": "exact"},
        "inference_validity": {"valid": True},
    }


@pytest.fixture
def invalid_grounding_output_missing_agent():
    """Grounding output missing agent field."""
    return {
        "grounding_results": {
            "assessments": [
                {
                    "finding_id": "RF-001",
                    "evidence_strength": 0.5,
                    # Missing required grounding fields
                }
            ]
        }
    }


@pytest.fixture
def valid_context_output():
    """Valid context analysis output."""
    return {
        "context_analysis": {
            "claim_analysis": [
                {
                    "claim_id": "C-001",
                    "risk_level": "HIGH",
                    "content": "Test claim",
                    "original_text": "Original claim text from conversation",
                    "verifiability": "verifiable",
                    "risk_factors": ["external_dependency", "assumption"],
                    "depends_on": ["C-002"],
                }
            ],
            "risk_surface": {"areas": ["auth", "data"], "exposure_level": "medium"},
            "dependency_graph": {"roots": ["C-001"], "chains": []},
            "key_observations": ["System assumes happy path"],
        }
    }


@pytest.fixture
def valid_report_output():
    """Valid final report output."""
    return {
        "executive_summary": (
            "This is a comprehensive executive summary that meets "
            "the minimum length requirement for validation."
        ),
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
def valid_strategy_output():
    """Valid attack strategy output data."""
    return {
        "attack_strategy": {
            "mode": "standard",
            "total_vectors": 5,
            "selected_vectors": [
                {
                    "category": "reasoning-flaws",
                    "priority": 1,
                    "rationale": (
                        "High density of logical claims requiring verification"
                    ),
                    "attack_styles": [
                        "socratic-questioning",
                        "contradiction-surfacing",
                    ],
                    "targets": [
                        {
                            "claim_id": "C-001",
                            "reason": "Central claim with multiple dependencies",
                        }
                    ],
                },
                {
                    "category": "assumption-gaps",
                    "priority": 2,
                    "rationale": "Several implicit assumptions detected",
                    "attack_styles": ["assumption-inversion"],
                },
            ],
            "attacker_assignments": {
                "reasoning-attacker": {
                    "categories": ["reasoning-flaws", "assumption-gaps"],
                    "targets": [{"claim_id": "C-001", "reason": "Primary target"}],
                },
                "context-attacker": {
                    "categories": ["context-manipulation", "authority-exploitation"],
                },
            },
            "grounding_plan": {
                "enabled": True,
                "agents": ["evidence-checker", "proportion-checker"],
            },
            "meta_analysis": {"enabled": False},
            "notes": ["Focus on reasoning chain integrity"],
        }
    }


@pytest.fixture
def minimal_strategy_output():
    """Minimal valid strategy output."""
    return {
        "attack_strategy": {
            "mode": "quick",
            "total_vectors": 2,
            "selected_vectors": [
                {
                    "category": "reasoning-flaws",
                    "priority": 1,
                    "rationale": "Test rationale",
                }
            ],
        }
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
