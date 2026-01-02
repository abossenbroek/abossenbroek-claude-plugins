"""Pydantic models for attack strategy output."""

from pydantic import BaseModel, Field


class StrategyTarget(BaseModel):
    """A target for attack."""

    claim_id: str | None = None
    area: str | None = None
    reason: str


class SelectedVector(BaseModel):
    """A selected attack vector."""

    category: str
    priority: int = Field(ge=1)
    rationale: str
    attack_styles: list[str] = Field(default_factory=list)
    targets: list[StrategyTarget] = Field(default_factory=list)


class AttackerAssignment(BaseModel):
    """Assignment for an attacker agent."""

    categories: list[str] = Field(default_factory=list)
    targets: list[StrategyTarget] = Field(default_factory=list)


class GroundingPlan(BaseModel):
    """Grounding plan configuration."""

    enabled: bool = True
    agents: list[str] = Field(default_factory=list)


class MetaAnalysisPlan(BaseModel):
    """Meta-analysis configuration."""

    enabled: bool = False
    focus: str | None = None


class AttackStrategyResults(BaseModel):
    """Results from attack strategist."""

    mode: str
    total_vectors: int = Field(ge=0)
    selected_vectors: list[SelectedVector] = Field(default_factory=list)
    attacker_assignments: dict[str, AttackerAssignment] = Field(default_factory=dict)
    grounding_plan: GroundingPlan | None = None
    meta_analysis: MetaAnalysisPlan | None = None
    notes: list[str] = Field(default_factory=list)


class AttackStrategyOutput(BaseModel):
    """Root structure for attack strategy output."""

    attack_strategy: AttackStrategyResults
