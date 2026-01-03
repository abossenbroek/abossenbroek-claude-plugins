# Context Engineering Plugin

Production-grade context engineering tool for expert LLM engineers. Analyzes and improves Claude Code plugins using SOTA orchestration patterns.

## Features

- **Plugin Analysis**: Deep structural analysis of Claude Code plugins
- **Context Optimization**: Apply Four Laws of Context Management
- **Orchestration Improvement**: Firewall architecture, phase-based execution
- **Handoff Generation**: YAML schemas, Pydantic models, validation hooks
- **Plan Optimization**: Optimize execution plans for context efficiency

## Installation

Add to your Claude Code plugins:

```bash
claude plugin add https://github.com/abossenbroek/abossenbroek-claude-plugins/context-engineering
```

## Commands

### /improve-plugin

Improve an existing plugin with SOTA patterns.

```bash
/improve-plugin              # Full improvement pass
/improve-plugin context      # Focus on context management
/improve-plugin orchestration # Focus on agent hierarchy
/improve-plugin handoff      # Focus on agent communication
```

### /optimize-plan

Optimize a plan file for efficient context flows.

```bash
/optimize-plan                           # Most recent plan
/optimize-plan ~/.claude/plans/plan.md   # Specific plan
```

### /audit-context

Audit for context management inefficiencies.

```bash
/audit-context          # Auto-detect plugin
/audit-context ./plugin # Specific plugin
```

### /generate-handoffs

Generate handoff schemas and validation models.

```bash
/generate-handoffs                    # All agents
/generate-handoffs agent1,agent2      # Specific agents
```

## Architecture

### Agent Hierarchy (14 agents)

```
Entry Coordinators (3)
├── improve-coordinator
├── plan-coordinator
└── audit-coordinator

Coordinator-Internal (11)
├── Analyzers (3)
│   ├── plugin-analyzer
│   ├── plan-analyzer
│   └── context-flow-mapper
├── Improvers (3)
│   ├── context-optimizer
│   ├── orchestration-improver
│   └── handoff-improver
├── Grounding (4)
│   ├── pattern-checker
│   ├── token-estimator
│   ├── consistency-checker
│   └── risk-assessor
└── Synthesizers (1)
    └── improvement-synthesizer
```

### Phase-Based Execution

```
Phase 1: Analyze    (FULL context)
Phase 2: Improve    (SELECTIVE context)
Phase 3: Ground     (FILTERED context, severity-batched)
Phase 4: Select     (User chooses improvements)
Phase 5: Synthesize (METADATA context)
```

### The Four Laws

| Law | Principle |
|-----|-----------|
| 1. Selective Projection | Pass only needed fields |
| 2. Tiered Fidelity | FULL → SELECTIVE → MINIMAL |
| 3. Reference vs Embedding | Use references for large data |
| 4. Lazy Loading | Load on-demand, not upfront |

## Skills

### Context Engineering

Loaded when: "context optimization", "reduce tokens", "Four Laws"

Provides:
- Four Laws quick reference
- Context tier definitions
- Anti-patterns checklist
- Handoff protocol templates

### Orchestration Patterns

Loaded when: "firewall architecture", "phase execution", "severity batching"

Provides:
- Pattern selection framework
- Firewall architecture guide
- Phase execution templates
- Validation hook patterns

## Output Validation

All sub-agent outputs are validated against Pydantic models via PostToolUse hooks.

Models defined in `src/context_engineering/models/`:
- `analysis_outputs.py` - PluginAnalysis, ContextFlowMap
- `improvement_outputs.py` - ContextImprovement, OrchestrationImprovement, HandoffImprovement
- `grounding_outputs.py` - PatternCompliance, TokenEstimate, RiskAssessment
- `synthesis_outputs.py` - ImprovementReport

## Templates

Production-ready templates in `templates/`:
- `coordinator-agent.md` - Entry agent template
- `sub-agent.md` - Coordinator-internal agent template
- `handoff-schema.yaml` - Handoff specification template
- `pydantic-model.py` - Validation model template
- `hooks-config.json` - Hook configuration template

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/test_context_engineering_*.py -v

# Validate manually
python scripts/validate_improvement_output.py < output.yaml
```

## License

MIT
