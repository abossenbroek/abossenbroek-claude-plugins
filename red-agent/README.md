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

1. Clone or copy the `red-agent` directory to your project or Claude Code plugins location
2. The plugin will be automatically detected by Claude Code

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

## License

MIT
