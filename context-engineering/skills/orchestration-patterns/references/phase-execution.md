# Phase-Based Execution

Detailed guide to designing phase-based agent workflows.

## Core Concept

Phase-based execution breaks complex workflows into distinct stages:

```
Phase 1: Analyze    ──▶  Phase 2: Work      ──▶  Phase 3: Ground   ──▶  Phase 4: Synthesize
(FULL context)           (SELECTIVE)             (FILTERED)             (METADATA)
```

Each phase has:
- **Specific purpose** - What it accomplishes
- **Context tier** - What data it receives
- **Agent(s)** - Who does the work
- **Output schema** - What it produces

## Standard Phase Structure

### Phase 1: Analysis (FULL)

**Purpose**: Understand the current state completely.

```yaml
analysis_phase:
  tier: FULL
  agents:
    - plugin-analyzer
    - plan-analyzer
  input:
    - complete_source_data
  output:
    - structured_analysis
    - identified_issues
    - opportunities
```

**Characteristics**:
- Receives everything needed for complete picture
- Produces structured analysis for downstream phases
- Only phase that should receive FULL context

### Phase 2: Work (SELECTIVE)

**Purpose**: Do the actual improvement/processing work.

```yaml
work_phase:
  tier: SELECTIVE
  parallel: true  # Workers can run in parallel
  agents:
    - context-optimizer
    - orchestration-improver
    - handoff-improver
  input:
    - analysis_summary (not full analysis)
    - relevant_files_only
    - focus_area_violations
  output:
    - specific_improvements
    - code_changes
```

**Characteristics**:
- Receives only relevant subset
- Can run in parallel if workers are independent
- Produces actionable improvements

### Phase 3: Grounding (FILTERED)

**Purpose**: Validate and verify the work output.

```yaml
grounding_phase:
  tier: FILTERED
  batched: true  # Items routed by priority
  agents:
    - pattern-checker
    - token-estimator
    - consistency-checker
    - risk-assessor
  input:
    - improvements_by_priority
    - not_all_improvements
  output:
    - validation_results
    - adjusted_estimates
    - risk_assessments
```

**Characteristics**:
- Receives only items that need validation
- Uses severity batching for efficiency
- Multiple validators can run in parallel

### Phase 4: Synthesis (METADATA)

**Purpose**: Generate final output from validated results.

```yaml
synthesis_phase:
  tier: METADATA
  agents:
    - improvement-synthesizer
  input:
    - selected_improvements (IDs + descriptions)
    - scope_stats (counts only)
    - validation_summary
  output:
    - final_report
    - before_after_comparison
```

**Characteristics**:
- Receives only statistics and selections
- Does NOT need full analysis or raw data
- Produces the final user-facing output

## Phase Transitions

### Designing Transitions

For each transition, define:

```yaml
transition:
  from: analyze
  to: work

  # What passes
  passes:
    - analysis_summary
    - relevant_files
    - focus_area

  # What doesn't pass
  excludes:
    - full_analysis_results
    - other_focus_areas
    - raw_source_data

  # Context tier change
  tier_change: FULL → SELECTIVE
```

### Transition Best Practices

1. **Always reduce tier** at each transition
2. **Document exclusions** explicitly
3. **Extract summaries** from full data
4. **Pass identifiers** instead of full objects

### Example Transition Chain

```yaml
# Phase 1 → Phase 2
analysis_to_work:
  passes:
    analysis_summary:
      violations_count: 5
      opportunities_by_type: {context: 3, orchestration: 2}
    relevant_files: [only files with issues]
  excludes:
    - full_plugin_scan
    - files_without_issues

# Phase 2 → Phase 3
work_to_grounding:
  passes:
    high_priority_improvements: [3 items]
    medium_priority_improvements: [2 items]
  excludes:
    - low_priority_improvements
    - full_analysis
    - code_context

# Phase 3 → Phase 4
grounding_to_synthesis:
  passes:
    selected_ids: [CTX-001, CTX-003]
    scope_stats: {analyzed: 14, available: 5, selected: 2}
    validation_summary: {compliant: 2, reduction: "35%"}
  excludes:
    - rejected_improvements
    - full_validation_details
    - original_plugin
```

## Parallel vs Sequential

### When to Parallelize

```yaml
# Parallel (independent workers)
work_phase:
  parallel: true
  agents:
    - context-optimizer      # Independent
    - orchestration-improver # Independent
    - handoff-improver       # Independent

# Parallel (independent validators)
grounding_phase:
  parallel: true
  agents:
    - pattern-checker   # Independent
    - token-estimator   # Independent
```

### When to Sequence

```yaml
# Sequential (dependencies)
workflow:
  - analysis   # Must complete first
  - work       # Depends on analysis
  - grounding  # Depends on work
  - synthesis  # Depends on grounding
```

### Hybrid Approach

```yaml
workflow:
  phase_1:  # Sequential
    - analysis

  phase_2:  # Parallel
    parallel: true
    - context_work
    - orchestration_work
    - handoff_work

  phase_3:  # Parallel per priority batch
    high_batch:
      parallel: true
      - all_validators
    medium_batch:
      parallel: true
      - subset_validators

  phase_4:  # Sequential
    - synthesis
```

## Phase Design Checklist

For each phase, verify:

- [ ] Purpose clearly defined
- [ ] Context tier specified
- [ ] Input documented
- [ ] Output schema defined
- [ ] Agent(s) assigned
- [ ] Parallel/sequential decided
- [ ] Exclusions listed

## Common Mistakes

### Mistake 1: Fat Analysis Phase

```yaml
# BAD: Analysis does everything
analysis_phase:
  agents: [analyzer]
  does:
    - Analyze
    - Generate improvements  # Should be Phase 2
    - Validate               # Should be Phase 3
```

**Fix**: Keep analysis focused on understanding, not acting.

### Mistake 2: Skipping Grounding

```yaml
# BAD: Work → Synthesis
phases:
  - analysis
  - work
  - synthesis  # No validation!
```

**Fix**: Always ground/validate before synthesis.

### Mistake 3: FULL Context Everywhere

```yaml
# BAD: Same tier all phases
analysis_phase: tier: FULL
work_phase: tier: FULL
grounding_phase: tier: FULL
synthesis_phase: tier: FULL
```

**Fix**: Progressive tier reduction.
