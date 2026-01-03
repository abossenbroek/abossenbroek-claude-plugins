# Handoff Protocols

Standard patterns for agent-to-agent data transfer.

## Standard Handoff Schema

```yaml
handoff:
  # Identifies the transition
  from_agent: "[source agent]"
  to_agent: "[target agent]"
  context_level: FULL|SELECTIVE|FILTERED|MINIMAL|METADATA

  # What IS passed
  payload:
    field_1: "[data]"
    field_2: "[data]"
    # Keep flat and minimal

  # What is NOT passed (explicit exclusions)
  not_passed:
    - full_snapshot
    - unrelated_data
    - other_agents_work
    # Document exclusions for clarity

  # Expected response format
  expected_output:
    format: yaml|json|markdown
    schema: "[schema name]"
```

## Protocol by Context Tier

### FULL Handoff

```yaml
handoff:
  from_agent: improve-coordinator
  to_agent: plugin-analyzer
  context_level: FULL

  payload:
    plugin_path: "/path/to/plugin"
    plugin_manifest:
      name: "plugin-name"
      version: "1.0.0"
      # Full manifest
    agent_files:
      - file: "agents/coordinator.md"
        content: |
          # Full content
      - file: "coordinator-internal/analyzer.md"
        content: |
          # Full content
    mode: "all"

  not_passed:
    - git_history
    - node_modules
    - build_artifacts

  expected_output:
    format: yaml
    schema: PluginAnalysis
```

### SELECTIVE Handoff

```yaml
handoff:
  from_agent: improve-coordinator
  to_agent: context-optimizer
  context_level: SELECTIVE

  payload:
    analysis_summary:
      plugin_name: "red-agent"
      violations_count: 5
      opportunities_count: 8
    focus_area: "context"
    relevant_files:
      - file: "agents/coordinator.md"
        content: |
          # Only this file has context issues
    violations_to_address:
      - type: "MISSING_TIER"
        file: "agents/coordinator.md"

  not_passed:
    - full_plugin_contents
    - files_without_issues
    - orchestration_violations
    - handoff_violations

  expected_output:
    format: yaml
    schema: ContextImprovement[]
```

### FILTERED Handoff

```yaml
handoff:
  from_agent: improve-coordinator
  to_agent: grounding/pattern-checker
  context_level: FILTERED

  payload:
    improvements_to_check:
      - id: "CTX-001"
        type: "TIER_SPEC"
        file: "agents/coordinator.md"
        priority: "HIGH"
      - id: "CTX-002"
        type: "NOT_PASSED"
        file: "agents/analyzer.md"
        priority: "HIGH"
      # Only HIGH priority in this batch
    focus_area: "context"
    improvement_count: 5  # Total for context

  not_passed:
    - MEDIUM_priority_improvements
    - LOW_priority_improvements
    - full_analysis_results
    - code_samples  # Just IDs for checking

  expected_output:
    format: yaml
    schema: PatternCompliance[]
```

### MINIMAL Handoff

```yaml
handoff:
  from_agent: command
  to_agent: coordinator
  context_level: MINIMAL

  payload:
    mode: "all"
    target_path: "/path/to/plugin"
    # Just identifiers and settings

  not_passed:
    - file_contents
    - prior_analysis
    - conversation_context

  expected_output:
    format: yaml
    schema: ImprovementReport
```

### METADATA Handoff

```yaml
handoff:
  from_agent: improve-coordinator
  to_agent: improvement-synthesizer
  context_level: METADATA

  payload:
    selected_improvements:
      - id: "CTX-001"
        description: "Add context tier to coordinator"
        files_modified: ["agents/coordinator.md"]
      - id: "CTX-002"
        description: "Add NOT PASSED section"
        files_modified: ["agents/analyzer.md"]
    scope_metadata:
      plugin_name: "red-agent"
      files_analyzed: 14
      improvements_available: 8
      improvements_selected: 2
    grounding_summary:
      pattern_compliant: 2
      estimated_reduction: "35%"

  not_passed:
    - full_analysis_results
    - rejected_improvements
    - original_plugin_contents
    - intermediate_outputs

  expected_output:
    format: yaml
    schema: ImprovementReport
```

## Handoff Patterns by Workflow

### Analysis Pipeline

```
Command
  │
  └──[MINIMAL]──> Coordinator
                     │
                     ├──[FULL]──> Analyzer
                     │              Output: PluginAnalysis
                     │
                     └──[SELECTIVE]──> Flow Mapper
                                         Output: ContextFlowMap
```

### Improvement Pipeline

```
Coordinator (has analysis)
  │
  ├──[SELECTIVE]──> Context Optimizer
  │                   Output: ContextImprovement[]
  │
  ├──[SELECTIVE]──> Orchestration Improver
  │                   Output: OrchestrationImprovement[]
  │
  └──[SELECTIVE]──> Handoff Improver
                      Output: HandoffImprovement[]
```

### Grounding Pipeline

```
Coordinator (has improvements)
  │
  ├──[FILTERED/HIGH]──> All 4 Grounding Agents
  │                       Output: *Grounding results
  │
  ├──[FILTERED/MEDIUM]──> Pattern Checker + Token Estimator
  │                         Output: PatternCompliance, TokenEstimate
  │
  └──[FILTERED/LOW]──> Pattern Checker only
                         Output: PatternCompliance
```

### Synthesis Pipeline

```
Coordinator (has grounded improvements + user selections)
  │
  └──[METADATA]──> Synthesizer
                     Output: ImprovementReport
```

## Best Practices

### 1. Always Document NOT PASSED

```yaml
not_passed:
  - "[explicit item 1]"
  - "[explicit item 2]"
```

This makes context isolation visible and debuggable.

### 2. Match Schema to Tier

| Tier | Payload Complexity |
|------|-------------------|
| FULL | Full objects, nested structures |
| SELECTIVE | Flat objects, relevant fields only |
| FILTERED | Arrays of items matching criteria |
| MINIMAL | Scalars, counts, identifiers |
| METADATA | Summary statistics only |

### 3. Validate Expected Output

Always specify:
```yaml
expected_output:
  format: yaml
  schema: "[Pydantic model name]"
```

This enables PostToolUse hook validation.

### 4. Tier Down, Never Up

```
FULL → SELECTIVE → FILTERED → MINIMAL → METADATA

Never: MINIMAL → FULL (fetching more later)
```

If an agent needs more data than its tier provides, the workflow design is wrong.
