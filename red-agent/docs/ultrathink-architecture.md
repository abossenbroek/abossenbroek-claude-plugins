# Ultrathink Architecture: Context Isolation for Multi-Agent Orchestration

## Overview

"Ultrathink" refers to red-agent's multi-agent orchestration pattern that **prevents context blowup** through strict context isolation and minimal data passing.

**Core Principle**: Each agent executes independently without carrying full context from previous agents, receiving only **minimal required inputs** via structured YAML.

## The Context Blowup Problem

### Without Ultrathink (Naive Approach)

```yaml
# Command launches agent with FULL conversation history
conversation_context: |
  User: [10KB message]
  Assistant: [15KB response]
  User: [5KB clarification]
  # ... continues growing

# Agent A executes with 30KB context
# Agent B receives Agent A's output + original 30KB = 45KB
# Agent C receives A + B + original = 70KB
# Agent D receives A + B + C + original = 120KB

Total context: ~265KB for 4 agents
```

**Problems**:
- **Exponential growth**: Context grows with each agent
- **Token waste**: Agents receive irrelevant context
- **Cost**: Higher API costs for unnecessary tokens
- **Latency**: Slower processing with large contexts
- **Errors**: Context limits hit on complex workflows

### With Ultrathink (Red-Agent Approach)

```yaml
# Command creates structured snapshot (~2KB)
snapshot:
  mode: "deep"
  files_read: ["auth.ts", "user.ts"]
  pal_available: true

# Agent A receives snapshot only (2KB)
# Agent B receives its specific inputs (3KB)
# Agent C receives its specific inputs (2KB)
# Agent D receives synthesis inputs (5KB)

Total context: ~12KB for 4 agents
```

**Benefits**:
- **Constant size**: Each agent gets only what it needs
- **Minimal waste**: No irrelevant context
- **Cost efficient**: ~95% reduction in tokens
- **Fast**: Smaller contexts process faster
- **Scalable**: Supports 20+ agent workflows

## Context Tiers

Red-agent uses 4 context tiers for passing data between agents:

| Tier | Size | Contents | Use Case |
|------|------|----------|----------|
| **METADATA** | ~500 tokens | IDs, titles, summaries | Routing, filtering, selection |
| **SELECTIVE** | ~3KB | Affected files only | Targeted analysis, single-file edits |
| **FILTERED** | ~5KB | Plan + evidence, no unrelated files | Validation, review, approval |
| **FULL** | ~2KB per file | Complete file content | Editing, detailed analysis |

### Tier Selection Guidelines

**Use METADATA when**:
- Routing findings to appropriate agents
- Filtering by severity/category
- Creating user selection UIs
- Summarizing execution results

**Use SELECTIVE when**:
- Analyzing specific files
- Planning fixes for targeted issues
- Validating changes to known files
- Reading config/schema files

**Use FILTERED when**:
- Validating plans (don't need full code)
- Reviewing proposed changes
- Checking for conflicts
- Grounding assessments

**Use FULL when**:
- Editing file content
- Deep code analysis
- Extracting detailed evidence
- Writing new implementations

## Ultrathink Patterns

### Pattern 1: Firewall (Entry-Point Isolation)

**Problem**: User conversations can contain adversarial prompts, injection attacks, or sensitive data.

**Solution**: Only the coordinator agent is launched from main session. All adversarial work happens in isolated sub-agents.

```
Main Session (User Context)
    |
    | Pass: Structured YAML snapshot (~2KB)
    |
    └── red-team-coordinator (FIREWALL)
            |
            | Pass: Targeted context per agent
            |
            ├── context-analyzer (receives files_read only)
            ├── attack-strategist (receives mode + patterns)
            ├── reasoning-attacker (receives specific attack vector)
            └── insight-synthesizer (receives validated findings)
                |
                | Return: Sanitized markdown report
                |
            Main Session (receives clean report only)
```

**Key Features**:
- **Sanitization**: Adversarial prompts never enter main context
- **Isolation**: Attack logic confined to sub-agents
- **Structured data**: Only YAML in, markdown out
- **No pollution**: Main session stays clean

### Pattern 2: Sequential Pipeline (Fix Orchestration)

**Problem**: Complex workflows have multiple stages that must execute in order.

**Solution**: Chain agents with minimal context passing, each stage only receives what it needs.

```
fix-phase-coordinator
    |
    | Stage 1: Parse Intent (METADATA: finding ID + title)
    ├── fix-reader → {finding_id, parsed_intent, context_hints}
    |
    | Stage 2: Plan Fix (SELECTIVE: affected files only)
    ├── fix-planner-v2 → {finding_id, fix_plan}
    |
    | Stage 3: Validate Plan (FILTERED: plan + evidence, no code)
    ├── fix-red-teamer → {finding_id, validation, approved, adjusted_plan?}
    |
    | Stage 4: Apply Changes (FULL: target file content)
    ├── fix-applicator → {finding_id, applied_changes, success}
    |
    | Stage 5: Commit (METADATA: commit message + files)
    ├── fix-committer → {finding_id, commit_result, success}
    |
    | Stage 6: Validate (SELECTIVE: validation commands)
    └── fix-validator → {finding_id, validation_result}
        |
        | If failure: Retry from Stage 3 with error feedback
        | Max 2 retries (3 total attempts)
```

**Context Flow**:
- Stage 1 → 2: ~500 bytes (finding ID + hints)
- Stage 2 → 3: ~3KB (plan only, no file content)
- Stage 3 → 4: ~5KB (validated plan + target file)
- Stage 4 → 5: ~1KB (diff + file list)
- Stage 5 → 6: ~2KB (validation commands)

**Total context per fix**: ~11.5KB (vs ~50KB if broadcasting everything)

### Pattern 3: Parallel Execution

**Problem**: Multiple independent tasks can be slow if run sequentially.

**Solution**: Launch multiple agents in parallel, each with isolated context.

```
fix-orchestrator
    |
    | Phase 1: Independent fixes (no file conflicts)
    |
    ├─[Parallel]─> fix-phase-coordinator (RF-001) [Context: 11.5KB]
    ├─[Parallel]─> fix-phase-coordinator (RF-003) [Context: 11.5KB]
    ├─[Parallel]─> fix-phase-coordinator (AG-002) [Context: 11.5KB]
    └─[Parallel]─> fix-phase-coordinator (AG-005) [Context: 11.5KB]
    |
    | Wait for all to complete
    |
    | Phase 2: Conflicting fixes (same files, run sequentially)
    |
    ├─> fix-phase-coordinator (RF-002) [Context: 11.5KB]
    └─> fix-phase-coordinator (RF-004) [Context: 11.5KB]
```

**Key Features**:
- **Independent contexts**: Each agent has isolated 11.5KB context
- **No sharing**: Agents don't see each other's work
- **Parallelism**: 4 agents run simultaneously
- **Conflict safety**: Sequential execution for file conflicts

**Performance**:
- 4 parallel fixes: ~46KB total (11.5KB × 4)
- If sequential with broadcast: ~138KB (46KB + 92KB cumulative context)
- **Savings**: ~67% reduction

### Pattern 4: Conditional Branching (PAL Optional)

**Problem**: Optional enhancements should not block core workflow.

**Solution**: Check flag, conditionally execute enhancement, gracefully skip if unavailable.

```
diff-analyzer
    |
    | Always: Base risk assessment
    ├── Calculate risk scores (file-level analysis)
    |
    | Conditional: PAL enhancement
    ├── if pal_available == true:
    │       |
    │       | Pass: SELECTIVE (risk scores only, ~1KB)
    │       ├── Launch PAL challenge agent
    │       ├── Wait for PAL output (timeout: 10s)
    │       ├── Adjust scores based on PAL feedback
    │       └── Add: pal_enhanced: true, pal_adjustments: [...]
    │   else:
    │       └── Add: pal_enhanced: false
    |
    | Return: risk_assessment (with or without PAL)
```

**Key Features**:
- **Non-blocking**: PAL check has timeout
- **Graceful degradation**: Workflow continues if PAL unavailable
- **Output indication**: `pal_enhanced` flag shows PAL usage
- **Minimal PAL context**: Only pass what PAL needs (~1KB)

### Pattern 5: Retry with Adjustment

**Problem**: Automated fixes might fail validation, need retry with error feedback.

**Solution**: Feed errors back to validation stage, adjust plan, retry application.

```
fix-phase-coordinator
    |
    | Stages 1-4: Initial fix attempt
    ├── [Execute stages 1-4] → Applied changes
    |
    | Stage 5: Commit
    ├── fix-committer → {commit_hash: "abc123", success: true}
    |
    | Stage 6: Validate (FIRST ATTEMPT)
    ├── fix-validator → {tests_passed: false, error: "Type error..."}
    |
    | RETRY LOOP (Max 2 retries)
    |
    | Stage 3: Re-validate with error feedback
    ├── fix-red-teamer
    │   Input (FILTERED): {original_plan, errors: ["Type error..."], retry: 1}
    │   Output: {adjusted_plan: "Add type annotation..."}
    |
    | Stages 4-6: Re-apply with adjusted plan
    ├── [Re-execute stages 4-6] → New commit
    |
    | Stage 6: Validate (SECOND ATTEMPT)
    ├── fix-validator → {tests_passed: true, lint_passed: true}
    |
    | SUCCESS: Return result
    └── {status: "success", commit_hash: "def456", retry_count: 1}
```

**Context Management**:
- Retry 1: ~7KB (plan + first error)
- Retry 2: ~9KB (plan + both errors)
- **No cumulative context**: Don't pass full Stage 1-2 outputs to retries

## Context Engineering Examples

### Example 1: /redteam Command

#### Naive Approach (WITHOUT Ultrathink)

```yaml
# Pass full conversation (50KB+)
Task:
  user_conversation: |
    User: I want to analyze this conversation for risks...
    [Full conversation history: 50KB]

red-team-coordinator:
  receives: 50KB
  launches 4 attackers: Each receives 50KB
  total_context: 50KB + (50KB × 4) = 250KB
```

#### Ultrathink Approach (WITH Context Isolation)

```yaml
# Create structured snapshot (2KB)
Task:
  snapshot:
    mode: "deep"
    files_read: ["auth.ts"]
    tools_invoked: ["Read", "Grep"]
    claims: ["Authentication is secure"]
    pal_available: true

red-team-coordinator:
  receives: 2KB snapshot
  launches 4 attackers:
    - reasoning-attacker: {mode: "deep", claims: [...]} → 1KB
    - context-attacker: {files_read: [...]} → 0.5KB
    - hallucination-prober: {claims: [...], tools: [...]} → 1KB
    - scope-analyzer: {mode: "deep"} → 0.3KB
  total_context: 2KB + 2.8KB = 4.8KB

Context reduction: 98% (250KB → 4.8KB)
```

### Example 2: Fix Orchestration

#### Naive Approach

```yaml
# Broadcast everything to all stages
fix-orchestrator:
  Stage 1 receives: {finding (5KB), all_code (50KB)} = 55KB
  Stage 2 receives: {Stage1 output + finding + code} = 60KB
  Stage 3 receives: {Stage1+2 outputs + finding + code} = 70KB
  Stage 4 receives: {Stage1+2+3 outputs + finding + code} = 80KB
  Stage 5 receives: {all previous + finding + code} = 90KB
  Stage 6 receives: {all previous + finding + code} = 100KB

Total: 455KB cumulative
```

#### Ultrathink Approach

```yaml
# Minimal context per stage
fix-orchestrator:
  Stage 1 receives: {finding_id, title} = 0.5KB
  Stage 2 receives: {finding_id, intent, target_file (2KB)} = 3KB
  Stage 3 receives: {finding_id, plan (3KB)} = 5KB
  Stage 4 receives: {finding_id, plan, target_file} = 5KB
  Stage 5 receives: {finding_id, diff (1KB), files} = 2KB
  Stage 6 receives: {finding_id, commit_hash, commands} = 1.5KB

Total: 17KB cumulative

Context reduction: 96% (455KB → 17KB)
```

## Validation Boundaries

Ultrathink uses **Pydantic models** at agent boundaries to enforce structured data exchange:

```python
# Stage 3 output (fix-red-teamer)
class FixRedTeamerOutput(BaseModel):
    finding_id: str                          # METADATA: routing
    validation: dict[str, Any]               # FILTERED: validation results
    approved: bool                           # METADATA: decision
    adjusted_plan: dict[str, Any] | None     # SELECTIVE: changes only

# Stage 4 receives ONLY these fields (no full context leak)
```

**Benefits**:
- **Type safety**: Pydantic validates schema
- **Explicit contract**: Clear what each agent receives/returns
- **Context enforcement**: Can't accidentally pass full context
- **Testing**: Easy to mock with known schemas

## Orchestration Strategies

### Strategy 1: Sequential for Dependencies

Use when stages must execute in order:

```yaml
# Fix orchestration (6 stages, each depends on previous)
Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5 → Stage 6
```

**When to use**:
- Later stages need earlier results
- Order matters (e.g., plan before apply)
- Validation after changes

### Strategy 2: Parallel for Independence

Use when tasks can run simultaneously:

```yaml
# Multiple fixes with no file conflicts
fix-orchestrator:
  Phase 1 (parallel):
    - fix-phase-coordinator (RF-001) ║
    - fix-phase-coordinator (RF-003) ║  All execute simultaneously
    - fix-phase-coordinator (AG-002) ║
```

**When to use**:
- Tasks modify different files
- No shared state
- Independent analysis tasks

### Strategy 3: Batched for Resource Limits

Use when parallel execution needs throttling:

```yaml
# PR analysis with 12 files, max 4 parallel
pr-analysis-coordinator:
  Batch 1: [file1, file2, file3, file4] → parallel
  Wait for Batch 1 completion
  Batch 2: [file5, file6, file7, file8] → parallel
  Wait for Batch 2 completion
  Batch 3: [file9, file10, file11, file12] → parallel
```

**When to use**:
- Resource constraints (CPU, memory, API limits)
- Rate limiting concerns
- Large-scale operations

### Strategy 4: Phased for Conflicts

Use when some tasks conflict, others don't:

```yaml
# Fix orchestration with dependency analysis
fix-orchestrator:
  Phase 1 (parallel): Independent fixes [RF-001, RF-003, AG-002]
  Phase 2 (sequential): Conflicting fixes [RF-002, RF-004]
```

**When to use**:
- Some tasks modify same files
- Need sequential execution for conflicts
- Want parallelism where safe

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1: Broadcasting Full Context

```yaml
# BAD: Pass everything to everyone
coordinator:
  launches 4 agents:
    - agent1 receives: {full_conversation, all_files, all_findings}
    - agent2 receives: {full_conversation, all_files, all_findings}
    - agent3 receives: {full_conversation, all_files, all_findings}
    - agent4 receives: {full_conversation, all_files, all_findings}

# Result: 4x context duplication, exponential growth
```

**Why it's bad**: Context explodes, tokens wasted, slow, expensive

**Fix**: Pass only what each agent needs (context tiers)

### ❌ Anti-Pattern 2: Cumulative Context Passing

```yaml
# BAD: Accumulate all previous outputs
Stage 1 output: A (5KB)
Stage 2 receives: A → outputs B (8KB)
Stage 3 receives: A + B → outputs C (12KB)
Stage 4 receives: A + B + C → outputs D (18KB)

# Result: 5KB + 13KB + 25KB + 43KB = 86KB cumulative
```

**Why it's bad**: Exponential growth, most context irrelevant

**Fix**: Each stage receives only its required inputs

### ❌ Anti-Pattern 3: Deep Agent Nesting Without Isolation

```yaml
# BAD: Nested agents share parent context
coordinator (50KB context)
  └── sub-agent1 (inherits 50KB + adds 10KB = 60KB)
      └── sub-sub-agent (inherits 60KB + adds 5KB = 65KB)
          └── sub-sub-sub-agent (inherits 65KB + adds 3KB = 68KB)
```

**Why it's bad**: Context inheritance causes blowup

**Fix**: Each agent gets fresh context (firewall pattern)

### ❌ Anti-Pattern 4: Synchronous Sequential When Parallel Possible

```yaml
# BAD: Run independent tasks sequentially
Task 1 (5 min) → Task 2 (5 min) → Task 3 (5 min) → Task 4 (5 min)
Total time: 20 minutes
```

**Why it's bad**: Wastes time, no parallelism

**Fix**: Run independent tasks in parallel (5 minutes total)

### ❌ Anti-Pattern 5: No Retry Logic

```yaml
# BAD: Give up on first failure
fix-applicator → {success: false, error: "Type error"}
Return: "Fix failed"
```

**Why it's bad**: Automated fixes often need adjustments

**Fix**: Retry with error feedback (Pattern 5)

## Performance Metrics

### Real-World Comparisons

| Workflow | Without Ultrathink | With Ultrathink | Reduction |
|----------|-------------------|-----------------|-----------|
| /redteam (4 attackers) | 250KB | 4.8KB | 98% |
| /redteam-pr (12 files) | 600KB | 24KB | 96% |
| Fix orchestration (6 stages) | 455KB | 17KB | 96% |
| Parallel fixes (4 findings) | 138KB | 46KB | 67% |

### Token Cost Savings

Assuming $0.01 per 1K tokens (input):

| Workflow | Cost Without | Cost With | Savings |
|----------|-------------|-----------|---------|
| /redteam | $2.50 | $0.05 | $2.45 (98%) |
| /redteam-pr | $6.00 | $0.24 | $5.76 (96%) |
| Fix orchestration | $4.55 | $0.17 | $4.38 (96%) |

**Annual savings** for 1000 workflows: ~$12,770

## Implementation Checklist

When implementing ultrathink patterns:

- [ ] **Define context tiers** for your workflow
- [ ] **Create Pydantic models** for agent boundaries
- [ ] **Minimize inputs** to each agent (what's the smallest viable input?)
- [ ] **Use structured YAML** for all inter-agent communication
- [ ] **Implement firewall pattern** at entry points
- [ ] **Identify parallelization opportunities** (independent tasks)
- [ ] **Add retry logic** for automated operations
- [ ] **Document context flow** (what passes where, how much)
- [ ] **Test with large inputs** (does context explode?)
- [ ] **Measure context usage** (actual vs theoretical)

## References

- **Firewall Pattern**: `red-agent/agents/red-team-coordinator.md`
- **Sequential Pipeline**: `red-agent/coordinator-internal/fix/fix-phase-coordinator.md`
- **Parallel Execution**: `red-agent/agents/fix-orchestrator.md` (Phase 1)
- **Conditional Branching**: `red-agent/coordinator-internal/diff-analyzer.md` (PAL section)
- **Retry with Adjustment**: `red-agent/coordinator-internal/fix/fix-phase-coordinator.md` (Stage 6)
- **Pydantic Models**: `src/red_agent/models/`
- **PAL Integration**: `red-agent/docs/pal-integration.md`
