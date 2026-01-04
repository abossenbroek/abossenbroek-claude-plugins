"""Pydantic models for fix orchestration pipeline.

This module provides type-safe models for validating outputs from the fix-orchestrator
and its 7 sub-agents in the 6-stage fix execution pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field


class FixReaderOutput(BaseModel):
    """Output from fix-reader agent."""

    finding_id: str
    parsed_intent: str
    context_hints: list[str] = Field(default_factory=list)


class FixPlanV2Output(BaseModel):
    """Output from fix-planner-v2 agent."""

    finding_id: str
    fix_plan: dict[str, Any]  # Contains changes, execution_order, risks


class FixRedTeamerOutput(BaseModel):
    """Output from fix-red-teamer agent."""

    finding_id: str
    validation: dict[str, Any]  # Contains addresses_issue, is_minimal, etc.
    approved: bool
    adjusted_plan: dict[str, Any] | None = None


class FixApplicatorOutput(BaseModel):
    """Output from fix-applicator agent."""

    finding_id: str
    applied_changes: dict[str, Any]  # Contains file, diff, etc.
    success: bool
    error: str | None = None


class FixCommitterOutput(BaseModel):
    """Output from fix-committer agent."""

    finding_id: str
    commit_result: (
        dict[str, Any] | None
    )  # Contains commit_hash, files_committed, message
    success: bool
    error: str | None = None


class FixValidatorOutput(BaseModel):
    """Output from fix-validator agent."""

    finding_id: str
    commit_hash: str
    validation_result: dict[str, Any]  # Contains tests_passed, lint_passed, etc.


class FixPhaseCoordinatorOutput(BaseModel):
    """Output from fix-phase-coordinator agent."""

    finding_id: str
    status: str  # success | failed
    commit_hash: str | None = None
    files_changed: list[str] = Field(default_factory=list)
    validation: str | None = None
    retry_count: int = Field(ge=0, le=2)
    error: str | None = None
    revert_command: str | None = None


class FixOrchestratorOutput(BaseModel):
    """Output from fix-orchestrator agent.

    Note: question_batches uses QuestionBatch from outputs module.
    Import QuestionBatch separately when needed for type checking.
    """

    execution_summary: dict[str, Any] | None = None  # After execution
    question_batches: list[Any] | None = None  # list[QuestionBatch] from outputs
