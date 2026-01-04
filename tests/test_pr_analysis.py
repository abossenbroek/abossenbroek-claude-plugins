"""Tests for PR analysis Pydantic models and validation functions."""

import pytest
from pydantic import ValidationError

from red_agent.models import (
    BreakingChange,
    CodeAttackApplied,
    CodeAttackerFinding,
    CodeAttackerOutput,
    CodeAttackSummary,
    CodeFindingEvidence,
    CodeFindingImpact,
    CodeFindingTarget,
    CodePatternDetected,
    DiffAnalysisOutput,
    DiffMetadata,
    DiffSummary,
    FileAnalysis,
    FileMetadata,
    FileRef,
    FocusArea,
    PatternDetected,
    PRFinding,
    PRRedTeamReport,
    PRSummary,
    RiskCategoryExposure,
)
from red_agent.scripts.validate_agent_output import (
    validate_code_attacker,
    validate_diff_analysis,
    validate_pr_report,
)


class TestDiffMetadataModel:
    """Tests for DiffMetadata model."""

    def test_valid_diff_metadata(self, valid_diff_metadata):
        """Test creating valid diff metadata."""
        metadata = DiffMetadata.model_validate(valid_diff_metadata)
        assert metadata.git_operation == "staged"
        assert metadata.total_files_changed == 3
        assert metadata.pr_size == "small"

    def test_git_operation_values(self):
        """Test that git_operation must be valid literal."""
        for op in ["staged", "working", "branch", "diff_file"]:
            metadata = DiffMetadata(
                git_operation=op,
                total_files_changed=1,
                total_additions=10,
                total_deletions=5,
                pr_size="tiny",
            )
            assert metadata.git_operation == op

    def test_invalid_git_operation(self):
        """Test that invalid git_operation is rejected."""
        with pytest.raises(ValidationError):
            DiffMetadata(
                git_operation="invalid",
                total_files_changed=1,
                total_additions=10,
                total_deletions=5,
                pr_size="tiny",
            )

    def test_pr_size_classification(self):
        """Test pr_size literal values."""
        for size in ["tiny", "small", "medium", "large", "massive"]:
            metadata = DiffMetadata(
                git_operation="staged",
                total_files_changed=1,
                total_additions=10,
                total_deletions=5,
                pr_size=size,
            )
            assert metadata.pr_size == size

    def test_invalid_pr_size(self):
        """Test that invalid pr_size is rejected."""
        with pytest.raises(ValidationError):
            DiffMetadata(
                git_operation="staged",
                total_files_changed=1,
                total_additions=10,
                total_deletions=5,
                pr_size="huge",
            )

    def test_negative_counts_rejected(self):
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError):
            DiffMetadata(
                git_operation="staged",
                total_files_changed=-1,
                total_additions=10,
                total_deletions=5,
                pr_size="tiny",
            )


class TestFileRefModel:
    """Tests for FileRef model."""

    def test_valid_file_ref(self):
        """Test creating valid file reference."""
        ref = FileRef(
            file_id="auth_001",
            path="src/auth/handler.ts",
            risk_score=0.85,
            diff_snippet="+ function validate() {",
        )
        assert ref.file_id == "auth_001"
        assert ref.risk_score == 0.85

    def test_risk_score_constraints(self):
        """Test risk_score must be between 0.0 and 1.0."""
        # Valid boundary values
        FileRef(
            file_id="test",
            path="test.py",
            risk_score=0.0,
            diff_snippet="test",
        )
        FileRef(
            file_id="test",
            path="test.py",
            risk_score=1.0,
            diff_snippet="test",
        )

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            FileRef(
                file_id="test",
                path="test.py",
                risk_score=1.5,
                diff_snippet="test",
            )

        # Invalid: below 0.0
        with pytest.raises(ValidationError):
            FileRef(
                file_id="test",
                path="test.py",
                risk_score=-0.1,
                diff_snippet="test",
            )

    def test_line_ranges_format(self):
        """Test line_ranges is properly formatted."""
        ref = FileRef(
            file_id="test",
            path="test.py",
            risk_score=0.5,
            diff_snippet="test",
            line_ranges=[[10, 20], [30, 40]],
        )
        assert ref.line_ranges == [[10, 20], [30, 40]]

    def test_empty_file_id_rejected(self):
        """Test that empty file_id is rejected."""
        with pytest.raises(ValidationError):
            FileRef(
                file_id="",
                path="test.py",
                risk_score=0.5,
                diff_snippet="test",
            )


class TestDiffAnalysisOutputModel:
    """Tests for DiffAnalysisOutput model."""

    def test_valid_diff_analysis_output(self, valid_diff_analysis_output):
        """Test creating valid diff analysis output."""
        output = DiffAnalysisOutput.model_validate(valid_diff_analysis_output)
        assert output.diff_analysis.summary.files_changed == 3
        assert len(output.diff_analysis.file_analysis) == 1

    def test_diff_summary_fields(self):
        """Test DiffSummary has all required fields."""
        summary = DiffSummary(
            files_changed=5,
            high_risk_files=2,
            medium_risk_files=2,
            low_risk_files=1,
            total_insertions=150,
            total_deletions=30,
        )
        assert summary.files_changed == 5
        assert summary.high_risk_files == 2

    def test_file_analysis_risk_levels(self):
        """Test FileAnalysis risk_level values."""
        for level in ["high", "medium", "low"]:
            analysis = FileAnalysis(
                file_id="test_001",
                path="test.py",
                risk_level=level,
                risk_score=0.5,
                change_summary="Test change",
                change_type="modification",
                insertions=10,
                deletions=5,
            )
            assert analysis.risk_level == level

    def test_invalid_risk_level(self):
        """Test that invalid risk_level is rejected."""
        with pytest.raises(ValidationError):
            FileAnalysis(
                file_id="test_001",
                path="test.py",
                risk_level="critical",
                risk_score=0.5,
                change_summary="Test change",
                change_type="modification",
                insertions=10,
                deletions=5,
            )

    def test_risk_category_exposure(self):
        """Test RiskCategoryExposure model."""
        exposure = RiskCategoryExposure(
            category="reasoning-flaws",
            exposure="high",
            affected_files=["auth_001"],
            notes="Critical authentication changes detected",
        )
        assert exposure.exposure == "high"
        assert "auth_001" in exposure.affected_files

    def test_pattern_detected(self):
        """Test PatternDetected model."""
        pattern = PatternDetected(
            pattern="error-handling-changes",
            description="Multiple error handling modifications",
            instances=3,
            affected_files=["file1.ts", "file2.ts"],
            risk_implication="Error handling changes may introduce regressions",
        )
        assert pattern.instances == 3

    def test_focus_area(self):
        """Test FocusArea model."""
        area = FocusArea(
            area="authentication",
            files=["auth_001", "auth_002"],
            rationale="Critical security component with multiple changes",
        )
        assert area.area == "authentication"


class TestCodeAttackerOutputModel:
    """Tests for CodeAttackerOutput model."""

    def test_valid_code_attacker_output(self, valid_code_attacker_output):
        """Test creating valid code attacker output."""
        output = CodeAttackerOutput.model_validate(valid_code_attacker_output)
        assert output.attack_results.attack_type == "code-reasoning-attacker"
        assert len(output.attack_results.findings) == 1

    def test_code_finding_id_patterns(self):
        """Test that finding IDs accept LE-, AG-, EH- prefixes."""
        for prefix in ["LE", "AG", "EH"]:
            finding = CodeAttackerFinding(
                id=f"{prefix}-001",
                category="logic-errors",
                severity="HIGH",
                title="Test finding",
                target=CodeFindingTarget(
                    file_path="test.py",
                    diff_snippet="test code",
                ),
                evidence=CodeFindingEvidence(type="control_flow_error"),
                attack_applied=CodeAttackApplied(
                    style="control-flow-tracing",
                    probe="What happens when X fails?",
                ),
                impact=CodeFindingImpact(if_exploited="System crashes"),
                recommendation="Add proper error handling to fix this issue",
                confidence=0.85,
            )
            assert finding.id == f"{prefix}-001"

    def test_invalid_finding_id_format(self):
        """Test that invalid finding ID format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CodeAttackerFinding(
                id="INVALID",
                category="logic-errors",
                severity="HIGH",
                title="Test finding",
                target=CodeFindingTarget(
                    file_path="test.py",
                    diff_snippet="test code",
                ),
                evidence=CodeFindingEvidence(type="test"),
                attack_applied=CodeAttackApplied(style="test", probe="test"),
                impact=CodeFindingImpact(),
                recommendation="Add proper error handling to fix this issue",
                confidence=0.85,
            )
        assert "XX-NNN" in str(exc_info.value)

    def test_severity_level_validation(self):
        """Test that severity must be valid level."""
        valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        for severity in valid_severities:
            finding = CodeAttackerFinding(
                id="LE-001",
                category="logic-errors",
                severity=severity,
                title="Test finding",
                target=CodeFindingTarget(
                    file_path="test.py",
                    diff_snippet="test code",
                ),
                evidence=CodeFindingEvidence(type="test"),
                attack_applied=CodeAttackApplied(style="test", probe="test"),
                impact=CodeFindingImpact(),
                recommendation="Add proper error handling to fix this issue",
                confidence=0.85,
            )
            assert finding.severity == severity

    def test_invalid_severity_level(self):
        """Test that invalid severity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CodeAttackerFinding(
                id="LE-001",
                category="logic-errors",
                severity="EXTREME",
                title="Test finding",
                target=CodeFindingTarget(
                    file_path="test.py",
                    diff_snippet="test code",
                ),
                evidence=CodeFindingEvidence(type="test"),
                attack_applied=CodeAttackApplied(style="test", probe="test"),
                impact=CodeFindingImpact(),
                recommendation="Add proper error handling to fix this issue",
                confidence=0.85,
            )
        assert "EXTREME" in str(exc_info.value)

    def test_confidence_constraints(self):
        """Test confidence must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            CodeAttackerFinding(
                id="LE-001",
                category="logic-errors",
                severity="HIGH",
                title="Test finding",
                target=CodeFindingTarget(
                    file_path="test.py",
                    diff_snippet="test code",
                ),
                evidence=CodeFindingEvidence(type="test"),
                attack_applied=CodeAttackApplied(style="test", probe="test"),
                impact=CodeFindingImpact(),
                recommendation="Add proper error handling to fix this issue",
                confidence=1.5,
            )

    def test_code_pattern_detected(self):
        """Test CodePatternDetected model."""
        pattern = CodePatternDetected(
            pattern="error-handling-gaps",
            instances=2,
            files_affected=["file1.ts", "file2.ts"],
            description="Missing error handling in async operations",
        )
        assert pattern.instances == 2
        assert len(pattern.files_affected) == 2

    def test_code_attack_summary(self):
        """Test CodeAttackSummary model."""
        summary = CodeAttackSummary(
            total_findings=3,
            by_severity={"critical": 0, "high": 2, "medium": 1},
            highest_risk_file="src/auth.ts",
            primary_weakness="Insufficient error handling",
        )
        assert summary.total_findings == 3


class TestPRRedTeamReportModel:
    """Tests for PRRedTeamReport model."""

    def test_valid_pr_report(self, valid_pr_report):
        """Test creating valid PR report."""
        report = PRRedTeamReport.model_validate(valid_pr_report)
        assert report.risk_level == "HIGH"
        assert report.pr_summary.files_changed == 5

    def test_executive_summary_min_length(self):
        """Test that executive_summary must be at least 50 chars."""
        with pytest.raises(ValidationError):
            PRRedTeamReport(
                executive_summary="Too short",
                pr_summary=PRSummary(
                    files_changed=1,
                    additions=10,
                    deletions=5,
                    pr_size="tiny",
                ),
                risk_level="LOW",
            )

    def test_pr_summary_fields(self):
        """Test PRSummary model fields."""
        summary = PRSummary(
            title="Add authentication feature",
            description="Implements OAuth2 authentication",
            files_changed=5,
            additions=150,
            deletions=30,
            pr_size="medium",
            high_risk_files=["src/auth/handler.ts"],
        )
        assert summary.pr_size == "medium"
        assert len(summary.high_risk_files) == 1

    def test_pr_finding_model(self):
        """Test PRFinding model."""
        finding = PRFinding(
            id="PR-001",
            severity="HIGH",
            title="Missing input validation",
            description="User input is not validated before processing in auth handler",
            file_path="src/auth/handler.ts",
            line_ranges=[[45, 52]],
            recommendation="Add input validation using the validator library",
            confidence=0.85,
        )
        assert finding.id == "PR-001"
        assert finding.severity == "HIGH"

    def test_pr_finding_id_format(self):
        """Test PRFinding ID must match XX-NNN or XXX-NNN pattern."""
        with pytest.raises(ValidationError) as exc_info:
            PRFinding(
                id="invalid",
                severity="HIGH",
                title="Test finding",
                description="This is a test finding description that is long enough",
                recommendation="Fix this issue by implementing proper validation",
                confidence=0.85,
            )
        assert "XX-NNN" in str(exc_info.value)

    def test_breaking_change_model(self):
        """Test BreakingChange model."""
        change = BreakingChange(
            type="API signature change",
            description="Function authenticate() now requires an additional parameter",
            file_path="src/auth/handler.ts",
            impact="Existing callers will fail until updated",
            mitigation="Add default value for new parameter",
        )
        assert change.type == "API signature change"

    def test_risk_level_values(self):
        """Test risk_level literal values."""
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            report = PRRedTeamReport(
                executive_summary="This is a comprehensive PR analysis report "
                "with sufficient length to pass validation.",
                pr_summary=PRSummary(
                    files_changed=1,
                    additions=10,
                    deletions=5,
                    pr_size="tiny",
                ),
                risk_level=level,
            )
            assert report.risk_level == level


class TestFileMetadataModel:
    """Tests for FileMetadata model."""

    def test_valid_file_metadata(self):
        """Test creating valid file metadata."""
        metadata = FileMetadata(
            path="src/auth/handler.ts",
            additions=25,
            deletions=10,
            change_type="modified",
            risk_score=0.75,
        )
        assert metadata.path == "src/auth/handler.ts"
        assert metadata.change_type == "modified"

    def test_change_type_values(self):
        """Test change_type literal values."""
        for change_type in ["added", "modified", "deleted"]:
            metadata = FileMetadata(
                path="test.py",
                additions=10,
                deletions=5,
                change_type=change_type,
                risk_score=0.5,
            )
            assert metadata.change_type == change_type

    def test_invalid_change_type(self):
        """Test that invalid change_type is rejected."""
        with pytest.raises(ValidationError):
            FileMetadata(
                path="test.py",
                additions=10,
                deletions=5,
                change_type="renamed",
                risk_score=0.5,
            )

    def test_risk_score_bounds(self):
        """Test risk_score must be 0.0-1.0."""
        with pytest.raises(ValidationError):
            FileMetadata(
                path="test.py",
                additions=10,
                deletions=5,
                change_type="modified",
                risk_score=1.5,
            )


class TestValidateDiffAnalysis:
    """Tests for validate_diff_analysis() function."""

    def test_valid_diff_analysis(self, valid_diff_analysis_output):
        """Test validation passes for valid output."""
        result = validate_diff_analysis(valid_diff_analysis_output)
        assert result.is_valid

    def test_missing_diff_analysis_key(self):
        """Test validation fails when diff_analysis key is missing."""
        result = validate_diff_analysis({"wrong_key": {}})
        assert not result.is_valid
        assert any("diff_analysis" in e for e in result.errors)

    def test_missing_summary(self, valid_diff_analysis_output):
        """Test warning when summary is missing."""
        data = {
            "diff_analysis": {
                "file_analysis": valid_diff_analysis_output["diff_analysis"][
                    "file_analysis"
                ],
            }
        }
        result = validate_diff_analysis(data)
        assert not result.is_valid  # summary is required

    def test_empty_file_analysis_warning(self):
        """Test warning when file_analysis is empty."""
        data = {
            "diff_analysis": {
                "summary": {
                    "files_changed": 0,
                    "high_risk_files": 0,
                    "medium_risk_files": 0,
                    "low_risk_files": 0,
                    "total_insertions": 0,
                    "total_deletions": 0,
                },
                "file_analysis": [],
            }
        }
        result = validate_diff_analysis(data)
        assert result.is_valid
        assert any("file_analysis" in w for w in result.warnings)


class TestValidateCodeAttacker:
    """Tests for validate_code_attacker() function."""

    def test_valid_code_attacker(self, valid_code_attacker_output):
        """Test validation passes for valid output."""
        result = validate_code_attacker(valid_code_attacker_output)
        assert result.is_valid

    def test_missing_attack_results(self):
        """Test validation fails when attack_results is missing."""
        result = validate_code_attacker({"wrong_key": {}})
        assert not result.is_valid
        assert any("attack_results" in e for e in result.errors)

    def test_no_findings_warning(self):
        """Test warning when no findings are reported."""
        data = {
            "attack_results": {
                "attack_type": "code-reasoning-attacker",
                "findings": [],
                "summary": {"total_findings": 0},
            }
        }
        result = validate_code_attacker(data)
        assert result.is_valid
        assert any("No findings" in w for w in result.warnings)


class TestValidatePRReport:
    """Tests for validate_pr_report() function."""

    def test_valid_pr_report(self, valid_pr_report):
        """Test validation passes for valid output."""
        result = validate_pr_report(valid_pr_report)
        assert result.is_valid

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        result = validate_pr_report({})
        assert not result.is_valid

    def test_short_executive_summary_warning(self):
        """Test warning when executive summary is short."""
        data = {
            "executive_summary": "Short",
            "pr_summary": {
                "files_changed": 1,
                "additions": 10,
                "deletions": 5,
                "pr_size": "tiny",
            },
            "risk_level": "LOW",
        }
        result = validate_pr_report(data)
        # Validation fails because executive_summary < 50 chars
        assert not result.is_valid

    def test_no_findings_warning(self, valid_pr_report):
        """Test warning when no findings are reported."""
        data = valid_pr_report.copy()
        data["findings"] = []
        result = validate_pr_report(data)
        assert result.is_valid
        assert any("No findings" in w for w in result.warnings)

    def test_missing_test_coverage_warning(self, valid_pr_report):
        """Test warning when test_coverage_notes is missing."""
        data = valid_pr_report.copy()
        if "test_coverage_notes" in data:
            del data["test_coverage_notes"]
        result = validate_pr_report(data)
        assert any("test_coverage_notes" in w for w in result.warnings)
