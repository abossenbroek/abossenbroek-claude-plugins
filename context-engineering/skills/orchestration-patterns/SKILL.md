---
name: Orchestration Patterns
description: >
  This skill should be used when designing agent orchestration, implementing
  firewall architecture, creating phase-based workflows, adding severity
  batching, structuring agent hierarchies, or implementing SOTA multi-agent
  coordination patterns. Provides production-ready patterns for scalable
  agent systems.
---

# Orchestration Patterns

## Overview

State-of-the-art patterns for multi-agent system orchestration. These patterns enable complex workflows while maintaining clear boundaries, efficient context flow, and debuggable execution.

## Pattern Selection Framework

| Pattern | Use When | Trade-offs |
|---------|----------|------------|
| **Firewall** | Context isolation critical | Coordination overhead |
| **Hierarchical** | Clear decomposition needed | Sequential bottleneck |
| **Phase-Based** | Distinct execution stages | Rigid structure |
| **Severity Batching** | Variable priority items | Complexity in routing |
| **Swarm** | Parallel exploration | Coordination overhead |
| **Hybrid** | Multiple needs | Implementation complexity |

For detailed pattern definitions, see `references/firewall-architecture.md`.

## Firewall Architecture

The foundational pattern for context-isolated multi-agent systems.

### Core Concept

```
Main Session (CLEAN)
       │
       ▼
   ┌───────────────────┐
   │  FIREWALL         │
   │  Entry Agent      │  ← Only entry point
   │  (Thin Router)    │
   └───────────────────┘
       │
       ▼
   ┌───────────────────┐
   │  ISOLATED WORK    │
   │  Sub-Agents       │  ← Work happens here
   │  (coordinator-    │
   │   internal/)      │
   └───────────────────┘
       │
       ▼
   ┌───────────────────┐
   │  SANITIZED OUTPUT │
   │  Final Report     │  ← Only this returns
   └───────────────────┘
```

### Key Rules

1. **Entry agents are THIN ROUTERS** - They route, not analyze
2. **Work in isolation** - Sub-agents do the actual work
3. **Structured data only** - No raw context passes through
4. **Sanitized return** - Only final report reaches main session

For implementation details, see `references/firewall-architecture.md`.

## Phase-Based Execution

Workflow structure with clear stages:

```yaml
phases:
  analyze:
    tier: FULL
    agents: [analyzer]
    output: analysis_results

  improve:
    tier: SELECTIVE
    agents: [optimizer, improver]
    input: analysis_summary
    output: improvements

  ground:
    tier: FILTERED
    agents: [checkers, validators]
    input: improvements_by_priority
    output: grounded_improvements

  synthesize:
    tier: METADATA
    agents: [synthesizer]
    input: selected_improvements
    output: final_report
```

For phase design guidance, see `references/phase-execution.md`.

## Severity-Based Batching

Route items by priority to reduce operations:

```yaml
routing:
  CRITICAL:
    validators: [all]          # 4 agents
    operations: ~16            # 4 findings × 4 validators

  HIGH:
    validators: [primary, secondary]  # 2 agents
    operations: ~10            # 5 findings × 2 validators

  MEDIUM:
    validators: [primary]      # 1 agent
    operations: ~8             # 8 findings × 1 validator

  LOW/INFO:
    validators: []             # Skip
    operations: 0

# Total: 34 operations vs 108 (all × all)
# Reduction: 68%
```

For batching strategies, see `references/severity-batching.md`.

## Agent Hierarchy Patterns

### Entry + Internal Structure

```
plugin/
├── agents/                    # ENTRY AGENTS (user-invocable)
│   ├── coordinator-a.md       # Firewall for workflow A
│   └── coordinator-b.md       # Firewall for workflow B
│
└── coordinator-internal/      # SUB-AGENTS (never directly invoked)
    ├── analyzer.md
    ├── processor.md
    ├── grounding/
    │   ├── checker-1.md
    │   └── checker-2.md
    └── synthesizer.md
```

### Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Entry/Firewall | `*-coordinator.md` | `improve-coordinator.md` |
| Analyzer | `*-analyzer.md` | `plugin-analyzer.md` |
| Worker | `*-optimizer.md`, `*-improver.md` | `context-optimizer.md` |
| Grounding | `grounding/*.md` | `grounding/pattern-checker.md` |
| Synthesizer | `*-synthesizer.md` | `improvement-synthesizer.md` |

## Validation with Hooks

### PostToolUse Pattern

```json
{
  "event": "PostToolUse",
  "matcher": {
    "tool_name": "Task"
  },
  "hooks": [{
    "type": "prompt",
    "prompt": "Validate sub-agent output..."
  }]
}
```

### Validation Flow

1. Sub-agent completes
2. Hook intercepts output
3. Validates against schema
4. Blocks if invalid → Coordinator retries
5. Passes if valid → Workflow continues

For hook configuration, see `references/validation-hooks.md`.

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Fat Coordinator | Coordinator does analysis | Extract to sub-agent |
| Flat Hierarchy | All agents at same level | Add coordinator layer |
| Missing Firewall | Work in main context | Add entry agent |
| No Grounding | Unvalidated outputs | Add grounding phase |
| Serial Execution | Sequential when parallel possible | Identify independent work |

## Quick Decision Guide

### When to Add Firewall

- Complex analysis that shouldn't pollute main context
- Multiple sub-agents needed
- Intermediate work should be isolated

### When to Add Phases

- 3+ distinct stages in workflow
- Different context needs per stage
- Clear sequential dependencies

### When to Add Batching

- Variable priority items
- Not all items need same validation
- Want to reduce operations

## Additional Resources

- `references/firewall-architecture.md` - Coordinator isolation patterns
- `references/phase-execution.md` - Phase-based workflow design
- `references/severity-batching.md` - CRITICAL→HIGH→MEDIUM→LOW routing
- `references/validation-hooks.md` - Pydantic + PostToolUse patterns
