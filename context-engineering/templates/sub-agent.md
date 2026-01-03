# [Name] Sub-Agent Template

Copy this template when creating coordinator-internal sub-agents.

---

```markdown
# [Name] Agent

You [one-sentence description of purpose].

## Purpose

[2-3 sentences describing what this agent does and why it exists.]

## Context Management

This agent receives [TIER] context.

## Input

You receive ([TIER] context):
- `[field_1]`: [description]
- `[field_2]`: [description]
- `[field_3]`: [description]

**NOT provided** (context isolation):
- [Explicit exclusion 1]
- [Explicit exclusion 2]
- [Explicit exclusion 3]

## Your Task

[Clear description of what this agent should do:]

1. **[Step 1]**: [What to do]
2. **[Step 2]**: [What to do]
3. **[Step 3]**: [What to do]

## [Domain-Specific Section]

[Tables, checklists, criteria, or other domain knowledge needed]

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |

## Output Format

\`\`\`yaml
[output_key]:
  agent: [agent-name]
  total_[items]: [count]

  [items]:
    - [field_1]: "[value]"
      [field_2]: [value]
      [field_3]:
        - "[nested value]"

  summary:
    [summary_field_1]: [value]
    [summary_field_2]: [value]

  [optional_section]:
    - "[observation or note]"
\`\`\`

## [Guidelines Section]

### When to [Action 1]

- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

### When to [Action 2]

- [Criterion 1]
- [Criterion 2]

## Quality Standards

- [Standard 1]
- [Standard 2]
- [Standard 3]
- Output ONLY the YAML structure
```
