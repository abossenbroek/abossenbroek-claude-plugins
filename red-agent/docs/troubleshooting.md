# Red Agent Troubleshooting Guide

## Common Issues

### PAL Integration Issues

#### PAL Not Detected (`pal_available: false`)

**Symptoms**:
- All workflows report `pal_available: false`
- PAL enhancements never applied
- `pal_enhanced: false` in all outputs

**Diagnosis**:
```bash
# Check if PAL MCP server is configured
# Look for mcp__pal__* tools in Claude Code

# Test PAL availability manually
# Launch pal-availability-checker agent
```

**Solutions**:
1. **Install PAL MCP server** (if not installed)
2. **Verify MCP configuration** in Claude Code settings
3. **Restart Claude Code** after MCP changes
4. **Check MCP server logs** for errors

**Workaround**: Workflows continue without PAL (no action needed)

---

#### PAL Check Times Out

**Symptoms**:
- `pal-availability-checker` takes >5 seconds
- Workflows proceed with `pal_available: false`
- No error messages

**Diagnosis**:
```bash
# Check MCP server response time
# Look for slow tool execution in logs
# Verify network connectivity (if PAL uses remote API)
```

**Solutions**:
1. **Check PAL MCP server logs**
2. **Verify network connectivity**
3. **Restart MCP server**
4. **Increase timeout** (edit pal-availability-checker.md line 62)

**Workaround**: Timeout triggers `pal_available: false`, workflows continue

---

#### PAL Enhancement Fails Mid-Analysis

**Symptoms**:
- `pal_available: true` but `pal_enhanced: false`
- Analysis completes successfully
- No PAL adjustments in output

**Diagnosis**:
```bash
# Check sub-agent logs for PAL errors
# Test mcp__pal__* tools manually
# Verify PAL MCP tool signatures
```

**Solutions**:
1. **Check PAL MCP tool is working**: Test `mcp__pal__listmodels`
2. **Verify PAL response format** matches expected schema
3. **Check for PAL API errors** (if using remote API)
4. **Update PAL MCP server** to latest version

**Workaround**: Analysis completes with base assessment (no PAL enhancement)

---

### Fix Orchestration Issues

#### Fix Validation Fails After Max Retries

**Symptoms**:
- Fix applied but validation fails
- `retry_count: 2` (max retries exhausted)
- `status: "failed"`
- Revert command provided

**Diagnosis**:
```bash
# Check validation error messages
# Review attempted fixes in git log
# Run validation commands manually
```

**Common Causes**:
1. **Test dependencies missing**: `npm install` or `pip install` needed
2. **Lint config changed**: Pre-commit hooks updated
3. **Type errors**: TypeScript/mypy config stricter than expected
4. **Environment issues**: Tests pass locally, fail in CI

**Solutions**:
1. **Run revert command** (provided in error output)
2. **Fix dependencies**: Install missing packages
3. **Update validation commands**: Edit fix-validator.md
4. **Manual fix**: Apply fix manually with correct approach

---

#### File Conflicts During Parallel Execution

**Symptoms**:
- Multiple fixes target same file
- Git conflicts during commit
- `status: "failed"` for some fixes

**Diagnosis**:
```bash
# Check which findings target same files
# Review dependency analysis output
# Look for file_path conflicts in phase grouping
```

**Solutions**:
1. **Re-run with conflict detection**: Orchestrator should detect conflicts
2. **Manual grouping**: Use interactive mode to select fixes carefully
3. **Sequential execution**: Run conflicting fixes one at a time

**Prevention**: Fix orchestrator's Phase 1 does dependency analysis

---

#### Commits Created But Tests Fail

**Symptoms**:
- Git commits exist (`commit_hash` in output)
- Validation reports test failures
- Need to revert multiple commits

**Diagnosis**:
```bash
# List recent commits
git log --oneline -5

# Check which commits are from fix orchestrator
git log --grep "fix-orchestrator"

# Review test failures
pytest tests/ -v
```

**Solutions**:
```bash
# Revert all fix orchestrator commits from this session
git log --grep "fix-orchestrator" --since="1 hour ago" --format="%H" | xargs -I {} git revert {}

# Or use provided revert commands from each fix
# (Available in fix-phase-coordinator output)
```

---

### Validation Hook Issues

#### PostToolUse Hook Blocks Agent

**Symptoms**:
- Agent execution stops mid-workflow
- Hook validation error message
- Pydantic ValidationError in logs

**Diagnosis**:
```bash
# Check hook output in logs
# Look for Pydantic validation errors
# Review agent output format
```

**Common Causes**:
1. **Model schema mismatch**: Agent output doesn't match Pydantic model
2. **Missing required fields**: Agent forgot to include required field
3. **Invalid enum value**: Used wrong severity/confidence value
4. **Type mismatch**: String where int expected, etc.

**Solutions**:
1. **Fix agent output**: Update agent to match schema
2. **Update model**: If schema is wrong, update Pydantic model in `src/red_agent/models/`
3. **Check AGENT_TYPE_MAP**: Verify correct model mapped to agent path
4. **Temporarily disable hook**: Comment out hook in plugin.json (for debugging only)

---

#### Hook Not Triggering

**Symptoms**:
- Invalid agent output not caught
- Validation bypassed
- Errors only appear later in workflow

**Diagnosis**:
```bash
# Check hook is registered in plugin.json
# Verify hook file exists
# Look for hook execution in logs
```

**Solutions**:
1. **Register hook**: Add to plugin.json `hooks` array
2. **Check file path**: Verify `hooks/validate-agent-output.py` exists
3. **Verify event**: Ensure `event: "PostToolUse"` is correct
4. **Reload plugin**: Restart Claude Code to reload plugin config

---

### Context Engineering Issues

#### Agent Receives Too Much Context

**Symptoms**:
- Agent execution slow
- High token costs
- Context limit errors

**Diagnosis**:
```bash
# Review agent input size
# Check what's being passed to agent
# Measure context tiers
```

**Solutions**:
1. **Use appropriate context tier**: Switch from FULL to SELECTIVE or METADATA
2. **Filter inputs**: Pass only affected files, not all files
3. **Summarize**: Create summaries instead of passing full content
4. **Refactor**: Split large agent into smaller sub-agents

**Reference**: See `docs/ultrathink-architecture.md` for context tiers

---

#### Context Blowup in Multi-Agent Workflow

**Symptoms**:
- Later agents very slow
- Cumulative context growth
- Token costs exponential

**Diagnosis**:
```bash
# Measure context size at each stage
# Check if full outputs being passed
# Review agent input/output sizes
```

**Solutions**:
1. **Implement firewall pattern**: Isolate agents, don't pass full context
2. **Use structured snapshots**: Create minimal YAML snapshots
3. **Selective propagation**: Only pass what next agent needs
4. **Parallel execution**: Avoid sequential accumulation

**Reference**: See `docs/ultrathink-architecture.md` for patterns

---

### Plugin Configuration Issues

#### Plugin Not Loading

**Symptoms**:
- Commands not available
- Agents not found
- Plugin validation fails

**Diagnosis**:
```bash
# Validate plugin
claude plugin validate ./red-agent

# Check for JSON syntax errors
cat red-agent/.claude-plugin/plugin.json | jq .

# Verify file references
uv run python scripts/validate_plugin_schemas.py
```

**Solutions**:
1. **Fix JSON syntax**: Check for trailing commas, missing quotes
2. **Fix file paths**: Ensure all referenced files exist
3. **Update schema**: Match latest plugin.json schema
4. **Reinstall plugin**: Remove and re-add in Claude Code

---

#### Commands Work But Agents Don't Launch

**Symptoms**:
- Command executes
- No agent launched or wrong agent launched
- No output from expected agent

**Diagnosis**:
```bash
# Check agent path in command
# Verify agent file exists
# Look for agent path typos
```

**Solutions**:
1. **Fix agent path**: Update path in command `.md` file
2. **Check file extension**: Agents must be `.md` files
3. **Verify agent registration**: Check plugin.json `agents` array
4. **Case sensitivity**: Paths are case-sensitive on some systems

---

### Test Issues

#### Tests Failing After Model Changes

**Symptoms**:
- Pydantic model tests fail
- ValidationError in test output
- Tests passed before model changes

**Diagnosis**:
```bash
# Run specific test file
uv run pytest tests/test_pydantic_models.py -v

# Check what changed
git diff src/red_agent/models/
```

**Solutions**:
1. **Update test fixtures**: Match new model schema
2. **Fix model**: If model is wrong, revert changes
3. **Update test expectations**: Adjust tests for intentional changes
4. **Check imports**: Ensure new models exported from `__init__.py`

---

#### Pre-commit Hooks Failing

**Symptoms**:
- Git commit blocked
- Pre-commit validation errors
- Ruff, mypy, or schema validation fails

**Diagnosis**:
```bash
# Run pre-commit manually
uv run pre-commit run --all-files

# Run specific hook
uv run ruff check .
uv run mypy src/
```

**Solutions**:
```bash
# Auto-fix ruff issues
uv run ruff check --fix .
uv run ruff format .

# Fix mypy type issues manually

# Validate schemas
uv run python scripts/validate_plugin_schemas.py
```

---

## Debugging Techniques

### Enable Verbose Logging

For debugging agent execution:

```markdown
# Add to agent prompt (temporary)
## Debug Mode

Log all inputs and outputs:
- Input received: [dump YAML]
- Processing: [step-by-step]
- Output generated: [dump YAML]
```

### Test Agent Outputs Manually

```python
# Test Pydantic model validation
from red_agent.models import FixReaderOutput

test_output = {
    "finding_id": "RF-001",
    "parsed_intent": "Fix SQL injection",
    "context_hints": ["check auth.ts"],
}

try:
    validated = FixReaderOutput(**test_output)
    print("Valid:", validated)
except ValidationError as e:
    print("Invalid:", e)
```

### Validate Against Claude Code

```bash
# Validate plugin
claude plugin validate ./red-agent

# Expected output: "✔ Validation passed"
# If fails: Review error message for schema issues
```

### Run Isolated Agent Test

Create minimal test case:

```markdown
# test-agent.md
You are a test agent.

## Input
```yaml
test_input: "hello"
```

## Task
Echo the input back.

## Output
```yaml
test_output: "hello"
```
```

Launch manually to verify agent execution works.

---

## Performance Debugging

### Measure Context Usage

Add logging to measure context size:

```markdown
# In agent
## Context Measurement

Before processing:
- Input size: [estimate tokens]
- Files received: [count]
- Expected output size: [estimate]

After processing:
- Actual output size: [measure]
- Context tier used: [METADATA/SELECTIVE/FILTERED/FULL]
```

### Identify Bottlenecks

For slow workflows:

1. **Time each agent**: Add timestamps to outputs
2. **Measure context sizes**: Log input/output tokens
3. **Check parallel execution**: Are independent tasks sequential?
4. **Review retry loops**: Excessive retries?

### Optimize Context

If context is too large:

1. **Use higher tier**: FULL → SELECTIVE → METADATA
2. **Filter inputs**: Remove irrelevant files
3. **Summarize**: Pass summaries instead of full content
4. **Split agents**: Divide work into smaller sub-agents

---

## Getting Help

### Before Reporting Issues

1. **Check this troubleshooting guide**
2. **Validate plugin**: Run `claude plugin validate`
3. **Run tests**: Run `uv run pytest` to ensure baseline works
4. **Check logs**: Review agent output and error messages
5. **Minimize reproduction**: Create smallest possible test case

### Reporting Issues

Include:

1. **Plugin version**: Git commit hash
2. **Command used**: Full command line
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Full error text
6. **Minimal reproduction**: Smallest example that reproduces issue

### Useful Commands

```bash
# Validate plugin
claude plugin validate ./red-agent

# Run all tests
uv run pytest tests/ -v

# Run pre-commit checks
uv run pre-commit run --all-files

# Check git status
git status

# View recent commits
git log --oneline -10

# Check Pydantic models
uv run python -c "from red_agent.models import *; print('Models imported successfully')"
```

---

## References

- **PAL Integration**: `docs/pal-integration.md`
- **Ultrathink Architecture**: `docs/ultrathink-architecture.md`
- **Plugin Configuration**: `.claude-plugin/plugin.json`
- **Pydantic Models**: `src/red_agent/models/`
- **Validation Hooks**: `hooks/validate-agent-output.py`
- **Test Fixtures**: `tests/fixtures/`
- **CI/CD**: `.github/workflows/` (if applicable)
