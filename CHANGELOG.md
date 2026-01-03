# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - Both Plugins

- **Validation Hook Standardization** - Unified PostToolUse hook behavior across red-agent and context-engineering
  - YAML output format: `decision: continue` or `decision: block` with multiline `reason`
  - Replaced JSON format (red-agent) and exit codes (context-engineering)
  - Error formatter with actionable hints (missing fields, enum violations, range errors)
  - Single source of truth: Import Pydantic models from `src/` (removed 179 lines of inline duplication)

### Added - Red Agent

- **Output Validation Documentation** - Added comprehensive validation section to red-agent/CLAUDE.md
  - YAML format examples
  - Text-based agent detection method
  - Validation failure examples with hints

### Added - Context Engineering

- **Enhanced Validation Documentation** - Updated validation section in context-engineering/CLAUDE.md
  - Model types reference (Analysis, Improvements, Grounding, Synthesis)
  - Structure-based agent detection method
  - Validation failure examples

### Added - Repository

- **PostToolUse Hook Standards** - Established standards for all future plugins
  - Output format specification (YAML with decision/reason)
  - Error message formatter template
  - Model import pattern (never duplicate)
  - Testing requirements (format, retry flow, error parsing)

- **Multi-Agent Orchestration Patterns** - Documentation for complex multi-phase tasks
  - Orchestrator → Phase Agents → File Agents hierarchy
  - Parallelization strategies and dependency management
  - Permission handling with settings.local.json checking
  - Example structures and decision trees

- **42 Comprehensive Tests** - Validation hook behavior test suite
  - `test_hook_output_format.py` - YAML format validation (17 tests)
  - `test_hook_retry_flow.py` - Retry behavior validation (9 tests)
  - `test_error_message_parsing.py` - Error message quality (16 tests)
  - Updated conftest.py with 3 new fixtures

### Documentation

- **Enhanced Pre-commit Workflow** - Auto-fix guidance and common issue reference
  - Common auto-fixable issues (F401, COM812, I001, W291, W293)
  - Manual fix requirements (E501, PLR0912, C901, ANN)
  - Step-by-step workflow (identify → auto-fix → manual → verify)

- **Phase-Based Planning Framework** - Decision framework for agent orchestration
  - When to use orchestrator pattern (5+ files, dependencies, parallelization)
  - Example decision trees for common scenarios
  - Pattern diagrams and execution strategies

### Technical Notes

**Validation Improvements:**
- Net reduction: 163 lines (45% smaller red-agent hook file)
- Test coverage: 42 new tests, 302 total (100% pass rate)
- Execution: 21-agent orchestration with parallelization (~12 minutes)

**Benefits:**
- Single source of truth eliminates model duplication
- Consistent YAML format improves LLM parseability
- Actionable hints improve agent retry success rate
- Comprehensive tests validate hook behavior and recovery flows

## [1.3.0] - 2026-01-02

### Added - Context Engineering Plugin

- **HO-001: Shared State System** - File-based state management with fcntl locking
  - Pydantic models: FocusArea, AnalysisMode, FileRef, ImmutableState, MutableState, ContextEngineeringState
  - `state_manager.py` CLI with init, read, update, lock, unlock commands
  - YAML persistence in `.context-engineering-state.yaml`

- **FW-002: File Cache** - Lazy loading system for context reduction
  - `file_cache.py` CLI with discover, fetch, refs commands
  - MD5-based file IDs (8 chars), token estimation (chars/4)
  - Reduces context pollution by loading files on-demand

- **AG-001: Python Validation Hook** - Type-safe output validation
  - Replaced prompt-based validation with Python script
  - Maps 12 agent types to Pydantic models
  - Detailed error messages with exit codes

- **OR-002: Challenger Agent** - Claim validation for HIGH priority improvements
  - ChallengeValidity enum: SUPPORTED/UNSUPPORTED/UNCERTAIN
  - Evidence strength scoring (0.0-1.0)
  - 1 round maximum per improvement

### Changed

- **OR-001: Phase Executor Architecture** - Refactored coordinator from 312 to 141 lines
  - 5 dedicated phase executors: analyze, improve, categorize, ground, synthesize
  - Context tier progression: MINIMAL → SELECTIVE → FILTERED → METADATA
  - Result: 97% context reduction through tiered fidelity

- **FW-001: I/O Phase Separation** - Strict separation of file I/O from analysis
  - `file-discovery-executor`: ONLY agent with Glob/Read permissions
  - `analysis-executor`: Pure analysis, cache-only access
  - Enforces clean architectural boundaries

- **CM-001: Focus-Based Filtering** - Targeted file distribution to improvers
  - Focus patterns: context, orchestration, handoff
  - Result: 42% reduction in context duplication (138 → 81 file refs)

### Documentation

- **CM-002: NOT PROVIDED Sections** - Explicit context isolation documentation
  - Added to all 13 coordinator-internal agents
  - Documents 5-8 exclusions per agent (session history, other plugins, user info, etc.)
  - Enforces firewall architecture transparency

### Technical Notes

**Architecture Achievements:**
- Firewall architecture: Thin coordinator delegates to specialized phase executors
- Grounding efficiency: 52% reduction via severity batching (40 → 19 operations)
- Type safety: 100% validation coverage using Pydantic models
- Test coverage: 95 new tests, 260 total (100% pass rate)

**Context Reduction Breakdown:**
```
Phase 1 (Analyze):    MINIMAL    ~100-500 tokens (plugin_path only)
Phase 2 (Improve):    SELECTIVE  ~1-5K tokens (filtered analysis)
Phase 3 (Categorize): MINIMAL    ~100-500 tokens (IDs only)
Phase 4 (Ground):     FILTERED   ~500-2K tokens (categorized)
Phase 6 (Synthesize): METADATA   ~50-200 tokens (selected only)
```

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
