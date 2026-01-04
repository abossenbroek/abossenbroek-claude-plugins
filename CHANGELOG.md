# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-01-04

### Added

- **jscpd Integration** - Duplicate code detection for PR analysis
  - npm dependency: jscpd 4.0.5 with exact version pinning
  - New `duplicate-code-analyzer` agent (5th parallel attacker)
  - 11th risk category: `code-duplication` for DRY violations
  - Configuration file (`.jscpd.json`) with detection thresholds
  - Graceful degradation if jscpd not installed

- **Security Infrastructure for npm Dependencies**
  - SHA-512 integrity hashes in package-lock.json (119 packages)
  - Pre-commit npm audit hooks (audit, integrity verification, lock file check)
  - CI validation for npm dependencies in GitHub Actions
  - MITM and supply chain attack protection
  - Integrity verification script (`scripts/verify_npm_integrity.py`)

- **Comprehensive Documentation** - 6 new documentation guides (3,500+ lines)
  - `docs/README.md`: Documentation index with navigation (374 lines)
  - `docs/usage-guide.md`: Complete command reference and workflows (490 lines)
  - `docs/attack-taxonomy.md`: 10x10 attack matrix explained (561 lines)
  - `docs/fix-orchestrator.md`: Automated remediation guide (663 lines)
  - `docs/github-integration.md`: CI/CD integration guide (781 lines)
  - `docs/jscpd-security.md`: npm security documentation (470 lines)

- **Fix Orchestrator** - Automated issue remediation
  - `/redteam-fix-orchestrator` command with interactive and GitHub modes
  - 6-stage execution pipeline: read → plan → red-team → apply → commit → validate
  - 7 specialized fix agents for parallel execution
  - Dependency analysis and conflict detection
  - Retry logic with validation feedback

- **PAL Integration Guidelines** - Best practices and test infrastructure
  - Complete PAL usage guide (`docs/pal-integration.md`)
  - Test fixtures for PAL mocking (`tests/fixtures/pal_mock.py`)
  - Audit results: 14 files with PAL, all with graceful degradation
  - Standard patterns for optional feature integration

- **Ultrathink Architecture Documentation** - Context isolation deep-dive
  - 5 core patterns: Firewall, Pipeline, Parallel, Branching, Retry
  - Context tiers with token budgets and real-world examples
  - Performance metrics: 96-98% context reduction
  - ROI calculation: $12,770 annual savings per 1000 workflows

- **Troubleshooting Guide** - Comprehensive debugging reference
  - PAL integration issues (detection, timeouts, enhancement)
  - Fix orchestration issues (validation, conflicts, commits)
  - Validation hook issues (blocking, triggering)
  - Context engineering issues (blowup, optimization)
  - Plugin configuration and test issues

### Changed

- **PR Analysis** - Now includes 5 parallel attackers (was 4)
  - Added `duplicate-code-analyzer` alongside existing 4 code attackers
  - Updated `pr-analysis-coordinator.md` with 5-attacker assignment
  - Risk category count: 11 (was 10)

- **Pydantic Models** - Extended for fix orchestration and jscpd
  - Added `CODE_DUPLICATION` to `RiskCategoryName` enum
  - New fix orchestration models in `src/red_agent/models/fix_orchestration.py`
  - 8 new models: FixReaderOutput, FixPlanV2Output, FixRedTeamerOutput, etc.
  - Centralized models extracted from inline definitions

- **Plugin Description** - Updated to reflect 11 risk categories
  - Changed from "10x10 attack taxonomy" to include code duplication
  - Added fix orchestrator capability to description

### Fixed

- **Input Validation** - Added comprehensive validation to duplicate-code-analyzer
  - File path safety (reject absolute paths, path traversal)
  - File size limits (10MB max to prevent resource exhaustion)
  - Execution timeout (60s for jscpd)
  - Output validation (verify JSON before parsing)

- **Pre-commit Hook Robustness** - Enhanced error handling in verify_npm_integrity.py
  - Try-catch for JSON parsing errors
  - Better error messages (show count, first few packages)
  - Graceful degradation for missing lock file
  - Informative success messages with package count

- **Documentation Clarity** - Implementation status vs. planned features
  - Added "Implementation Status" section to jscpd-security.md
  - Clearly marked implemented features (✅) vs. planned (⏳)
  - Distinguished current capabilities from enterprise-grade enhancements

### Technical Notes

jscpd Configuration:
```json
{
  "threshold": 5,
  "minLines": 5,
  "minTokens": 50,
  "ignore": ["**/.git", "**/node_modules", "**/__pycache__"],
  "format": ["python", "javascript", "typescript", "go", "rust"],
  "reporters": ["json"],
  "output": ".jscpd-report.json"
}
```

Duplication Severity Mapping:
- CRITICAL: 50+ duplicate lines (mass copy-paste)
- HIGH: 20-49 lines (significant duplication)
- MEDIUM: 10-19 lines (moderate duplication)
- LOW: 5-9 lines (minor duplication)

Security Layers:
1. Version pinning (exact versions in package.json)
2. Integrity hashing (SHA-512 in package-lock.json)
3. Pre-commit validation (npm audit + integrity check)
4. CI validation (GitHub Actions workflow)

Red-Team Self-Check:
- Ran red-team analysis on this PR itself
- Addressed 3 critical and 3 high-priority findings
- Result: All 312 tests passing, all pre-commit hooks passing

## [1.3.0] - 2026-01-03

### Added

- **PR Red-Team Analysis** - Apply adversarial testing to pull request code changes
  - 4 git operation modes: `/redteam-pr:staged`, `:working`, `:diff`, `:branch`
  - All 10 rainbow-teaming categories now applied to code changes
  - 4 code attackers running in parallel: reasoning, context, security, scope
  - PR-specific report format with file grouping, breaking changes, test coverage analysis

- **User Scoping for Large PRs** - Interactive filtering for PRs with 15+ files
  - Analyze all files (may take 2-5 minutes for massive PRs)
  - High-risk files only (risk_score > 0.7) - recommended
  - Specific files/directories via glob patterns
  - By commit (branch mode only)

- **Cascading Coordination** - Parallel batch processing for massive PRs (50+ files)
  - Splits files into batches of 20
  - Launches up to 4 sub-coordinators in parallel (16 total attackers)
  - 4x speedup for massive PRs through intelligent parallelization

- **Optional PAL Integration** - Enhanced analysis with PAL MCP when available
  - diff-analyzer: PAL challenges risk assessments
  - security-prober: PAL deepthink for CRITICAL/HIGH findings
  - pr-analysis-coordinator: PAL challenges CRITICAL findings in deep mode
  - Graceful degradation when PAL unavailable

- **Comprehensive Test Suite** - 48 new tests for PR analysis (308 total)
  - Pydantic model validation: DiffMetadata, FileRef, CodeAttackerOutput, PRRedTeamReport
  - Validation function tests: validate_diff_analysis, validate_code_attacker, validate_pr_report
  - Finding ID format, risk score constraints, severity levels

### Changed

- **Context Management** - 85% token reduction for PR analysis
  - SELECTIVE context tier for diff parsing (2K tokens vs 10K naive)
  - FILTERED context per attacker (1K tokens vs 5K per attacker)
  - METADATA only to synthesizer (1.2K tokens vs 20K)
  - Total: ~10K tokens vs ~85K naive approach

- **Validation Infrastructure** - Extended for PR analysis outputs
  - 17 new Pydantic models in `pr_analysis.py`
  - Enhanced validation with PR-specific warning functions
  - Complete nested structure validation for diff analysis and code findings

- **Documentation** - Added comprehensive PR Analysis section to README
  - Usage examples for all 4 commands
  - Mode options and user scoping behavior
  - Performance characteristics table
  - Example workflows (pre-commit review, feature branch review, CI/CD integration)

### Technical Notes

PR Analysis Architecture (5-phase pipeline):
```
Command → Git Discovery → pr-analysis-coordinator (FIREWALL)
  ├─ Phase 1: Diff Analysis (SELECTIVE) → diff-analyzer
  ├─ Phase 2: Strategy (MINIMAL) → attack-strategist
  ├─ Phase 3: Code Attack (FILTERED, PARALLEL) → 4 code attackers
  ├─ Phase 4: Grounding (BATCHED) → existing grounding agents
  └─ Phase 5: Synthesis (METADATA) → pr-insight-synthesizer
```

Performance targets by PR size:
```
Tiny (1-2 files):     4 agents,  10s target
Small (2-5 files):    4 agents,  20s target
Medium (5-15 files):  4 agents,  60s target
Large (15-50 files):  8 agents, 120s target
Massive (50+ files): 16 agents, 300s target (5 min)
```

Code attacker categories:
- code-reasoning-attacker: logic-errors, assumption-gaps, edge-case-handling
- code-context-attacker: breaking-changes, dependency-violations, api-contract-changes
- security-prober: security-vulnerabilities, input-validation, information-disclosure
- change-scope-analyzer: scope-creep, unintended-side-effects, test-coverage-gaps

## [1.2.1] - 2026-01-02

### Added

- **Multi-Agent Collaboration Skill** - Extracted SOTA patterns into reusable skill
  - Four Laws of Context Management: selective projection, tiered fidelity, reference vs embedding, lazy loading
  - Architectural pattern reference: hierarchical, swarm, ReAct, plan-execute, reflection
  - Red-agent implementation examples demonstrating 84% context reduction

### Changed

- Consolidated `docs/CONTEXT_MANAGEMENT.md` into skill's progressive disclosure structure
- Updated 12 sub-agent files to reference skill location

### Technical Notes

Context engineering patterns now follow three-level progressive disclosure:
- L1 (~100 tokens): Skill metadata always loaded
- L2 (~2000 tokens): Core patterns loaded on trigger
- L3 (on-demand): Deep references loaded as needed

## [1.2.0] - 2026-01-02

### Added

- **`/redteam-w-fix` Command** - Interactive fix selection workflow with `AskUserQuestion` integration
- **PAL MCP Availability Checker** - Graceful degradation when MCP servers unavailable
- **Pre-push Validation** - `claude plugin validate` integration for authoritative schema checks
- Finding conciseness guidelines enforcing field length limits

### Changed

- **Context Management Overhaul** - Implemented tiered fidelity architecture
  - FULL → MINIMAL → SELECTIVE → FILTERED → METADATA
  - Severity-based grounding batches: 60-70% operation reduction
  - Result: 78% total context reduction (315KB → 55KB)

### Fixed

- Duplicate hook loading from explicit `hooks` reference
- Ruff lint violations in `validate_against_claude_code.py`

### Technical Notes

Grounding batch routing by severity:
```
CRITICAL → 4 agents | HIGH → 2 agents | MEDIUM → 1 agent | LOW/INFO → skip
```

## [1.1.0] - 2025-12-15

### Added

- **PostToolUse Hook** - Auto-validation of sub-agent outputs with retry logic
- **CI Pipeline** - GitHub Actions workflow for automated validation
- CLI interface for `validate_agent_output.py`

### Changed

- Migrated to `src/` layout for proper Python packaging
- Restructured `agents` field in plugin.json to array format

### Fixed

- Removed `_schema_note` fields rejected by Claude Code's strict schema validation

### Technical Notes

Validation hook implements block-and-retry pattern:
- Pydantic models validate YAML output structure
- Invalid output triggers re-prompt with error context
- Maximum 2 retries before escalation

## [1.0.0] - 2025-12-01

### Added

- **Red-Agent Plugin** - Adversarial analysis using Rainbow Teaming methodology
- **`/redteam` Command** - Entry point for red team analysis
- **10×10 Attack Taxonomy** - 10 risk categories × 10 attack styles
- **Pydantic Validation Models** - Type-safe agent output validation
- JSON schemas for plugin and marketplace manifests
- Pre-commit hooks: schema validation, config hygiene, agent file existence

### Technical Notes

Architecture follows firewall pattern:
```
Main Session → red-team-coordinator (isolation boundary)
                    ├── context-analyzer
                    ├── attack-strategist
                    ├── attackers (4 parallel)
                    ├── grounding (4, severity-batched)
                    └── insight-synthesizer
```

Risk categories: reasoning-flaws, assumption-gaps, context-manipulation, authority-exploitation, information-leakage, hallucination-risks, over-confidence, scope-creep, dependency-blindness, temporal-inconsistency

---

[Unreleased]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/releases/tag/v1.0.0
