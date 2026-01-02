# Claude Code Plugins Repository

A collection of Claude Code plugins with strict validation infrastructure. This repository demonstrates best practices for plugin development with type-safe validation using Pydantic models.

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

**Why**: 79 tests validate the entire validation infrastructure. Untested changes break silently.

### 3. Never Commit Without Verification

Before any commit:
1. Run pre-commit (fixes auto-fixable issues)
2. Run pytest (catches logic errors)
3. Stage only intended files

**Why**: This repo uses CI. Broken commits create noise and block PRs.

### 4. Use Pydantic Models for All Validation

Agent output validation MUST use the Pydantic models in `red-agent/models/`. Do not create ad-hoc validation logic.

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

# Make changes, then commit
git add -A
git commit -m "Short description of change"

# Push and create PR
git push -u origin feature/description
gh pr create --title "Title" --body "Description"
```

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
├── .claude-plugin/          # Marketplace manifest
│   └── marketplace.json     # Plugin registry for this repo
├── .claude/                  # Claude Code settings
│   └── settings.local.json  # Allowed permissions
├── red-agent/               # Red team analysis plugin
│   ├── .claude-plugin/      # Plugin manifest
│   ├── agents/              # Entry-point agents (launched by Task tool)
│   ├── commands/            # Slash commands (user-invocable)
│   ├── coordinator-internal/# Sub-agents (NOT directly invocable)
│   ├── models/              # Pydantic models for validation
│   ├── scripts/             # Python validation tools
│   └── skills/              # Reusable skill definitions
├── schemas/                 # JSON schemas for config validation
├── scripts/                 # Repo-level validation scripts
└── tests/                   # pytest test suite
```

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, ruff config, pytest config |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `red-agent/models/` | Pydantic models (source of truth for validation) |
| `red-agent/scripts/validate_agent_output.py` | Runtime validator for agent outputs |
| `scripts/validate_plugin_schemas.py` | JSON schema validator for configs |
| `scripts/validate_against_claude_code.py` | Claude Code schema validation (pre-push) |
| `scripts/check_config_hygiene.py` | Hygiene checks (author emails, empty arrays, etc.) |

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
   - Located in `red-agent/models/`
   - Used by `validate_agent_output.py` to validate agent outputs
   - Provides type-safe validation with clear error messages

4. **Tests (CI)**
   - 165+ tests covering all validators
   - Run via `uv run pytest tests/ -v`

### When to Use Each

| Situation | Tool |
|-----------|------|
| Editing `plugin.json` or `marketplace.json` | Pre-commit runs automatically |
| Creating new agent output format | Add Pydantic model, then tests |
| Validating agent output at runtime | Use `validate_agent_output.py` |
| Checking if changes broke anything | Run `uv run pytest` |

---

## Common Tasks

### Add a New Pydantic Model

1. Create model in appropriate file under `red-agent/models/`
2. Export from `red-agent/models/__init__.py`
3. Add tests in `tests/test_pydantic_models.py`
4. Run tests: `uv run pytest tests/test_pydantic_models.py -v`

### Add a New Validator

1. Add validation function to appropriate script
2. Add tests with both valid and invalid inputs
3. Run: `uv run pytest -v && uv run pre-commit run --all-files`

### Fix a Failing Pre-commit

```bash
# See what's wrong
uv run pre-commit run --all-files

# Auto-fix ruff issues
uv run ruff check --fix .
uv run ruff format .

# Re-run to verify
uv run pre-commit run --all-files
```

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

### 5. Am I unsure about a schema field?

Check `sdk-tools.d.ts` in the Claude Code package for tool schemas. For plugin/marketplace schemas, test by loading in Claude Code.

### 6. Could this affect users?

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

## Quick Reference

```bash
# Install/update dependencies
uv sync --all-extras

# Run all tests
uv run pytest tests/ -v

# Run pre-commit
uv run pre-commit run --all-files

# Validate against Claude Code (runs on push)
uv run python scripts/validate_against_claude_code.py
# or directly:
claude plugin validate ./red-agent

# Fix ruff issues
uv run ruff check --fix . && uv run ruff format .

# Create commit
git add -A && git commit -m "message"

# Push (triggers pre-push Claude Code validation)
git push && gh pr create
```
