# Red Agent - Claude Code Red Team Plugin

## Purpose

This plugin provides `/redteam` - a contrarian agent that applies adversarial red/rainbow team analysis to find weaknesses in LLM interactions.

## Critical Architecture Rules

### Context Isolation (MUST FOLLOW)

1. **FIREWALL PATTERN**: Only the `red-team-coordinator` agent is launched from main session
2. **NO POLLUTION**: Adversarial work, attack prompts, and intermediate reasoning NEVER enter main context
3. **STRUCTURED DATA ONLY**: Pass context snapshots (YAML), not raw conversation
4. **SANITIZED OUTPUT**: Only the final markdown report returns to user

### Agent Hierarchy

```
Main Session
    └── red-team-coordinator (FIREWALL - only entry point)
            ├── context-analyzer
            ├── attack-strategist
            ├── reasoning-attacker
            ├── context-attacker
            ├── hallucination-prober
            ├── scope-analyzer
            ├── grounding/evidence-checker
            ├── grounding/proportion-checker
            ├── grounding/alternative-explorer
            ├── grounding/calibrator
            └── insight-synthesizer
```

## File Locations

- Commands: `commands/redteam.md`
- Main Agent: `agents/red-team-coordinator.md`
- Sub-Agents: `coordinator-internal/*.md`
- Grounding: `coordinator-internal/grounding/*.md`
- Reference: `skills/rainbow-teaming/SKILL.md`

## Modes

- `quick` - 2-3 vectors, skip grounding
- `standard` - 5-6 vectors, basic grounding (default)
- `deep` - All vectors, full grounding + meta-analysis
- `focus:[category]` - Deep dive on one category

## Risk Categories

1. reasoning-flaws
2. assumption-gaps
3. context-manipulation
4. authority-exploitation
5. information-leakage
6. hallucination-risks
7. over-confidence
8. scope-creep
9. dependency-blindness
10. temporal-inconsistency

## Key Principles

- Stateless: Analyzes current context only
- Self-contained: No external MCP dependencies
- Grounded: Findings verified with evidence scores
- Transparent: Reports include confidence levels and limitations

## Output Validation

PostToolUse hooks validate sub-agent outputs against Pydantic models:
- **Format**: YAML with `decision: continue` or `decision: block` + `reason`
- **Models**: Imported from `src/red_agent/models/` (single source of truth)
- **Agent Detection**: Text-based (searches prompt/description for agent names)
- **Retry**: No enforced limit - coordinators decide strategy

### Validation Failure Example

```yaml
decision: block
reason: |
  Validation failed for reasoning-attacker output:
  - findings.0.id: ID must match pattern XX-NNN or XXX-NNN, got: invalid-format
    Hint: Check the format and regenerate
  Please fix these fields and regenerate the output.
```
