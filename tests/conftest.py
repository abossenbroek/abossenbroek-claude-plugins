"""Pytest fixtures for validation tests."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml


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


# =============================================================================
# CLI Test Helper Fixtures
# =============================================================================


@pytest.fixture
def yaml_fixture_path(tmp_path: Path) -> Callable[[dict[str, Any], str], Path]:
    """Factory fixture: converts Python dict to YAML file.

    Usage:
        def test_example(yaml_fixture_path, valid_attacker_output):
            path = yaml_fixture_path(valid_attacker_output, "test.yaml")
            # path is now a Path to a YAML file containing the data
    """

    def _create_yaml(data: dict[str, Any], filename: str = "test.yaml") -> Path:
        path = tmp_path / filename
        path.write_text(yaml.dump(data, default_flow_style=False))
        return path

    return _create_yaml


@pytest.fixture
def run_cli() -> Callable[..., subprocess.CompletedProcess[str]]:
    """Factory fixture: runs CLI command and captures output.

    Usage:
        def test_example(run_cli):
            result = run_cli(
                "red_agent.scripts.validate_agent_output",
                ["--type", "attacker", "--input", str(path)]
            )
            assert result.returncode == 0
    """

    def _run(
        module_path: str,
        args: list[str],
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", module_path, *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_text,
            check=False,
        )

    return _run


# =============================================================================
# PR Analysis Fixtures
# =============================================================================


@pytest.fixture
def valid_diff_metadata():
    """Valid diff metadata with all required fields."""
    return {
        "git_operation": "staged",
        "files_changed": [
            {
                "path": "src/auth/handler.ts",
                "additions": 25,
                "deletions": 10,
                "change_type": "modified",
                "risk_score": 0.85,
            },
            {
                "path": "src/utils/helpers.ts",
                "additions": 15,
                "deletions": 5,
                "change_type": "modified",
                "risk_score": 0.3,
            },
            {
                "path": "tests/auth.test.ts",
                "additions": 50,
                "deletions": 0,
                "change_type": "added",
                "risk_score": 0.1,
            },
        ],
        "total_files_changed": 3,
        "total_additions": 90,
        "total_deletions": 15,
        "pr_size": "small",
    }


@pytest.fixture
def valid_diff_analysis_output():
    """Valid diff analysis output with all required fields."""
    return {
        "diff_analysis": {
            "summary": {
                "files_changed": 3,
                "high_risk_files": 1,
                "medium_risk_files": 1,
                "low_risk_files": 1,
                "total_insertions": 90,
                "total_deletions": 15,
            },
            "file_analysis": [
                {
                    "file_id": "auth_handler_001",
                    "path": "src/auth/handler.ts",
                    "risk_level": "high",
                    "risk_score": 0.85,
                    "change_summary": (
                        "Authentication handler with new validation logic"
                    ),
                    "risk_factors": ["authentication", "validation", "security"],
                    "line_ranges": [[45, 67], [80, 95]],
                    "change_type": "modification",
                    "insertions": 25,
                    "deletions": 10,
                }
            ],
            "risk_surface": [
                {
                    "category": "reasoning-flaws",
                    "exposure": "high",
                    "affected_files": ["auth_handler_001"],
                    "notes": "Authentication logic changes require careful review",
                }
            ],
            "patterns_detected": [
                {
                    "pattern": "error-handling-changes",
                    "description": "Multiple error handling modifications detected",
                    "instances": 2,
                    "affected_files": ["auth_handler_001"],
                    "risk_implication": (
                        "Error handling changes may introduce regressions"
                    ),
                }
            ],
            "high_risk_files": ["auth_handler_001"],
            "focus_areas": [
                {
                    "area": "authentication",
                    "files": ["auth_handler_001"],
                    "rationale": "Critical security component with validation changes",
                }
            ],
            "key_observations": [
                "Authentication handler has significant changes",
                "New validation logic added to auth flow",
            ],
        }
    }


@pytest.fixture
def valid_code_attacker_output():
    """Valid code attacker output with all required fields."""
    return {
        "attack_results": {
            "attack_type": "code-reasoning-attacker",
            "categories_probed": [
                "logic-errors",
                "assumption-gaps",
                "edge-case-handling",
            ],
            "findings": [
                {
                    "id": "LE-001",
                    "category": "logic-errors",
                    "severity": "HIGH",
                    "title": "Missing null check in authentication flow",
                    "target": {
                        "file_path": "src/auth/handler.ts",
                        "line_numbers": [47, 52],
                        "diff_snippet": (
                            "+ if (user.isValid) {\n"
                            "+   return authenticate(user);\n"
                            "+ }"
                        ),
                        "function_name": "validateUser",
                    },
                    "evidence": {
                        "type": "control_flow_error",
                        "description": "User object not validated before access",
                        "code_quote": "if (user.isValid)",
                    },
                    "attack_applied": {
                        "style": "control-flow-tracing",
                        "probe": "What happens when user is null or undefined?",
                    },
                    "impact": {
                        "if_exploited": "Application crashes with TypeError",
                        "affected_functionality": "User authentication",
                    },
                    "recommendation": (
                        "Add null check before accessing user properties: "
                        "if (user && user.isValid)"
                    ),
                    "confidence": 0.85,
                }
            ],
            "patterns_detected": [
                {
                    "pattern": "missing-null-checks",
                    "instances": 2,
                    "files_affected": ["src/auth/handler.ts", "src/auth/validator.ts"],
                    "description": "Multiple locations lack null safety checks",
                    "systemic_recommendation": (
                        "Consider using TypeScript strict null checks"
                    ),
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
                "highest_risk_file": "src/auth/handler.ts",
                "primary_weakness": "Insufficient null safety in authentication flow",
            },
        }
    }


@pytest.fixture
def valid_pr_report():
    """Valid PR red team report with all required fields."""
    return {
        "executive_summary": (
            "This PR introduces authentication changes with moderate risk. "
            "Key concerns include missing null checks in the auth handler "
            "and potential error handling gaps that could affect user experience."
        ),
        "pr_summary": {
            "title": "Add OAuth2 authentication",
            "description": "Implements OAuth2 authentication flow with refresh tokens",
            "files_changed": 5,
            "additions": 150,
            "deletions": 30,
            "pr_size": "medium",
            "high_risk_files": ["src/auth/handler.ts"],
        },
        "risk_level": "HIGH",
        "findings": [
            {
                "id": "PR-001",
                "severity": "HIGH",
                "title": "Missing input validation in auth handler",
                "description": "User input is not validated before processing, "
                "which could lead to injection attacks",
                "file_path": "src/auth/handler.ts",
                "line_ranges": [[45, 52]],
                "recommendation": (
                    "Add input validation using a schema validation library"
                ),
                "confidence": 0.85,
            }
        ],
        "findings_by_file": {
            "src/auth/handler.ts": [
                {
                    "id": "PR-001",
                    "severity": "HIGH",
                    "title": "Missing input validation in auth handler",
                    "description": "User input is not validated before processing",
                    "recommendation": "Add input validation using schema validation",
                    "confidence": 0.85,
                }
            ]
        },
        "breaking_changes": [
            {
                "type": "API signature change",
                "description": (
                    "Function authenticate() now requires additional scope parameter"
                ),
                "file_path": "src/auth/handler.ts",
                "impact": "Existing callers will fail until updated to pass scope",
                "mitigation": "Add default value for scope parameter",
            }
        ],
        "recommendations": [
            "Add comprehensive input validation",
            "Implement proper error handling",
            "Add unit tests for edge cases",
        ],
        "test_coverage_notes": "Test coverage increased by 15% with new auth tests",
    }
