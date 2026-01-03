# PAL Integration Guidelines

## Overview

PAL (Prompt-Agent-Loop) is an **optional enhancement** for red-agent workflows. All features work correctly whether PAL is available or not.

**Key Principle**: PAL MUST BE PURELY OPTIONAL - no workflow should fail if PAL is unavailable.

## Standard Integration Pattern

All PAL usage follows this consistent pattern:

```yaml
Step 1: Availability Check (Non-Blocking)
  - Launch pal-availability-checker agent
  - Parse YAML result for pal_available flag
  - Timeout: 5 seconds max
  - Continue regardless of result

Step 2: Flag Propagation
  - Include pal_available: true/false in snapshot/input
  - Pass to downstream agents

Step 3: Conditional Usage
  - Check pal_available flag before using PAL
  - Execute PAL enhancement if available
  - Gracefully skip if unavailable

Step 4: Output Indication
  - Add pal_enhanced: true/false to output
  - Document PAL adjustments if applied
  - Include pal_reasoning fields where relevant
```

## PAL Usage by Workflow

### 1. Standard Red Team Analysis (/redteam, /redteam-w-fix)

**PAL Check**: Lines 28-45 in commands
**Usage**: Flag passed to coordinator, available for sub-agents
**Enhancement**: None at coordinator level (sub-agents may use)

**Pattern**:
```yaml
# Step 1 in command
pal_check:
  agent: pal-availability-checker
  blocking: false
  timeout: 5_seconds
  result: pal_available: true/false

# Included in snapshot
snapshot:
  pal_available: true
  pal_models: ["gpt-4o", "gemini-pro"]
```

### 2. PR Analysis (/redteam-pr:*)

**PAL Check**: Lines 24-54 in commands
**Usage**: Enhanced risk assessment (diff-analyzer), security analysis (security-prober), CRITICAL finding validation (pr-analysis-coordinator)

**Enhancement Points**:

#### diff-analyzer (Risk Validation)
- **Trigger**: `pal_available == true`
- **Enhancement**: PAL validates risk scores
- **Fallback**: Use base risk assessment
- **Output**: `pal_enhanced: true`, `pal_adjustments: [...]`

```yaml
# If pal_available == true
pal_adjustments:
  - file: "src/auth/controller.ts"
    original_score: 0.7
    adjusted_score: 0.85
    reason: "PAL identified additional SQL injection risk"
```

#### security-prober (Deepthink for CRITICAL/HIGH)
- **Trigger**: `pal_available == true AND severity in [CRITICAL, HIGH]`
- **Enhancement**: PAL deepthink for exploit scenarios
- **Fallback**: Skip PAL enhancement
- **Output**: `pal_enhanced: true`, `pal_reasoning: "..."`, `exploit_scenario`

```yaml
# Enhanced finding
finding:
  id: "RF-001"
  severity: "CRITICAL"
  pal_enhanced: true
  pal_reasoning: "PAL deepthink analysis confirms..."
  exploit_scenario: "Attacker could..."
```

#### pr-analysis-coordinator (PAL Challenge for CRITICAL)
- **Trigger**: `pal_available == true AND mode == "deep" AND severity == CRITICAL`
- **Enhancement**: PAL challenges grounding assessment
- **Fallback**: Skip PAL challenge
- **Output**: `pal_challenged: true`, `pal_challenge_reasoning`, `confidence_adjustment`

```yaml
# Challenged finding
finding:
  id: "RF-001"
  pal_challenged: true
  pal_challenge_reasoning: "PAL challenge confirmed..."
  confidence_adjustment: -0.05  # Reduced from 0.95 to 0.90
```

### 3. Fix Orchestration (/redteam-fix-orchestrator)

**PAL Check**: Lines 26-45 in command
**Usage**: Future enhancement (NOT IMPLEMENTED)
**Current**: File-level conflict detection only
**Future**: PAL-based dependency analysis

**Current Implementation**:
- Receives `pal_available` flag but doesn't use it
- Uses file-level conflict detection (default)
- See fix-orchestrator.md lines 386-429 for future design

## PAL Availability Checker

**Agent**: `pal-availability-checker.md`
**Purpose**: Non-blocking PAL MCP detection

**Behavior**:
1. Attempts to call `mcp__pal__listmodels` tool
2. Returns structured YAML:
   ```yaml
   pal_check:
     available: true
     models:
       - name: "gpt-4o"
         provider: "openai"
       - name: "gemini-pro"
         provider: "google"
   ```
3. If tool fails or doesn't exist: Returns `available: false`
4. **Timeout**: Must return result in under 5 seconds
5. **Critical**: Failure is NOT an error - PAL is optional

## Graceful Degradation Requirements

### Mandatory Checks

For each PAL usage, verify:

- [ ] Has `pal_available` check before use?
- [ ] Has documented fallback behavior?
- [ ] Never blocks/fails if PAL unavailable?
- [ ] Has timeout on PAL calls (non-blocking)?
- [ ] Output indicates PAL usage (pal_enhanced flag)?

### Example Patterns

#### Good: Conditional with Fallback
```markdown
## PAL Enhancement (Optional)

If pal_available == true:
  - Launch PAL enhancement agent
  - Apply PAL feedback
  - Add to output: pal_enhanced: true

If pal_available == false:
  - Skip PAL enhancement (graceful degradation)
  - Add to output: pal_enhanced: false
```

#### Bad: Blocking on PAL
```markdown
## PAL Enhancement

Launch PAL enhancement agent  # ❌ No availability check!
Apply PAL feedback             # ❌ Blocks if PAL unavailable!
```

## Output Indication

All PAL-enhanced outputs MUST indicate PAL usage:

| Agent | Output Flag | Additional Fields |
|-------|------------|-------------------|
| diff-analyzer | `pal_enhanced: true/false` | `pal_adjustments: [...]` |
| security-prober | `pal_enhanced: true` | `pal_reasoning`, `exploit_scenario` |
| pr-analysis-coordinator | `pal_challenged: true` | `pal_challenge_reasoning`, `confidence_adjustment` |
| fix-orchestrator | None (not implemented) | Future: `pal_dependency_analysis` |

## Testing Requirements

### Test Scenarios

1. **PAL Unavailable**:
   - Run all commands with PAL MCP not installed
   - Expected: All commands complete successfully with `pal_available: false`

2. **PAL Availability Check Timeout**:
   - Mock pal-availability-checker to timeout
   - Expected: Commands continue after timeout with `pal_available: false`

3. **PAL Enhancement Failure**:
   - Mock PAL deepthink/challenge to fail mid-analysis
   - Expected: Analysis continues without PAL enhancement, `pal_enhanced: false`

4. **Mixed Availability**:
   - PAL available at start, becomes unavailable mid-workflow
   - Expected: Agents that already checked flag continue with their decisions

### Test Fixtures

Use `tests/fixtures/pal_mock.py` for mocking PAL availability:

```python
from tests.fixtures.pal_mock import MockPAL

# Mock PAL unavailable
with MockPAL(available=False):
    # Run workflow
    pass

# Mock PAL available with specific models
with MockPAL(available=True, models=["gpt-4o"]):
    # Run workflow
    pass

# Mock PAL timeout
with MockPAL(timeout=True):
    # Run workflow
    pass
```

## Best Practices

### 1. Explicit Non-Blocking Statements

Always document that PAL checks are non-blocking:

```markdown
This step is NON-BLOCKING - continue regardless of result. PAL is optional.
```

### 2. Graceful Degradation Documentation

Explicitly document fallback behavior:

```markdown
If pal_available == false: Skip PAL enhancement (graceful degradation).
```

### 3. Dual Conditions for Safety

Use multiple conditions when appropriate:

```markdown
If pal_available == true AND mode == "deep"
```

### 4. Timeout Requirements

Specify timeout limits:

```markdown
Return result in under 5 seconds
```

### 5. Future-Ready Design

Accept `pal_available` flag even if not currently used:

```markdown
# Input
pal_available: true  # Currently unused, reserved for future enhancement
```

## Troubleshooting

### PAL MCP Not Detected

**Symptom**: `pal_available: false` in all workflows

**Diagnosis**:
1. Check if PAL MCP server is installed
2. Verify MCP server configuration in Claude Code settings
3. Check `mcp__pal__listmodels` tool is available

**Solution**:
- Install PAL MCP server
- Restart Claude Code
- **Workaround**: Workflows continue without PAL (no action needed)

### PAL Check Times Out

**Symptom**: pal-availability-checker takes >5 seconds

**Diagnosis**:
1. PAL MCP server may be slow to respond
2. Network issues if PAL uses remote API
3. MCP server initialization issues

**Solution**:
- Check PAL MCP server logs
- Verify network connectivity
- Restart MCP server
- **Workaround**: Timeout triggers `pal_available: false`, workflows continue

### PAL Enhancement Fails Mid-Analysis

**Symptom**: Analysis completes but `pal_enhanced: false` despite `pal_available: true`

**Diagnosis**:
1. PAL deepthink/challenge agent failed
2. PAL MCP tool error during execution
3. Invalid PAL response format

**Solution**:
- Check sub-agent logs for PAL errors
- Verify PAL MCP tool is working: Test `mcp__pal__listmodels`
- **Workaround**: Analysis completes with base assessment (no PAL enhancement)

## Architecture Decisions

### Why PAL is Optional

1. **Availability**: PAL MCP may not be installed
2. **Performance**: PAL adds latency (deepthink can be slow)
3. **Reliability**: Core analysis should never depend on external MCP
4. **Flexibility**: Users can choose when to enable PAL (mode=deep)

### Why Non-Blocking

1. **User Experience**: Analysis shouldn't hang waiting for PAL
2. **Robustness**: PAL failures don't break workflows
3. **Timeout Protection**: 5-second timeout prevents infinite waits
4. **Graceful Degradation**: Base analysis always available

### Why Dual Conditions (pr-analysis-coordinator)

PAL challenge requires both:
- `pal_available == true`: PAL MCP must be present
- `mode == "deep"`: User explicitly requested enhanced analysis

**Rationale**: Expensive PAL operations only for deep analysis requests.

### Why Severity Filtering (security-prober)

PAL deepthink only for CRITICAL/HIGH findings:
- **Cost**: PAL calls are expensive (time + API costs)
- **Value**: Highest value for severe findings
- **Scalability**: Prevents PAL overload on large PRs

**Rationale**: Focus expensive enhancements where they matter most.

## Future Enhancements

### 1. PAL Dependency Analysis (fix-orchestrator)

**Status**: Design complete, not implemented
**File**: `fix-orchestrator.md` lines 386-429

**When to implement**:
- Users report file-level detection missing conflicts
- Import chain conflicts become common
- User explicitly requests PAL-based dependency analysis

**Implementation**:
1. Update `FixOrchestratorOutput` model with `pal_dependency_analysis` fields
2. Add conditional PAL usage in Phase 1 (dependency analysis)
3. Test both `pal_available=true/false` paths
4. Document enhancement in fix-orchestrator.md

### 2. PAL Model Selection Strategy

**Current**: Returns list of available models, doesn't specify which to use
**Future**: Could add model selection guidance:
- Use GPT-4o for deepthink (complex reasoning)
- Use Gemini Pro for challenge (adversarial analysis)
- Use Claude Opus for synthesis (comprehensive summary)

### 3. PAL Usage Statistics in Reports

**Current**: Reports don't indicate PAL usage
**Future**: Could add transparency:
```markdown
Analysis enhanced with PAL for 3 CRITICAL findings
PAL challenge applied to 2 findings, adjusted confidence by -5%
```

### 4. Configurable PAL Timeouts

**Current**: Hardcoded 5-second timeout
**Future**: Could make timeout configurable per workflow:
```yaml
pal_config:
  availability_check_timeout: 5
  deepthink_timeout: 30
  challenge_timeout: 15
```

## References

- **PAL Availability Checker**: `red-agent/agents/pal-availability-checker.md`
- **PR Analysis Coordinator**: `red-agent/agents/pr-analysis-coordinator.md` (lines 253-291)
- **Diff Analyzer**: `red-agent/coordinator-internal/diff-analyzer.md` (lines 31-75)
- **Security Prober**: `red-agent/coordinator-internal/security-prober.md` (lines 107-150)
- **Fix Orchestrator**: `red-agent/agents/fix-orchestrator.md` (lines 386-429)
- **Test Fixtures**: `tests/fixtures/pal_mock.py` (to be created)
