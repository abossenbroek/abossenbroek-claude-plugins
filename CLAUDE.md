# Claude Code Plugins Repository

A collection of production-grade Claude Code plugins with strict validation infrastructure. This repository demonstrates best practices for plugin development with type-safe validation using Pydantic models.

**Plugins**: See `red-agent/CLAUDE.md` and `context-engineering/CLAUDE.md` for plugin-specific documentation.

## Critical Rules

These rules are non-negotiable. Violating them causes real problems.

### 1. Always Run Pre-commit Before Suggesting Completion

```bash
uv run pre-commit run --all-files
```

**Why**: Pre-commit catches ruff violations, JSON errors, and schema mismatches. A "complete" task with failing hooks wastes user time.

### 2. Always Run Tests After Code Changes

```bash
uv run pytest tests/ -v
```

**Why**: Comprehensive test coverage validates the entire infrastructure. Untested changes break silently.

### 3. Never Commit Without Verification

Before any commit:
1. Run pre-commit (fixes auto-fixable issues)
2. Run pytest (catches logic errors)
3. Stage only intended files

**Why**: This repo uses CI. Broken commits create noise and block PRs.

### 4. Use Pydantic Models for All Validation

Agent output validation MUST use Pydantic models. Do not create ad-hoc validation logic.

**Model locations**:
- Red-agent: `src/red_agent/models/`
- Context-engineering: `src/context_engineering/models/`

**Why**: Single source of truth. Manual validation diverges from the schema.

### 5. Validate Against Claude Code Before Push

Use `claude plugin validate` to validate schemas against Claude Code's internal validation:

```bash
# Validate a plugin
claude plugin validate ./red-agent

# Validate marketplace
claude plugin validate .

# Or run the pre-push hook manually
uv run python scripts/validate_against_claude_code.py
```

**Why**: This uses Claude Code's actual schema validation, catching issues before push. The pre-push hook runs this automatically.

---

## Development Workflow

### Setup

```bash
# Install dependencies (creates .venv automatically)
uv sync --all-extras

# Verify setup
uv run pytest tests/ -v
uv run pre-commit run --all-files
```

### Making Changes

1. **Before coding**: Read relevant test files to understand expected behavior
2. **While coding**: Follow existing patterns in the codebase
3. **After coding**: Run `uv run pytest` and `uv run pre-commit run --all-files`
4. **Before committing**: Verify all checks pass

### Git Workflow

This repo uses feature branches. Main branch is protected.

```bash
# Create feature branch
git checkout -b feature/description

# Make changes, run validation chain, then commit
git add -A
git commit -m "feat(plugin): description"

# Push and create PR
git push -u origin feature/description
gh pr create --title "Title" --body "Description"
```

**Conventional Commit Types**:
- `feat(plugin)`: New features, new agents, architectural improvements
- `fix(plugin)`: Bug fixes, broken validation, test fixes
- `refactor(plugin)`: Code restructuring without behavior change
- `docs(plugin)`: ONLY for README/changelog updates
- `test(plugin)`: Adding or modifying tests
- `chore(plugin)`: Dependency updates, config changes

**IMPORTANT**: Agent/prompt changes are `feat` or `fix`, NOT `docs`. Markdown files in `agents/`, `coordinator-internal/`, `commands/` are executable code, not documentation.

---

## Code Standards

### Python

| Rule | Enforcement |
|------|-------------|
| Python 3.12+ | `pyproject.toml` requires-python |
| Type hints on all functions | ruff PLR rules |
| No unused imports/variables | ruff F rules |
| Modern syntax (match, \|, etc.) | ruff UP rules |
| 88 character line length | ruff format |

### Ruff Configuration

Strict ruleset enabled. See `pyproject.toml` for full config. Key rules:
- `E`, `W`, `F`: Core Python errors
- `I`: Import sorting
- `B`: Bugbear (common bugs)
- `UP`: Pyupgrade (modern syntax)
- `PL`: Pylint rules
- `ARG`: Unused arguments
- `SIM`: Simplification opportunities

### Test Conventions

- Test files: `tests/test_*.py`
- Fixtures: `tests/conftest.py`
- Pattern: One test class per module/feature
- Naming: `test_<behavior>` for functions, `Test<Feature>` for classes

**Example**:
```python
class TestValidateAttackerOutput:
    def test_valid_output(self, valid_attacker_output):
        result = validate_attacker_output(valid_attacker_output)
        assert result.is_valid

    def test_missing_required_field(self):
        result = validate_attacker_output({})
        assert not result.is_valid
```

---

## Directory Structure

```
.
├── .claude-plugin/               # Marketplace manifest
│   └── marketplace.json          # Plugin registry for this repo
├── .claude/                      # Claude Code settings
│   └── settings.local.json       # Allowed permissions
├── red-agent/                    # Red team analysis plugin (see red-agent/CLAUDE.md)
│   ├── .claude-plugin/plugin.json
│   ├── agents/                   # Entry coordinators (firewall boundary)
│   ├── coordinator-internal/     # Sub-agents (isolated from main session)
│   ├── commands/                 # Slash commands
│   └── skills/                   # Reusable skill definitions
├── context-engineering/          # Context optimization plugin (see context-engineering/CLAUDE.md)
│   ├── .claude-plugin/plugin.json
│   ├── agents/                   # Entry coordinators (firewall boundary)
│   ├── coordinator-internal/     # Sub-agents + phase executors
│   ├── commands/                 # Slash commands
│   ├── hooks/                    # PostToolUse validation hooks
│   ├── scripts/                  # State/cache management CLIs
│   └── skills/                   # Reusable skill definitions
├── src/                          # Python package source
│   ├── red_agent/models/         # Pydantic models for red-agent
│   └── context_engineering/models/ # Pydantic models for context-engineering
├── schemas/                      # JSON schemas for config validation
├── scripts/                      # Repo-level validation scripts
└── tests/                        # pytest test suite (260+ tests)
```

**Note**: For plugin-specific architecture, commands, and patterns, refer to the respective `CLAUDE.md` files. This keeps documentation co-located with implementation.

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, ruff config, pytest config |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `src/*/models/` | Pydantic models (source of truth for validation) |
| `*/hooks/validate-agent-output.py` | PostToolUse hook for type-safe validation |
| `scripts/validate_plugin_schemas.py` | JSON schema validator for configs |
| `scripts/validate_against_claude_code.py` | Claude Code schema validation (pre-push) |
| `scripts/check_config_hygiene.py` | Hygiene checks (author emails, empty arrays, etc.) |
| `*/CLAUDE.md` | Plugin-specific documentation (architecture, patterns, rules) |

---

## Validation Architecture

### Four Layers of Validation

1. **Pre-commit (Development Time)**
   - `validate_plugin_schemas.py`: Validates against local JSON schemas
   - `check_config_hygiene.py`: Checks author emails, empty arrays, schema references
   - `validate_agent_files.py`: Verifies referenced agent/command files exist

2. **Pre-push (Claude Code Validation)**
   - `validate_against_claude_code.py`: Uses `claude plugin validate` for authoritative schema validation
   - Catches issues that local schemas might miss

3. **Pydantic Models (Runtime)**
   - Located in `red-agent/models/` and `context-engineering/models/`
   - Used by `validate_agent_output.py` to validate agent outputs
   - Provides type-safe validation with clear error messages

4. **Tests (CI)**
   - 165+ tests covering all validators
   - Run via `uv run pytest tests/ -v`

### PostToolUse Hook Output Format

All plugins use YAML format for hook decisions:

**Success**:
```yaml
decision: continue
```

**Failure**:
```yaml
decision: block
reason: |
  Detailed error message
  with field-level hints
```

**Rationale**: YAML is more LLM-native than JSON, handles multiline errors cleanly, and requires no escaping.

### PostToolUse Hook Standards (Established 2025-01)

All plugins should follow these standards for PostToolUse hooks:

#### Output Format
Hooks must return YAML (not JSON or exit codes):

**Success**:
```yaml
decision: continue
```

**Failure**:
```yaml
decision: block
reason: |
  Detailed error message
  with field-level hints
```

**Rationale**: YAML is more LLM-native, handles multiline errors cleanly, requires no escaping.

#### Error Message Format
Use `format_validation_error()` function in all hooks:

```python
def format_validation_error(error: dict[str, Any]) -> str:
    """Format Pydantic validation error with actionable hints."""
    location = ".".join(str(x) for x in error["loc"])
    message = error["msg"]
    error_type = error.get("type", "")

    formatted = f"- {location}: {message}"

    # Add context-specific hints
    if "missing" in error_type:
        formatted += f"\n  Hint: Add '{location}' field to output"
    elif "enum" in error_type or "literal" in error_type:
        formatted += "\n  Hint: Check valid values in model definition"
    elif "type_error.float" in error_type or "greater_than" in error_type:
        formatted += "\n  Hint: Value must be numeric in valid range"
    elif "string_too_short" in error_type:
        formatted += "\n  Hint: Field requires more content"

    return formatted
```

#### Model Imports
Hooks must import Pydantic models from `src/` (single source of truth):

```python
# Add src directory to path
SCRIPT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

# Import from centralized models
from plugin_name.models import ModelName
```

**Never duplicate models inline in hooks.**

#### Testing Requirements
All hooks must have:
- Output format tests (YAML parseability, continue/block decisions)
- Retry flow tests (validation failure → retry → success)
- Error message parsing tests (field paths, hints, actionability)

### When to Use Each

| Situation | Tool |
|-----------|------|
| Editing `plugin.json` or `marketplace.json` | Pre-commit runs automatically |
| Creating new agent output format | Add Pydantic model, then tests |
| Validating agent output at runtime | Use `validate_agent_output.py` |
| Checking if changes broke anything | Run `uv run pytest` |

---

## Common Workflows

### Standard Validation Chain

After making changes, run this validation sequence:

```bash
# 1. Run tests
uv run pytest tests/ -v

# 2. Run pre-commit hooks
uv run pre-commit run --all-files

# 3. Validate plugins against Claude Code
claude plugin validate ./red-agent
claude plugin validate ./context-engineering
```

All three must pass before committing.

### Add a New Pydantic Model

1. Create model in appropriate file under `src/*/models/`
2. Export from `src/*/models/__init__.py`
3. Add tests in `tests/test_*_models.py`
4. Run validation chain (above)

### Add a New Validator

1. Add validation function to appropriate script
2. Add tests with both valid and invalid inputs
3. Run: `uv run pytest -v && uv run pre-commit run --all-files`

### Fix a Failing Pre-commit

**Workflow**:
1. Run pre-commit to identify issues
2. Auto-fix what's possible (ruff, formatting)
3. Manually fix remaining issues
4. Re-run to verify

```bash
# See what's wrong
uv run pre-commit run --all-files

# Auto-fix ruff issues (most violations)
uv run ruff check --fix .
uv run ruff format .

# Re-run to verify - check if any issues remain
uv run pre-commit run --all-files

# If line-length issues remain (E501), manually fix:
# - Break long lines at logical points
# - Use parentheses for implicit line continuation
# - Keep strings readable
```

**Common Auto-Fixable Issues**:
- Unused imports (F401)
- Missing trailing commas (COM812)
- Import sorting (I001)
- Whitespace issues (W291, W293)

**Requires Manual Fix**:
- Line too long (E501) - requires judgment on where to break
- Complex logic issues (PLR0912, C901)
- Missing type hints (ANN)

### Add a New Plugin

1. Create directory: `new-plugin/`
2. Create manifest: `new-plugin/.claude-plugin/plugin.json`
3. Add to marketplace: `.claude-plugin/marketplace.json`
4. Run validation: `uv run pre-commit run --all-files`

---

## Anti-Patterns

### Do NOT

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Skip pre-commit | Pushes broken code | Always run before commit |
| Add validation logic outside Pydantic | Creates divergent schemas | Add to `red-agent/models/` |
| Guess plugin schema fields | May break on Claude Code update | Test by loading plugin in Claude Code |
| Use emojis in CLI output | Encoding issues in some terminals | Use ASCII: `[OK]`, `[ERROR]`, `[WARN]` |
| Call `sys.exit()` in library functions | Prevents error aggregation | Raise exceptions, handle in `main()` |
| Create tests without negative cases | Only catches "happy path" bugs | Test invalid inputs too |

### Common Mistakes

1. **Forgetting to export from `__init__.py`**: New models won't be importable
2. **Using `str` instead of `Enum` for validated fields**: Loses type safety
3. **Not running tests after refactoring**: Silent breakage
4. **Committing without running pre-commit**: CI will fail

---

## Decision Framework

When unsure how to proceed, use this framework:

### 1. Does an existing pattern apply?

Look for similar code in the repo. Follow established conventions.

### 2. Will this break existing tests?

Run `uv run pytest` early and often. Tests document expected behavior.

### 3. Is this a config change?

Test by loading the plugin in Claude Code to verify the schema is accepted.

### 4. Am I adding validation logic?

Use Pydantic models. Never create ad-hoc validation.

### 5. Should I spawn an agent with Task tool?

**YES - Spawn agents to prevent context pollution when:**
- Task requires multiple files/rounds of analysis
- Task has independent sub-tasks that can be parallelized
- Task involves complex multi-step workflows
- You're implementing a plan with compartmentalized fixes

**NO - Work directly when:**
- Task is a single straightforward edit
- You have all context needed in current session
- Task requires tight iteration/debugging loop

**Pattern**: Main session = thin orchestrator, agents = focused workers with minimal context

### 6. Should I break this into phases with multiple agents?

**YES - Use phase-based orchestration when:**
- Task has 5+ file modifications across different conceptual areas
- Clear sequential dependencies (Phase A must complete before Phase B)
- Significant parallelization opportunity (multiple independent sub-tasks)
- Need for centralized verification/aggregation at the end

**NO - Use simpler approaches when:**
- Task has 1-4 related file modifications
- All work can be done in parallel with no dependencies
- Task is exploratory/research-focused
- Single agent can handle the full context

**Phase-Based Pattern**:
```
Main Session (Orchestrator)
  ↓
Spawn Phase 1 (blocking) → Spawn Phases 2-5 (parallel)
  ↓                              ↓
File Agents                  File Agents (each phase)
```

**Example Decision Tree**:
- "Refactor validation hooks across 2 plugins" → Phase-based (Phase 1: refactor models, Phases 2-5: parallel format/test/docs changes)
- "Add new validation model" → Direct implementation (single conceptual change)
- "Fix bug in hook" → Direct implementation (focused scope)

### 7. Am I unsure about a schema field?

Check `sdk-tools.d.ts` in the Claude Code package for tool schemas. For plugin/marketplace schemas, test by loading in Claude Code.

### 8. Could this affect users?

Consider backwards compatibility. Avoid breaking changes without explicit request.

---

## Plugin Development Notes

### Claude Code Plugin Structure

Plugins consist of:
- `plugin.json`: Manifest with commands, agents, skills
- `commands/`: Slash commands (`.md` files)
- `agents/`: Agents launchable via Task tool
- `skills/`: Reusable skills

### Schema Validation

Claude Code provides `claude plugin validate` for pre-push validation:

```bash
# Validate plugin against Claude Code's internal schemas
claude plugin validate ./red-agent

# Validate marketplace
claude plugin validate .

# Run pre-push hook manually
uv run python scripts/validate_against_claude_code.py
```

**Validation layers:**
1. **Pre-commit**: Local JSON schema validation (`scripts/validate_plugin_schemas.py`)
2. **Pre-push**: Claude Code validation (`scripts/validate_against_claude_code.py`)
3. **Tool schemas**: `sdk-tools.d.ts` in @anthropic-ai/claude-code package

### Schema Discovery

The `sdk-tools.d.ts` file in the Claude Code npm package is auto-generated from internal JSON schemas:

```typescript
/* This file was automatically generated by json-schema-to-typescript.
 * DO NOT MODIFY IT BY HAND. Instead, modify the source JSONSchema file... */
```

**Location**: `~/.local/share/nvm/*/lib/node_modules/@anthropic-ai/claude-code/sdk-tools.d.ts`

This is the canonical reference for tool input schemas (AskUserQuestion, Bash, etc.). Plugin/marketplace schemas are not exported but are validated by `claude plugin validate`.

**Schema patterns discovered via validation:**
- Marketplace description: Use `metadata.description`, not top-level `description`
- Agent paths: Must be `.md` files (directories not supported)
- Commands: Can be object with `source` property or array of paths

---

## Agent Orchestration Patterns

### When Executing Complex Plans

For multi-fix implementations (like architectural refactors):

**Orchestration Pattern**:
1. **Main Session** = Thin orchestrator (routing only, minimal logic)
2. **Implementation Agent** per fix:
   - Receives minimal context (fix spec + file paths)
   - Creates/modifies files
   - Commits frequently (`wip: description`)
   - Returns completion status
3. **Validation Agent** after each fix:
   - Receives success criteria + test commands
   - Runs validation chain
   - Returns PASS/FAIL + specific issues
4. **Remediation Agent** if validation fails:
   - Max 2 rounds before escalating to user
   - Gets specific issues to fix

**Dependency Management**:
- Identify parallel vs sequential fixes
- Launch independent fixes in parallel (single message, multiple Task calls)
- Wait for dependencies before launching dependent fixes

**Context Reduction**:
- Each agent gets ONLY what it needs (not full codebase)
- Use file references/IDs instead of full content
- State/cache systems for data sharing between agents

### Parallel Agent Spawning

```python
# CORRECT - Multiple agents in one message (parallel)
"I'll spawn 3 agents in parallel"
<Task for fix-1>
<Task for fix-2>
<Task for fix-3>

# WRONG - Sequential spawning (slower)
"Let me spawn agent 1"
<Task for fix-1>
[wait for response]
"Now agent 2"
<Task for fix-2>
```

### Multi-Agent Orchestration for Complex Multi-Phase Tasks

For tasks requiring multiple coordinated phases (like refactoring across plugins, comprehensive testing suites, or documentation updates):

**Pattern**: Orchestrator → Phase Agents → File Agents

1. **Orchestrator Agent** (main session):
   - Thin coordinator that spawns phase agents
   - Monitors for permission blocks
   - Aggregates results
   - Runs verification checklist

2. **Phase Agents** (spawned by orchestrator):
   - One agent per independent phase
   - Each phase spawns its own file-specific agents
   - Phases with dependencies run sequentially
   - Phases without dependencies run in parallel

3. **File Agents** (spawned by phase agents):
   - One agent per file modification
   - Spawn in parallel within each phase
   - Focused, single-purpose modifications

**Dependency Management**:
- Identify which phases depend on others
- Sequential: Phase 1 → wait → Phase 2
- Parallel: Phases 2, 3, 4, 5 spawn together (single message, multiple Task calls)

**Example Structure**:
```
Orchestrator
├── Phase 1 (Sequential - blocks others)
├── Phase 2 (Parallel) ─┬─ file-agent-1
│                        └─ file-agent-2
├── Phase 3 (Parallel) ─┬─ file-agent-3
│                        └─ file-agent-4
└── Phase 4 (Parallel)
```

**When to Use**:
- Tasks involving 5+ file modifications across multiple conceptual areas
- Tasks with clear phase boundaries and some dependencies
- Tasks where parallelization significantly reduces execution time

**Permission Handling**:
- Each phase/file agent reports permission blocks immediately
- Orchestrator aggregates and alerts user
- Check `.claude/settings.local.json` for pre-approved permissions before alerting

**Before Alerting User About Permissions**:
1. Check `.claude/settings.local.json` for pre-approved permissions:
```json
{
  "allowedToolPatterns": [
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Edit",
    "Write"
  ]
}
```

2. Only alert if permission is NOT in allowedToolPatterns

3. If blocked by new permission:
   - Report which agent/phase was blocked
   - Report which specific file/operation needs permission
   - Report required permission pattern to add

**Pattern**: Check local settings → Use approved permissions → Alert only for new ones

## Quick Reference

```bash
# Install/update dependencies
uv sync --all-extras

# Standard validation chain (run after changes)
uv run pytest tests/ -v
uv run pre-commit run --all-files
claude plugin validate ./red-agent
claude plugin validate ./context-engineering

# Fix ruff issues
uv run ruff check --fix . && uv run ruff format .

# Create commit (use correct type!)
git add -A && git commit -m "feat(plugin): description"

# Push (triggers pre-push Claude Code validation)
git push && gh pr create
```
