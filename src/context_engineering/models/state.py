"""State management models for context engineering plugin.

This module provides Pydantic models for managing shared state across sub-agents,
enabling immutable configuration and mutable results without full context passing.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FocusArea(str, Enum):
    """Analysis focus areas for context engineering."""

    ALL = "all"
    CONTEXT = "context"
    ORCHESTRATION = "orchestration"
    HANDOFF = "handoff"


class AnalysisMode(str, Enum):
    """Analysis depth modes."""

    QUICK = "quick"  # Fast surface-level analysis
    STANDARD = "standard"  # Balanced depth and speed
    DEEP = "deep"  # Comprehensive analysis


class FileRef(BaseModel):
    """Reference to a cached file with optional content."""

    id: str = Field(..., description="Unique identifier for the file")
    path: str = Field(..., description="Absolute path to the file")
    loaded: bool = Field(..., description="Whether content has been loaded")
    content: str | None = Field(None, description="File content if loaded")
    token_estimate: int = Field(..., description="Estimated token count")


class ImmutableState(BaseModel, frozen=True):
    """Immutable configuration set at session start.

    This state cannot be modified after initialization, ensuring
    consistent configuration across all sub-agents.
    """

    plugin_path: str = Field(..., description="Absolute path to plugin directory")
    focus_area: FocusArea = Field(..., description="Analysis focus area")
    mode: AnalysisMode = Field(..., description="Analysis depth mode")
    user_request: str = Field(..., description="Original user request")
    session_id: str = Field(..., description="Unique session identifier")


class MutableState(BaseModel):
    """Mutable state that can be updated during analysis."""

    file_cache: dict[str, FileRef] = Field(
        default_factory=dict, description="Cache of loaded files"
    )
    intermediate_results: dict[str, Any] = Field(
        default_factory=dict, description="Results from completed phases"
    )
    phase_completed: list[str] = Field(
        default_factory=list, description="List of completed phase names"
    )
    user_selections: dict[str, Any] = Field(
        default_factory=dict, description="User choices and preferences"
    )


class ContextEngineeringState(BaseModel):
    """Complete state for context engineering analysis session.

    Combines immutable configuration with mutable results and
    provides optimistic locking for concurrent access.
    """

    immutable: ImmutableState = Field(..., description="Immutable session config")
    mutable: MutableState = Field(..., description="Mutable analysis state")
    lock_holder: str | None = Field(None, description="Current lock holder agent name")
    version: int = Field(1, description="Version for optimistic locking")
