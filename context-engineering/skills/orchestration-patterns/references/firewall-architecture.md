# Firewall Architecture

Detailed guide to implementing coordinator isolation in multi-agent systems.

## Core Concept

The firewall pattern creates a boundary between the main session and specialized work:

```
Main Session
    │
    │ (only plugin_path, mode)
    ▼
┌─────────────────────────────────────────┐
│           FIREWALL BOUNDARY             │
│  ┌──────────────────────────────────┐   │
│  │     Entry Coordinator            │   │
│  │     (Thin Router)                │   │
│  │                                  │   │
│  │  • Routes data to sub-agents     │   │
│  │  • Does NOT analyze              │   │
│  │  • Does NOT synthesize           │   │
│  │  • Returns final report ONLY     │   │
│  └──────────────────────────────────┘   │
│                 │                       │
│    ┌────────────┼────────────┐          │
│    │            │            │          │
│    ▼            ▼            ▼          │
│  Analyzer    Improver    Validator      │
│                                         │
│  (All work stays inside firewall)       │
└─────────────────────────────────────────┘
    │
    │ (only final report)
    ▼
Main Session
```

## Why Firewall?

### Problem: Context Pollution

Without firewall:
```
Main Session
    │
    ├── Analysis reasoning pollutes context
    ├── Intermediate findings exposed
    ├── 50KB+ of work visible to future prompts
    └── Hard to debug what influenced what
```

### Solution: Isolation

With firewall:
```
Main Session
    │
    ├── Only final report visible (~2KB)
    ├── Work context isolated
    ├── Clean separation of concerns
    └── Easy to debug and maintain
```

## Entry Agent Pattern

### What Entry Agents DO

1. **Receive minimal input** from main session
2. **Route data** to sub-agents
3. **Orchestrate phases** in sequence
4. **Return final output** unchanged

### What Entry Agents DO NOT

1. **Analyze** - That's sub-agents' job
2. **Synthesize** - That's synthesizer's job
3. **Modify output** - Return verbatim
4. **Hold state** - Stateless routing

### Entry Agent Template

```markdown
# [Name] Coordinator Agent

You are the [NAME] COORDINATOR - the firewall between main session and [work type].

## Your Role: THIN ROUTER

You are a THIN ROUTER. You:
- ROUTE data between sub-agents
- DO NOT perform analysis yourself
- DO NOT aggregate or synthesize
- DO NOT modify the final output

## Context Isolation (CRITICAL)

You are in an ISOLATED context. This means:
- You can spawn sub-agents that do [work type]
- [Work type] stays in this isolated context
- Only the final [output type] returns to main session

## Execution Flow

### Phase 1: [Initial Phase] (FULL CONTEXT)
[Launch analyzer with full data]

### Phase 2: [Work Phase] (SELECTIVE CONTEXT)
[Launch workers with relevant subset]

### Phase 3: [Grounding Phase] (FILTERED CONTEXT)
[Launch validators with priority batch]

### Phase 4: [Synthesis Phase] (METADATA CONTEXT)
[Launch synthesizer with stats + results]

### Phase 5: Return Output
Return the synthesizer's output DIRECTLY.

DO NOT:
- Add any wrapper text
- Explain the process
- Include coordinator notes
- Modify the output in any way
```

## Sub-Agent Placement

### Directory Structure

```
plugin/
├── agents/                    # Entry points (firewall)
│   └── workflow-coordinator.md
│
└── coordinator-internal/      # Work agents (isolated)
    ├── analyzer.md
    ├── worker-a.md
    ├── worker-b.md
    ├── grounding/
    │   ├── checker.md
    │   └── validator.md
    └── synthesizer.md
```

### Why `coordinator-internal/`?

1. **Not directly invocable** - Users can't bypass firewall
2. **Clear ownership** - Belongs to coordinator
3. **Isolation signal** - These agents work in isolation
4. **Organization** - Related agents grouped together

## Data Flow Rules

### Rule 1: Tier Down, Never Up

```
FULL (analyzer) → SELECTIVE (workers) → FILTERED (grounding) → METADATA (synthesis)

NEVER: METADATA → FULL (fetching more data later)
```

### Rule 2: Structured Handoffs Only

```yaml
# BAD: Passing raw context
prompt_to_subagent: |
  Here's everything:
  [raw conversation dump]

# GOOD: Structured handoff
prompt_to_subagent:
  task: "Analyze plugin structure"
  payload:
    plugin_path: "/path/to/plugin"
    mode: "deep"
```

### Rule 3: Explicit Exclusions

```yaml
# In coordinator prompts:
**DO NOT pass**:
- Full snapshot
- Unrelated data
- Other agents' work

# In sub-agent definitions:
**NOT provided**:
- [Explicit list of exclusions]
```

## Multi-Coordinator Systems

When plugin has multiple workflows:

```
plugin/
├── agents/
│   ├── workflow-a-coordinator.md   # Firewall for A
│   └── workflow-b-coordinator.md   # Firewall for B
│
└── coordinator-internal/
    ├── a/                          # A's sub-agents
    │   ├── analyzer.md
    │   └── synthesizer.md
    │
    ├── b/                          # B's sub-agents
    │   ├── processor.md
    │   └── reporter.md
    │
    └── shared/                     # Shared sub-agents
        └── validator.md
```

## Debugging Firewalls

### Issue: Coordinator Doing Work

**Symptom**: Coordinator has analysis logic
**Fix**: Extract to sub-agent

```markdown
# BEFORE (bad)
## Execution
1. Analyze the files...
2. Find patterns...

# AFTER (good)
## Execution
1. Launch analyzer sub-agent
2. Receive structured results
```

### Issue: Context Leaking

**Symptom**: Sub-agent receives too much
**Fix**: Add NOT PASSED section

```markdown
# BEFORE (bad)
Prompt: [everything]

# AFTER (good)
Prompt:
  relevant_data: [filtered]

**NOT provided**:
- Full context
- Unrelated items
```

### Issue: Output Modified

**Symptom**: Coordinator adds commentary
**Fix**: Return verbatim

```markdown
# BEFORE (bad)
return f"Here's the analysis:\n{output}"

# AFTER (good)
Return output DIRECTLY without modification.
```
