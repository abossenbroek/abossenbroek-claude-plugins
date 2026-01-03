# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/abossenbroek/abossenbroek-claude-plugins/releases/tag/v1.0.0
