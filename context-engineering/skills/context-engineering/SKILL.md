---
name: Context Engineering
description: >
  This skill should be used when designing context management, implementing
  tiered fidelity, reducing token waste, applying Four Laws patterns,
  creating "NOT PASSED" sections, optimizing agent context, or debugging
  context-related issues. Provides SOTA patterns for context-efficient
  multi-agent systems achieving 60-80% token reduction.
---

# Context Engineering

## Overview

State-of-the-art patterns for managing context in LLM agent systems. These patterns enable complex multi-agent workflows while minimizing token overhead through strategic context engineering.

## The Four Laws of Context Management

| Law | Principle | Token Impact |
|-----|-----------|--------------|
| **1. Selective Projection** | Pass only fields each agent needs | -30-50% |
| **2. Tiered Fidelity** | Define explicit context tiers per role | -40-60% |
| **3. Reference vs Embedding** | Use references for large data | -50-80% |
| **4. Lazy Loading** | Load data on-demand, not upfront | -30-50% |

For detailed explanations and examples, see `references/four-laws.md`.

## Context Tiers

| Tier | Description | Use Case | Typical Size |
|------|-------------|----------|--------------|
| **FULL** | Complete data | Initial analysis | 5-20K tokens |
| **SELECTIVE** | Relevant subset | Domain workers | 1-5K tokens |
| **FILTERED** | Criteria-matched | Validators | 500-2K tokens |
| **MINIMAL** | Mode + counts | Routing | 100-500 tokens |
| **METADATA** | Stats only | Synthesis | 50-200 tokens |

For tier selection guidance, see `references/context-tiers.md`.

## Quick Reference: Input Section Pattern

### Before (Anti-pattern)
```yaml
## Input
You receive:
- snapshot: Full context snapshot
- all_findings: Complete list
- full_config: Everything
```

### After (SOTA Pattern)
```yaml
## Input
You receive (SELECTIVE context):
- analysis_summary: Key findings only
- relevant_files: Files for this focus area
- mode: Analysis depth setting

**NOT provided** (context isolation):
- Full plugin contents
- Unrelated analysis results
- Other agents' intermediate work
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Snapshot Broadcasting | Same data to every agent | Tier by role |
| Defensive Inclusion | "Maybe they need this" | Document NOT PASSED |
| Grounding Everything | Validating low-priority | Severity batching |
| Large Embeddings | Full arrays when counts suffice | Reference pattern |
| Repeated Context | Same data multiple times in chain | Pass once, reference later |

## Handoff Protocol

Standard handoff between agents:

```yaml
handoff:
  from_agent: coordinator
  to_agent: analyzer
  context_level: SELECTIVE

  payload:
    mode: deep
    analysis_summary:
      claim_count: 15
      high_risk_count: 4
    relevant_files:
      - file: "[path]"
        content: "[content]"

  not_passed:
    - full_snapshot
    - unrelated_files
    - other_agents_data

  expected_output:
    format: yaml
    schema: AnalysisOutput
```

For complete handoff patterns, see `references/handoff-protocols.md`.

## Severity-Based Batching

Reduce validation operations by priority:

```yaml
batching:
  HIGH:     [all_validators]    # 4 agents
  MEDIUM:   [checker, estimator] # 2 agents
  LOW:      [checker]            # 1 agent
  INFO:     []                   # Skip

# Result: 60-70% fewer validation operations
```

## Metrics to Track

| Metric | Target | Calculation |
|--------|--------|-------------|
| Tier Compliance | 100% | Agents with tier / Total agents |
| Redundancy Ratio | < 0.1 | Duplicate data / Total data |
| Context per Agent | < 2K | Avg tokens per agent |
| NOT PASSED Coverage | 100% | Agents with exclusions / Total |

## Additional Resources

- `references/four-laws.md` - Detailed law explanations with examples
- `references/context-tiers.md` - Tier definitions and selection guide
- `references/handoff-protocols.md` - YAML schema patterns
- `references/examples.md` - Production examples from red-agent
