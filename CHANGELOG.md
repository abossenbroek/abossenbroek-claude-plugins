# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2026-01-02

### Added
- Multi-agent collaboration skill with SOTA context management patterns
  - `SKILL.md`: Core skill with Four Laws of Context Management
  - `references/context-engineering.md`: Detailed context patterns
  - `references/patterns.md`: Architectural patterns (hierarchical, swarm, ReAct, etc.)
  - `references/examples.md`: Red-agent implementation examples

### Changed
- Consolidated `docs/CONTEXT_MANAGEMENT.md` into the new skill
- Updated 12 agent files to reference new skill location
- Removed redundant inline references where key limits already present

## [1.2.0] - 2026-01-02

### Added
- `/redteam-w-fix` command with interactive fix selection workflow
- PAL MCP availability detection for graceful degradation
- AskUserQuestion schema validation for fix-coordinator outputs
- Claude Code schema validation pre-push hook (`claude plugin validate`)
- Finding conciseness guidelines for attacker agents

### Changed
- Implemented SOTA context management achieving 78%+ context reduction
- Tiered context fidelity: FULL -> MINIMAL -> SELECTIVE -> FILTERED -> METADATA
- Severity-based grounding batches reducing operations by 60-70%

### Fixed
- Removed explicit hooks reference to fix duplicate loading
- Fixed ruff lint errors in validate_against_claude_code.py

## [1.1.0] - 2025-12-15

### Added
- CI workflow with GitHub Actions
- Enhanced validation scripts
- PostToolUse hook with auto-correct validation
- CLI tests for validation tools

### Changed
- Migrated to src layout for Python packages
- Improved agents field format in plugin.json

### Fixed
- Removed `_schema_note` fields rejected by Claude Code

## [1.0.0] - 2025-12-01

### Added
- Initial release of red-agent plugin
- `/redteam` command for adversarial analysis
- 10x10 attack taxonomy (Rainbow Teaming methodology)
- Comprehensive Pydantic models for agent output validation
- Pre-commit hooks for schema validation
- Root CLAUDE.md with project guidelines

### Added (Infrastructure)
- JSON schemas for plugin and marketplace validation
- Unit tests for all validators
- Ruff configuration for code quality

[Unreleased]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/releases/tag/v1.0.0
