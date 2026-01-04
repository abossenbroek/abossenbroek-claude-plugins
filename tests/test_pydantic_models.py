"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from red_agent.models import (
    AnalysisMode,
    AskUserQuestion,
    AskUserQuestionOption,
    AttackerFinding,
    AttackerOutput,
    Confidence,
    Evidence,
    Finding,
    FindingDetail,
    FindingDetailOption,
    FindingSeverity,
    FindingWithFixes,
    FixCoordinatorAskUserOutput,
    FixCoordinatorOutput,
    FixOption,
    FixPlannerOutput,
    GroundingAssessment,
    GroundingNotes,
    GroundingOutput,
    Pattern,
    QuestionBatch,
    RedTeamReport,
    RiskCategory,
    RiskCategoryName,
    RiskOverview,
    Severity,
)


class TestEnums:
    """Tests for enum types."""

    def test_severity_values(self):
        """Test severity enum has expected values."""
        assert Severity.CRITICAL == "CRITICAL"
        assert Severity.HIGH == "HIGH"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.LOW == "LOW"
        assert Severity.INFO == "INFO"

    def test_finding_severity_excludes_info(self):
        """Test finding severity excludes INFO and NONE."""
        values = [e.value for e in FindingSeverity]
        assert "INFO" not in values
        assert "NONE" not in values

    def test_confidence_levels(self):
        """Test confidence enum has expected values."""
        assert Confidence.EXPLORING == "exploring"
        assert Confidence.CERTAIN == "certain"
        assert len(Confidence) == 7

    def test_risk_category_names(self):
        """Test all 11 risk categories exist."""
        assert len(RiskCategoryName) == 11
        assert RiskCategoryName.REASONING_FLAWS == "reasoning-flaws"
        assert RiskCategoryName.CODE_DUPLICATION == "code-duplication"

    def test_analysis_modes(self):
        """Test analysis mode enum."""
        assert AnalysisMode.QUICK == "quick"
        assert AnalysisMode.STANDARD == "standard"
        assert AnalysisMode.DEEP == "deep"


class TestEvidenceModel:
    """Tests for Evidence model."""

    def test_valid_evidence(self):
        """Test creating valid evidence."""
        evidence = Evidence(quote="test quote", source="test.md")
        assert evidence.quote == "test quote"
        assert evidence.source == "test.md"
        assert evidence.message_num is None

    def test_evidence_with_message_num(self):
        """Test evidence with message number."""
        evidence = Evidence(quote="test", source="test.md", message_num=5)
        assert evidence.message_num == 5


class TestGroundingNotesModel:
    """Tests for GroundingNotes model."""

    def test_valid_grounding_notes(self):
        """Test creating valid grounding notes."""
        notes = GroundingNotes(evidence_strength=0.85)
        assert notes.evidence_strength == 0.85

    def test_evidence_strength_out_of_range(self):
        """Test that evidence_strength must be 0-1."""
        with pytest.raises(ValidationError):
            GroundingNotes(evidence_strength=1.5)

        with pytest.raises(ValidationError):
            GroundingNotes(evidence_strength=-0.1)


class TestFindingModel:
    """Tests for Finding model."""

    def test_valid_finding(self):
        """Test creating valid finding."""
        finding = Finding(
            id="RF-001",
            category="reasoning-flaws",
            severity=FindingSeverity.HIGH,
            title="Test finding title",
            confidence="85%",
        )
        assert finding.id == "RF-001"
        assert finding.severity == FindingSeverity.HIGH

    def test_invalid_id_format(self):
        """Test that invalid ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Finding(
                id="invalid",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Test title here",
                confidence="85%",
            )
        assert "XX-NNN" in str(exc_info.value)

    def test_three_letter_id(self):
        """Test that 3-letter IDs are valid."""
        finding = Finding(
            id="ABC-123",
            category="test",
            severity=FindingSeverity.HIGH,
            title="Test title here",
            confidence="85%",
        )
        assert finding.id == "ABC-123"

    def test_invalid_confidence_format(self):
        """Test that invalid confidence format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Finding(
                id="RF-001",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Test title here",
                confidence="85",  # Missing %
            )
        assert "percentage" in str(exc_info.value).lower()

    def test_title_too_short(self):
        """Test that title must be at least 10 characters."""
        with pytest.raises(ValidationError):
            Finding(
                id="RF-001",
                category="test",
                severity=FindingSeverity.HIGH,
                title="Short",  # Less than 10 chars
                confidence="85%",
            )


class TestPatternModel:
    """Tests for Pattern model."""

    def test_valid_pattern(self):
        """Test creating valid pattern."""
        pattern = Pattern(name="Test Pattern", description="A test pattern")
        assert pattern.name == "Test Pattern"
        assert pattern.instances == 1  # Default

    def test_instances_must_be_positive(self):
        """Test that instances must be >= 1."""
        with pytest.raises(ValidationError):
            Pattern(name="Test", description="Test", instances=0)


class TestRiskCategoryModel:
    """Tests for RiskCategory model."""

    def test_valid_risk_category(self):
        """Test creating valid risk category."""
        cat = RiskCategory(
            category=RiskCategoryName.REASONING_FLAWS, severity=Severity.HIGH
        )
        assert cat.category == RiskCategoryName.REASONING_FLAWS
        assert cat.count == 0  # Default

    def test_confidence_percentage_format(self):
        """Test that confidence must be percentage format."""
        cat = RiskCategory(
            category=RiskCategoryName.REASONING_FLAWS,
            severity=Severity.HIGH,
            confidence="85%",
        )
        assert cat.confidence == "85%"

    def test_invalid_confidence_format(self):
        """Test that invalid confidence format is rejected."""
        with pytest.raises(ValidationError):
            RiskCategory(
                category=RiskCategoryName.REASONING_FLAWS,
                severity=Severity.HIGH,
                confidence="invalid",
            )


class TestAttackerFindingModel:
    """Tests for AttackerFinding model."""

    def test_valid_attacker_finding_numeric_confidence(self):
        """Test attacker finding with numeric confidence."""
        finding = AttackerFinding(
            id="RF-001",
            severity="HIGH",
            title="Test",
            confidence=0.85,
            category="reasoning-flaws",
            target={"claim_id": "C-001"},
            evidence={"type": "logical_gap"},
            attack_applied={"style": "questioning", "probe": "Test probe"},
            impact={"if_exploited": "Test impact"},
            recommendation="Test recommendation text",
        )
        assert finding.confidence == 0.85

    def test_valid_attacker_finding_percentage_confidence(self):
        """Test attacker finding with percentage confidence."""
        finding = AttackerFinding(
            id="RF-001",
            severity="HIGH",
            title="Test",
            confidence="85%",
            category="reasoning-flaws",
            target={"claim_id": "C-001"},
            evidence={"type": "logical_gap"},
            attack_applied={"style": "questioning", "probe": "Test probe"},
            impact={"if_exploited": "Test impact"},
            recommendation="Test recommendation text",
        )
        assert finding.confidence == "85%"

    def test_numeric_confidence_out_of_range(self):
        """Test that numeric confidence must be 0-1."""
        with pytest.raises(ValidationError):
            AttackerFinding(
                id="RF-001",
                severity="HIGH",
                title="Test",
                confidence=2.0,
                category="reasoning-flaws",
                target={"claim_id": "C-001"},
                evidence={"type": "logical_gap"},
                attack_applied={"style": "questioning", "probe": "Test probe"},
                impact={"if_exploited": "Test impact"},
                recommendation="Test recommendation text",
            )

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError):
            AttackerFinding(id="RF-001", severity="HIGH", title="Test", confidence=0.85)


class TestAttackerOutputModel:
    """Tests for AttackerOutput model."""

    def test_valid_attacker_output(self, valid_attacker_output):
        """Test creating valid attacker output."""
        output = AttackerOutput.model_validate(valid_attacker_output)
        assert output.attack_results.attack_type == "reasoning-attacker"

    def test_missing_attack_results(self):
        """Test that missing attack_results is rejected."""
        with pytest.raises(ValidationError):
            AttackerOutput.model_validate({})


class TestGroundingAssessmentModel:
    """Tests for GroundingAssessment model."""

    def test_valid_assessment(self):
        """Test creating valid grounding assessment."""
        assessment = GroundingAssessment(
            finding_id="RF-001",
            evidence_strength=0.85,
            original_confidence=0.90,
            evidence_review={"evidence_exists": True},
            quote_verification={"match_quality": "exact"},
            inference_validity={"valid": True},
            adjusted_confidence=0.80,
        )
        assert assessment.evidence_strength == 0.85

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError):
            GroundingAssessment(
                finding_id="RF-001", evidence_strength=0.85, adjusted_confidence=0.80
            )


class TestGroundingOutputModel:
    """Tests for GroundingOutput model."""

    def test_valid_grounding_output(self, valid_grounding_output):
        """Test creating valid grounding output."""
        output = GroundingOutput.model_validate(valid_grounding_output)
        assert output.grounding_results.agent == "evidence-checker"


class TestRedTeamReportModel:
    """Tests for RedTeamReport model."""

    def test_valid_report(self, valid_report_output):
        """Test creating valid report."""
        report = RedTeamReport.model_validate(valid_report_output)
        assert report.risk_overview.overall_risk_level == Severity.HIGH

    def test_executive_summary_too_short(self):
        """Test that executive summary must be at least 50 chars."""
        with pytest.raises(ValidationError):
            RedTeamReport(
                executive_summary="Too short",
                risk_overview=RiskOverview(
                    overall_risk_level=Severity.LOW, categories=[]
                ),
                findings={},
            )


class TestFixOptionModel:
    """Tests for FixOption model."""

    def test_valid_fix_option(self):
        """Test creating valid fix option."""
        option = FixOption(
            label="A: Quick fix",
            description="Add validation check at entry point",
            pros=["Fast to implement", "Low risk"],
            cons=["Doesn't fix root cause"],
            complexity="LOW",
            affected_components=["AuthController"],
        )
        assert option.label == "A: Quick fix"
        assert option.complexity == "LOW"
        assert len(option.pros) == 2
        assert len(option.cons) == 1

    def test_complexity_case_insensitive(self):
        """Test that complexity is normalized to uppercase."""
        option = FixOption(
            label="B: Medium fix",
            description="Refactor the validation flow",
            complexity="medium",
            affected_components=[],
        )
        assert option.complexity == "MEDIUM"

    def test_invalid_complexity(self):
        """Test that invalid complexity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FixOption(
                label="C: Bad option",
                description="Invalid complexity level",
                complexity="EXTREME",
                affected_components=[],
            )
        assert "EXTREME" in str(exc_info.value)

    def test_defaults(self):
        """Test that defaults are applied correctly."""
        option = FixOption(
            label="A: Minimal",
            description="A minimal fix",
            complexity="LOW",
        )
        assert option.pros == []
        assert option.cons == []
        assert option.affected_components == []


class TestFixPlannerOutputModel:
    """Tests for FixPlannerOutput model."""

    def test_valid_fix_planner_output(self):
        """Test creating valid fix planner output."""
        output = FixPlannerOutput(
            finding_id="RF-001",
            finding_title="Invalid inference in authentication",
            options=[
                FixOption(
                    label="A: Add null check",
                    description="Quick fix to add null check",
                    complexity="LOW",
                ),
                FixOption(
                    label="B: Refactor auth",
                    description="Restructure auth validation",
                    complexity="MEDIUM",
                ),
            ],
        )
        assert output.finding_id == "RF-001"
        assert len(output.options) == 2

    def test_invalid_finding_id(self):
        """Test that invalid finding ID is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FixPlannerOutput(
                finding_id="invalid",
                finding_title="Test title",
                options=[
                    FixOption(
                        label="A: Fix",
                        description="A fix",
                        complexity="LOW",
                    )
                ],
            )
        assert "XX-NNN" in str(exc_info.value)

    def test_requires_at_least_one_option(self):
        """Test that at least one option is required."""
        with pytest.raises(ValidationError):
            FixPlannerOutput(
                finding_id="RF-001",
                finding_title="Test title",
                options=[],
            )

    def test_max_three_options(self):
        """Test that max three options are allowed."""
        with pytest.raises(ValidationError):
            FixPlannerOutput(
                finding_id="RF-001",
                finding_title="Test title",
                options=[
                    FixOption(label="A", description="A", complexity="LOW"),
                    FixOption(label="B", description="B", complexity="LOW"),
                    FixOption(label="C", description="C", complexity="LOW"),
                    FixOption(label="D", description="D", complexity="LOW"),
                ],
            )


class TestFindingWithFixesModel:
    """Tests for FindingWithFixes model."""

    def test_valid_finding_with_fixes(self):
        """Test creating valid finding with fixes."""
        finding = FindingWithFixes(
            finding_id="AG-002",
            title="Hidden assumption about user roles",
            severity="HIGH",
            options=[
                FixOption(
                    label="A: Role check",
                    description="Add explicit role validation",
                    complexity="LOW",
                    affected_components=["RoleMiddleware"],
                )
            ],
        )
        assert finding.finding_id == "AG-002"
        assert finding.severity == "HIGH"

    def test_invalid_severity(self):
        """Test that invalid severity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FindingWithFixes(
                finding_id="RF-001",
                title="Test finding",
                severity="EXTREME",
                options=[FixOption(label="A", description="A", complexity="LOW")],
            )
        assert "EXTREME" in str(exc_info.value)


class TestFixCoordinatorOutputModel:
    """Tests for FixCoordinatorOutput model."""

    def test_valid_fix_coordinator_output(self):
        """Test creating valid fix coordinator output."""
        output = FixCoordinatorOutput(
            findings_with_fixes=[
                FindingWithFixes(
                    finding_id="RF-001",
                    title="First finding",
                    severity="CRITICAL",
                    options=[
                        FixOption(label="A", description="Fix A", complexity="LOW")
                    ],
                ),
                FindingWithFixes(
                    finding_id="AG-002",
                    title="Second finding",
                    severity="HIGH",
                    options=[
                        FixOption(label="A", description="Fix A", complexity="LOW"),
                        FixOption(label="B", description="Fix B", complexity="MEDIUM"),
                    ],
                ),
            ]
        )
        assert len(output.findings_with_fixes) == 2
        assert output.findings_with_fixes[0].severity == "CRITICAL"

    def test_empty_findings_allowed(self):
        """Test that empty findings list is allowed."""
        output = FixCoordinatorOutput(findings_with_fixes=[])
        assert len(output.findings_with_fixes) == 0


class TestAskUserQuestionOptionModel:
    """Tests for AskUserQuestionOption model."""

    def test_valid_option(self):
        """Test creating valid option."""
        option = AskUserQuestionOption(
            label="A: Quick fix [LOW]",
            description="Add validation check at entry point",
        )
        assert option.label == "A: Quick fix [LOW]"
        assert "validation" in option.description

    def test_empty_label_rejected(self):
        """Test that empty label is rejected."""
        with pytest.raises(ValidationError):
            AskUserQuestionOption(label="", description="Some description")


class TestAskUserQuestionModel:
    """Tests for AskUserQuestion model."""

    def test_valid_question(self):
        """Test creating valid question."""
        question = AskUserQuestion(
            question="RF-001: Invalid auth inference\nHow should we fix?",
            header="RF-001",
            multiSelect=False,
            options=[
                AskUserQuestionOption(label="A: Fix", description="Quick fix"),
                AskUserQuestionOption(label="B: Refactor", description="Full refactor"),
            ],
        )
        assert question.header == "RF-001"
        assert len(question.options) == 2
        assert question.multiSelect is False

    def test_header_too_long(self):
        """Test that header > 12 chars is rejected."""
        with pytest.raises(ValidationError):
            AskUserQuestion(
                question="Test question here",
                header="ThisHeaderIsTooLong",
                multiSelect=False,
                options=[
                    AskUserQuestionOption(label="A", description="A"),
                    AskUserQuestionOption(label="B", description="B"),
                ],
            )

    def test_question_too_short(self):
        """Test that question < 10 chars is rejected."""
        with pytest.raises(ValidationError):
            AskUserQuestion(
                question="Short?",
                header="RF-001",
                multiSelect=False,
                options=[
                    AskUserQuestionOption(label="A", description="A"),
                    AskUserQuestionOption(label="B", description="B"),
                ],
            )

    def test_too_few_options(self):
        """Test that < 2 options is rejected."""
        with pytest.raises(ValidationError):
            AskUserQuestion(
                question="Test question here",
                header="RF-001",
                multiSelect=False,
                options=[AskUserQuestionOption(label="A", description="A")],
            )

    def test_too_many_options(self):
        """Test that > 4 options is rejected."""
        with pytest.raises(ValidationError):
            AskUserQuestion(
                question="Test question here",
                header="RF-001",
                multiSelect=False,
                options=[
                    AskUserQuestionOption(label="A", description="A"),
                    AskUserQuestionOption(label="B", description="B"),
                    AskUserQuestionOption(label="C", description="C"),
                    AskUserQuestionOption(label="D", description="D"),
                    AskUserQuestionOption(label="E", description="E"),
                ],
            )


class TestQuestionBatchModel:
    """Tests for QuestionBatch model."""

    def test_valid_batch(self):
        """Test creating valid question batch."""
        batch = QuestionBatch(
            batch_number=1,
            severity_level="CRITICAL_HIGH",
            questions=[
                AskUserQuestion(
                    question="RF-001: Test finding question",
                    header="RF-001",
                    multiSelect=False,
                    options=[
                        AskUserQuestionOption(label="A", description="Fix A"),
                        AskUserQuestionOption(label="B", description="Fix B"),
                    ],
                )
            ],
        )
        assert batch.batch_number == 1
        assert batch.severity_level == "CRITICAL_HIGH"

    def test_invalid_severity_level(self):
        """Test that invalid severity level is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QuestionBatch(
                batch_number=1,
                severity_level="INVALID",
                questions=[
                    AskUserQuestion(
                        question="Test question here",
                        header="RF-001",
                        multiSelect=False,
                        options=[
                            AskUserQuestionOption(label="A", description="A"),
                            AskUserQuestionOption(label="B", description="B"),
                        ],
                    )
                ],
            )
        assert "INVALID" in str(exc_info.value)

    def test_batch_number_must_be_positive(self):
        """Test that batch number must be >= 1."""
        with pytest.raises(ValidationError):
            QuestionBatch(
                batch_number=0,
                severity_level="HIGH",
                questions=[
                    AskUserQuestion(
                        question="Test question here",
                        header="RF-001",
                        multiSelect=False,
                        options=[
                            AskUserQuestionOption(label="A", description="A"),
                            AskUserQuestionOption(label="B", description="B"),
                        ],
                    )
                ],
            )

    def test_max_four_questions_per_batch(self):
        """Test that > 4 questions per batch is rejected."""
        question = AskUserQuestion(
            question="Test question here",
            header="RF-001",
            multiSelect=False,
            options=[
                AskUserQuestionOption(label="A", description="A"),
                AskUserQuestionOption(label="B", description="B"),
            ],
        )
        with pytest.raises(ValidationError):
            QuestionBatch(
                batch_number=1,
                severity_level="HIGH",
                questions=[question, question, question, question, question],
            )


class TestFindingDetailOptionModel:
    """Tests for FindingDetailOption model."""

    def test_valid_option(self):
        """Test creating valid finding detail option."""
        option = FindingDetailOption(
            label="A: Quick fix",
            description="Add validation",
            pros=["Fast", "Low risk"],
            cons=["Doesn't fix root cause"],
            complexity="LOW",
            affected_components=["AuthController"],
        )
        assert option.complexity == "LOW"
        assert len(option.pros) == 2

    def test_complexity_normalized_to_uppercase(self):
        """Test that complexity is normalized."""
        option = FindingDetailOption(
            label="B",
            description="Desc",
            complexity="medium",
        )
        assert option.complexity == "MEDIUM"


class TestFindingDetailModel:
    """Tests for FindingDetail model."""

    def test_valid_finding_detail(self):
        """Test creating valid finding detail."""
        detail = FindingDetail(
            finding_id="RF-001",
            title="Invalid auth inference",
            severity="CRITICAL",
            full_options=[
                FindingDetailOption(label="A", description="Fix A", complexity="LOW")
            ],
        )
        assert detail.finding_id == "RF-001"
        assert detail.severity == "CRITICAL"

    def test_invalid_finding_id(self):
        """Test that invalid finding ID is rejected."""
        with pytest.raises(ValidationError):
            FindingDetail(
                finding_id="invalid",
                title="Title",
                severity="HIGH",
                full_options=[
                    FindingDetailOption(label="A", description="A", complexity="LOW")
                ],
            )


class TestFixCoordinatorAskUserOutputModel:
    """Tests for FixCoordinatorAskUserOutput model."""

    def test_valid_output(self):
        """Test creating valid AskUserQuestion-compatible output."""
        output = FixCoordinatorAskUserOutput(
            question_batches=[
                QuestionBatch(
                    batch_number=1,
                    severity_level="CRITICAL_HIGH",
                    questions=[
                        AskUserQuestion(
                            question="RF-001: Invalid inference\nSeverity: CRITICAL",
                            header="RF-001",
                            multiSelect=False,
                            options=[
                                AskUserQuestionOption(
                                    label="A: Fix [LOW]",
                                    description="Quick fix",
                                ),
                                AskUserQuestionOption(
                                    label="B: Refactor [MEDIUM]",
                                    description="Full refactor",
                                ),
                            ],
                        )
                    ],
                )
            ],
            finding_details=[
                FindingDetail(
                    finding_id="RF-001",
                    title="Invalid inference",
                    severity="CRITICAL",
                    full_options=[
                        FindingDetailOption(
                            label="A: Fix [LOW]",
                            description="Quick fix",
                            complexity="LOW",
                        )
                    ],
                )
            ],
        )
        assert len(output.question_batches) == 1
        assert len(output.finding_details) == 1

    def test_requires_at_least_one_batch(self):
        """Test that at least one question batch is required."""
        with pytest.raises(ValidationError):
            FixCoordinatorAskUserOutput(
                question_batches=[],
                finding_details=[],
            )

    def test_finding_details_optional(self):
        """Test that finding_details can be empty."""
        output = FixCoordinatorAskUserOutput(
            question_batches=[
                QuestionBatch(
                    batch_number=1,
                    severity_level="HIGH",
                    questions=[
                        AskUserQuestion(
                            question="Test question here",
                            header="RF-001",
                            multiSelect=False,
                            options=[
                                AskUserQuestionOption(label="A", description="A"),
                                AskUserQuestionOption(label="B", description="B"),
                            ],
                        )
                    ],
                )
            ],
        )
        assert len(output.finding_details) == 0
