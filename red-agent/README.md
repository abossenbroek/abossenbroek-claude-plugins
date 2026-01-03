# Red Agent - Adversarial Red Team Analysis for Claude Code

A standalone Claude Code plugin that applies adversarial red/rainbow team analysis to find weaknesses in LLM interactions.

## Overview

Red Agent provides `/redteam` - a contrarian agent that systematically probes conversations and code for vulnerabilities using a 10x10 attack taxonomy derived from state-of-the-art LLM red-teaming research.

### Key Features

- **Rainbow Teaming**: 10 risk categories × 10 attack styles = comprehensive coverage
- **Context Isolation**: All adversarial work happens in isolated agent contexts
- **Grounded Findings**: Independent verification layer prevents false positives
- **Actionable Reports**: Clear recommendations with confidence scores

## Installation

### Requirements

- Claude Code CLI installed
- [uv](https://docs.astral.sh/uv/) (Python package manager) - required for validation hooks

### Steps

1. Clone or copy the `red-agent` directory to your project or Claude Code plugins location
2. The plugin will be automatically detected by Claude Code
3. Validation hooks run automatically via `uv` (no manual setup needed)

The plugin includes a PostToolUse hook that validates agent outputs using Pydantic models. The hook uses `uv run --script` with inline dependencies, so validation "just works" without manual dependency installation.

## Usage

```bash
# Standard analysis of current conversation
/redteam

# Quick surface-level analysis (2-3 vectors, no grounding)
/redteam quick

# Deep comprehensive analysis (all vectors, full grounding)
/redteam deep

# Focus on specific category
/redteam focus:reasoning-flaws

# Analyze a specific file
/redteam standard file:src/auth.py

# Analyze recent git changes
/redteam code
```

## Modes

| Mode | Vectors | Grounding | Use Case |
|------|---------|-----------|----------|
| `quick` | 2-3 | Skip | Fast sanity check |
| `standard` | 5-6 | Basic | Balanced analysis (default) |
| `deep` | All 10 | Full | Comprehensive review |
| `focus:X` | All for X | Full | Deep dive on one area |

## Risk Categories

1. **reasoning-flaws** - Logic gaps, invalid inferences
2. **assumption-gaps** - Hidden premises, unstated constraints
3. **context-manipulation** - Poisoned context, prompt injection
4. **authority-exploitation** - Role confusion, credential misuse
5. **information-leakage** - Unintended disclosure
6. **hallucination-risks** - Fabricated facts, confident errors
7. **over-confidence** - Unjustified certainty
8. **scope-creep** - Actions beyond request
9. **dependency-blindness** - Unverified external data
10. **temporal-inconsistency** - Stale info, version conflicts

## Architecture

```
/redteam command
    │
    ▼
┌─────────────────────────────┐
│   red-team-coordinator      │  ← FIREWALL (isolated from main)
│   (thin router)             │
├─────────────────────────────┤
│  ┌────────────────────────┐ │
│  │ Phase 1: Analyze       │ │  context-analyzer
│  │ Phase 2: Strategize    │ │  attack-strategist
│  │ Phase 3: Attack        │ │  4 attacker agents (parallel)
│  │ Phase 4: Ground        │ │  4 grounding agents (parallel)
│  │ Phase 5: Synthesize    │ │  insight-synthesizer
│  └────────────────────────┘ │
└─────────────────────────────┘
    │
    ▼
Sanitized Markdown Report
```

## Output

The plugin produces a markdown report including:

- **Executive Summary**: Critical findings and overall risk level
- **Risk Heat Map**: Category-by-category severity overview
- **Findings**: Detailed issues with evidence, probing questions, and recommendations
- **Grounding Notes**: Evidence strength and alternative interpretations
- **Patterns**: Cross-cutting systemic observations
- **Recommendations**: Prioritized action items
- **Limitations**: Transparency about analysis scope and confidence

### Sample Finding

```markdown
### [RF-001] Invalid Inference in Auth Flow
- **Category**: reasoning-flaws
- **Severity**: HIGH
- **Confidence**: 72% (adjusted from 85%)

**Evidence**: > "Step 3 assumes the API returns JSON..."

**Probing Question**: "What if the API returns non-JSON in error cases?"

**Recommendation**: Add content-type validation before parsing

**Grounding Notes**:
- Evidence: Strong (0.8/1.0) - direct quote from response
- Alternative: Could be intentional for backward compatibility
- Status: GROUNDED
```

## File Structure

```
red-agent/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── hooks/
│   ├── hooks.json            # Hook configuration
│   └── validate-agent-output.py  # PostToolUse validation script
├── commands/
│   └── redteam.md            # Command entry point
├── agents/
│   └── red-team-coordinator.md   # Main coordinator (firewall)
├── coordinator-internal/
│   ├── context-analyzer.md   # Analyzes conversation snapshot
│   ├── attack-strategist.md  # Selects attack vectors
│   ├── reasoning-attacker.md # Logic/assumption attacks
│   ├── context-attacker.md   # Authority/role/temporal attacks
│   ├── hallucination-prober.md   # Confidence/source attacks
│   ├── scope-analyzer.md     # Scope/dependency attacks
│   ├── insight-synthesizer.md    # Report generation
│   └── grounding/
│       ├── evidence-checker.md   # Verifies evidence
│       ├── proportion-checker.md # Checks severity
│       ├── alternative-explorer.md   # Explores alternatives
│       └── calibrator.md     # Calibrates confidence
├── skills/
│   └── rainbow-teaming/
│       └── SKILL.md          # Methodology reference
├── CLAUDE.md                 # Project instructions
└── README.md                 # This file
```

## Design Principles

### Context Isolation

All adversarial work happens in isolated agent contexts to prevent:
- Attack prompts entering main session
- "I attacked X" reasoning polluting context
- Intermediate findings confusing users

Only the final sanitized report returns to the main session.

### Grounding Layer

Findings are verified before reporting:
- **Evidence Checker**: Validates quoted evidence exists and is accurate
- **Proportion Checker**: Ensures severity matches actual impact
- **Alternative Explorer**: Generates counterarguments and alternatives
- **Calibrator**: Synthesizes into final confidence scores

This prevents manufactured findings and ensures proportionate reporting.

### Automatic Validation with Auto-Correct

A PostToolUse hook validates all sub-agent outputs in real-time. Invalid outputs are automatically corrected:

```
Agent produces YAML output
        ↓
PostToolUse hook validates
        ↓
┌─────────────────────────────┐
│ Valid: Passes silently      │
│ Invalid: Blocks + retries   │
└─────────────────────────────┘
        ↓
Coordinator retries with error context
        ↓
User sees only valid final output
```

**How auto-correct works:**
1. Hook detects YAML parse errors or schema violations
2. Hook blocks the output with specific error details
3. Coordinator automatically retries the sub-agent
4. Process repeats until valid (max 2 retries)

Validated output types:
- **attacker** - Findings from attack agents
- **grounding** - Evidence verification results
- **context** - Context analysis output
- **strategy** - Attack strategy selection
- **report** - Final synthesized report

## Research Foundation

- [Rainbow Teaming](https://arxiv.org/abs/2402.16822) - Quality-diversity for adversarial prompts
- [LLM Red-Team Survey](https://arxiv.org/html/2410.09097v1) - Comprehensive attack taxonomy
- Multi-turn attack techniques (Crescendo, many-shot, adaptive)
- Reasoning exploitation patterns

## Contributing

Contributions welcome! Areas of interest:
- Additional risk categories
- New attack styles
- Improved grounding heuristics
- Integration with external verification tools

## PR Analysis Commands

Red Agent includes specialized commands for analyzing pull requests and git diffs directly.

### Available Commands

| Command | Description |
|---------|-------------|
| `/redteam-pr:staged` | Analyze staged changes (`git diff --cached`) |
| `/redteam-pr:working` | Analyze working directory changes (`git diff`) |
| `/redteam-pr:diff <file>` | Analyze a specific diff file |
| `/redteam-pr:branch <base>` | Analyze branch changes against base (default: main) |

### Usage Examples

```bash
# Analyze staged changes before committing
/redteam-pr:staged

# Quick analysis of working directory changes
/redteam-pr:working quick

# Deep analysis of a specific diff file
/redteam-pr:diff ./changes.diff deep

# Analyze feature branch against main
/redteam-pr:branch main

# Focus on specific risk category
/redteam-pr:staged focus:reasoning-flaws
```

### Mode Options

All PR analysis commands support the same modes as `/redteam`:

| Mode | Description |
|------|-------------|
| `quick` | Fast surface-level analysis (2-3 vectors, no grounding) |
| `standard` | Balanced analysis (default) |
| `deep` | Comprehensive review (all vectors, full grounding) |
| `focus:X` | Deep dive on specific category |

### User Scoping for Large PRs

For PRs with many files, the commands automatically scope the analysis:

1. **File Risk Scoring**: Each file is assigned a risk score (0.0-1.0) based on:
   - File type (security-sensitive files score higher)
   - Change patterns (authentication, validation changes)
   - Size of changes

2. **User Scoping**: For large PRs (15+ files), users may be asked to select focus areas:
   - High-risk files are pre-selected
   - Users can add/remove files from analysis scope
   - Ensures analysis stays focused and efficient

### Cascading Support for Massive PRs

For PRs with 50+ files or 2000+ lines changed:

1. **Automatic Parallelization**: Files are grouped into batches
2. **8-16 Parallel Agents**: Multiple code-reasoning-attacker agents analyze batches concurrently
3. **Result Aggregation**: Findings are merged and deduplicated
4. **Pattern Detection**: Cross-file patterns are identified across all batches

### PAL Integration (Optional)

PR analysis supports optional PAL (Prompt-Agent-Loop) enhancement:

- Structured prompt patterns for consistent analysis
- Agent orchestration for complex multi-file PRs
- Loop detection to prevent analysis cycles

### Performance Characteristics

| PR Size | Files | Lines Changed | Agents | Target Time |
|---------|-------|---------------|--------|-------------|
| Tiny | 1-2 | 1-10 | 4 | 10s |
| Small | 2-5 | 10-100 | 4 | 20s |
| Medium | 5-15 | 100-500 | 4 | 60s |
| Large | 15-50 | 500-2000 | 8 | 120s |
| Massive | 50+ | 2000+ | 16 | 300s (5 min) |

### Example Workflows

#### Pre-Commit Review

```bash
# Stage your changes
git add -A

# Run analysis on staged changes
/redteam-pr:staged

# Review findings and fix issues before committing
```

#### Feature Branch Review

```bash
# Switch to feature branch
git checkout feature/new-auth

# Analyze all changes against main
/redteam-pr:branch main deep

# Address findings before creating PR
```

#### CI/CD Integration

```bash
# In CI pipeline, analyze the PR diff
/redteam-pr:diff $PR_DIFF_FILE standard

# Fail pipeline if CRITICAL or HIGH findings
```

### Output Format

PR analysis produces a structured report including:

- **PR Summary**: File counts, additions/deletions, risk classification
- **Risk Level**: Overall CRITICAL/HIGH/MEDIUM/LOW/INFO assessment
- **Findings**: Issues organized by file and severity
- **Breaking Changes**: API changes that may affect consumers
- **Recommendations**: Prioritized action items
- **Test Coverage Notes**: Comments on test changes

### Sample Output

```markdown
## PR Red Team Analysis Report

### Executive Summary
This PR introduces authentication changes with moderate risk...

### PR Summary
- Files Changed: 5
- Additions: 150 / Deletions: 30
- PR Size: Medium
- High Risk Files: src/auth/handler.ts

### Risk Level: HIGH

### Findings

#### [PR-001] Missing Input Validation
- **Severity**: HIGH
- **File**: src/auth/handler.ts (lines 45-52)
- **Confidence**: 85%

**Description**: User input is not validated...

**Recommendation**: Add input validation using...

### Breaking Changes
- API signature change in authenticate()...

### Recommendations
1. Add comprehensive input validation
2. Implement proper error handling
3. Add unit tests for edge cases
```

## License

MIT
