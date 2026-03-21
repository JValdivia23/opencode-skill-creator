---
name: my-skill
description: Detailed description of what this skill does, when to use it, and what triggers should activate it. Be specific - this is how the agent decides to use this skill. Include keywords and scenarios that should trigger this skill.
license: MIT
compatibility: opencode
metadata:
  category: utility
  author: your-name
  version: "1.0.0"
---

# My Skill Name

Comprehensive guide for [what this skill does].

## Overview

This skill helps with [detailed description]. It provides [list of capabilities].

**Best for:** [Use case 1], [Use case 2], [Use case 3]

**Not suitable for:** [What this skill doesn't do]

## What I Do

- **Primary capability 1**: Description of what this does
- **Primary capability 2**: Description of what this does
- **Primary capability 3**: Description of what this does

## When to Use Me

### Activate This Skill When:

1. **Scenario 1**: User mentions [specific keywords/phrases]
2. **Scenario 2**: User asks for [specific task]
3. **Scenario 3**: User is working with [specific file type/concept]

### Don't Use This Skill When:

- [Scenario where another skill is better]
- [Task that should be handled differently]

## Prerequisites

Before using this skill, ensure you have:

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Quick Start

### Basic Example

```bash
# Simplest usage
command --input file.txt --output result.txt
```

### Common Workflow

```bash
# Step 1: Prepare
prepare-command

# Step 2: Execute
execute-command --option value

# Step 3: Verify
verify-command
```

## Detailed Usage

### Section 1: Topic A

Detailed explanation of topic A.

**Command:**
```bash
command-a --param1 value1 --param2 value2
```

**Parameters:**
- `--param1`: Description of param1
- `--param2`: Description of param2

**Example:**
```bash
# Example with real values
command-a --param1 "hello" --param2 42
```

### Section 2: Topic B

Detailed explanation of topic B.

**Code Example:**
```python
# Python example
def process_data(input_file):
    with open(input_file, 'r') as f:
        data = f.read()
    return transform(data)
```

### Section 3: Topic C

Detailed explanation of topic C.

## Advanced Features

### Feature 1

Advanced usage details.

```bash
# Advanced command
advanced-command --complex-option \
  --sub-option value \
  --another-option
```

### Feature 2

More advanced details.

## Common Tasks Reference

| Task | Command | Notes |
|------|---------|-------|
| Task 1 | `cmd1 --opt` | Common use case |
| Task 2 | `cmd2 --flag` | With specific option |
| Task 3 | `cmd3 <input>` | Batch processing |
| Task 4 | `cmd4` | Quick check |

## Workflows

### Workflow 1: Complete Process

Step-by-step workflow for a complete process.

1. **Step 1**: Description
   ```bash
   command-1
   ```

2. **Step 2**: Description
   ```bash
   command-2
   ```

3. **Step 3**: Description
   ```bash
   command-3
   ```

### Workflow 2: Alternative Approach

Alternative workflow for different scenario.

## Configuration

### Option 1: Environment Variables

```bash
export SKILL_SETTING_1="value"
export SKILL_SETTING_2="value"
```

### Option 2: Config File

Create `~/.config/my-skill/config.json`:

```json
{
  "setting1": "value",
  "setting2": "value"
}
```

## Best Practices

1. **Best Practice 1**: Explanation
2. **Best Practice 2**: Explanation
3. **Best Practice 3**: Explanation

## Important Warnings

⚠️ **Warning 1**: Important caution about something

⚠️ **Warning 2**: Another important caution

## Troubleshooting

### Issue 1: Common Problem

**Symptom:** Description of what goes wrong

**Solution:**
```bash
# Fix command
fix-command
```

### Issue 2: Another Problem

**Symptom:** Description

**Solution:** Step-by-step fix

## Examples

### Example 1: Simple Case

**Input:**
```
Sample input data
```

**Command:**
```bash
process --input sample.txt
```

**Output:**
```
Expected output
```

### Example 2: Complex Case

**Scenario:** Description of scenario

**Commands:**
```bash
# Multiple commands
step-1
data=$(step-2)
step-3 --data "$data"
```

**Result:** Expected outcome

## Integration with Other Tools

### Tool A

How this skill works with Tool A.

```bash
# Combined usage
skill-command | tool-a --process
```

### Tool B

How this skill works with Tool B.

## Performance Considerations

- Large files: Use `--stream` option
- Batch processing: Process in chunks of 100
- Memory usage: Monitor with `--verbose`

## Security Notes

- Never commit sensitive data
- Use environment variables for secrets
- Validate all inputs

## References

- **Detailed Guide**: `references/detailed-guide.md`
- **API Reference**: `references/api-reference.md`
- **Troubleshooting**: `references/troubleshooting.md`
- **Examples**: `references/examples.md`

## Changelog

### v1.0.0 (YYYY-MM-DD)
- Initial release
- Feature 1 implemented
- Feature 2 implemented

## License

[License information - see LICENSE.txt]
