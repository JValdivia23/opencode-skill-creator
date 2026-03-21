# Claude Skills Adaptation Guide

Guide for adapting Claude Code skills to work with OpenCode.

## Overview

Claude Code and OpenCode both use the same SKILL.md format, but there are important differences in:
- Tool availability
- Agent capabilities (subagents)
- Command structure
- File paths

**Good news**: Most Claude skills work with minimal or no changes in OpenCode.

---

## Compatibility Matrix

| Claude Skill | Compatibility | Notes |
|--------------|---------------|-------|
| **pdf** | ✓ High | Works as-is; some CLI tools may need installation |
| **git** | ✓ High | Works as-is |
| **web-search** | ⚠ Medium | May use different search APIs |
| **skill-creator** | ✗ Low | Highly specific to Claude's ecosystem |
| **eval-viewer** | ✗ Low | Depends on Claude's eval infrastructure |
| **testing** | ⚠ Medium | Test frameworks work; execution may differ |
| **api-integration** | ✓ High | API calls work the same |

---

## Key Differences

### 1. Tool Names

**Claude-specific tools that differ in OpenCode:**

| Claude Tool | OpenCode Equivalent | Notes |
|-------------|---------------------|-------|
| `claude` CLI | `opencode` | Different command structure |
| `Task` | `task` | Similar functionality |
| Subagents | Limited | OpenCode may not support full subagent spawning |
| `present_files` | Check availability | May not be available |

**What to look for in SKILL.md:**
```bash
# Search for Claude-specific tool references
grep -n "claude" SKILL.md
grep -n "Task" SKILL.md
grep -n "present_files" SKILL.md
```

### 2. File Paths

**Claude conventions:**
- `~/.claude/skills/` - Claude's skill directory
- `/tmp/claude-*` - Claude temporary files

**OpenCode conventions:**
- `~/.config/opencode/skills/` - OpenCode skill directory
- `~/.opencode/` - Project-local config

**Adaptation needed:**
```markdown
# Claude skill might say:
Save the skill to `~/.claude/skills/my-skill/`

# Change to:
Save the skill to `~/.config/opencode/skills/my-skill/`
```

### 3. Agent Capabilities

**Claude features that may differ:**

| Feature | Claude | OpenCode | Adaptation |
|---------|--------|----------|------------|
| Subagents | Full support | Varies | Use sequential tasks |
| Parallel execution | Yes | Check availability | May need sequential |
| Web browsing | Built-in | Via tools | Use webfetch tool |
| File watching | Yes | Check availability | May use polling |

### 4. Permission System

**Claude permissions (frontmatter):**
```yaml
---
permission:
  tool_name: allow
---
```

**OpenCode permissions (opencode.json):**
```json
{
  "permission": {
    "tool": {
      "*": "allow"
    }
  }
}
```

**Impact**: Skills mentioning permission setup need different instructions.

---

## Common Adaptations

### Adaptation 1: Remove Subagent Instructions

If a Claude skill heavily uses subagents:

**Before:**
```markdown
Spawn 5 subagents in parallel to process each file:
```

**After:**
```markdown
Process files sequentially:
1. Process file 1
2. Process file 2
3. etc.
```

### Adaptation 2: Update Path References

**Before:**
```markdown
Install to: `~/.claude/skills/`
```

**After:**
```markdown
Install to: `~/.config/opencode/skills/` (global)
or: `./.opencode/skills/` (project-local)
```

### Adaptation 3: Replace Claude-Specific Commands

**Before:**
```bash
claude -p "prompt text"
```

**After:**
```bash
# Check OpenCode equivalent or use direct tool calls
```

### Adaptation 4: Update Browser References

**Before:**
```markdown
Open the browser viewer...
```

**After:**
```markdown
If browser is available, open the viewer...
Otherwise, display results in conversation...
```

---

## Testing Adapted Skills

After adapting a Claude skill:

1. **Install the skill** using this skill-creator
2. **Test basic functionality** with a simple prompt
3. **Check for errors** in tool calls
4. **Verify all file operations** work correctly
5. **Test edge cases** mentioned in the skill

### Test Script

```bash
#!/bin/bash
# test_adapted_skill.sh

SKILL_NAME="$1"
TEST_PROMPT="${2:-Test the skill}"

echo "=== Testing Adapted Skill: $SKILL_NAME ==="
echo "Prompt: $TEST_PROMPT"
echo ""

# Check skill is installed
if [ ! -d "$HOME/.config/opencode/skills/$SKILL_NAME" ] && \
   [ ! -d "./.opencode/skills/$SKILL_NAME" ]; then
    echo "✗ Skill not installed"
    exit 1
fi

echo "✓ Skill is installed"
echo ""

# Check SKILL.md structure
echo "Checking SKILL.md..."
SKILL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME/SKILL.md"
[ -f "./.opencode/skills/$SKILL_NAME/SKILL.md" ] && \
  SKILL_PATH="./.opencode/skills/$SKILL_NAME/SKILL.md"

# Look for problematic patterns
echo ""
echo "Scanning for potential issues:"

# Check for claude references
CLAUDE_COUNT=$(grep -ic "claude" "$SKILL_PATH" 2>/dev/null || echo "0")
echo "  Claude references: $CLAUDE_COUNT"

# Check for subagent mentions
SUBAGENT_COUNT=$(grep -ic "subagent" "$SKILL_PATH" 2>/dev/null || echo "0")
echo "  Subagent mentions: $SUBAGENT_COUNT"

# Check for Claude paths
PATH_COUNT=$(grep -c "\.claude" "$SKILL_PATH" 2>/dev/null || echo "0")
echo "  Claude paths (.claude): $PATH_COUNT"

# Check for present_files
PRESENT_COUNT=$(grep -ic "present_files" "$SKILL_PATH" 2>/dev/null || echo "0")
echo "  present_files mentions: $PRESENT_COUNT"

echo ""
echo "=== Test Complete ==="
echo ""
echo "Manual testing required:"
echo "1. Start OpenCode"
echo "2. Try the prompt: $TEST_PROMPT"
echo "3. Verify the skill triggers"
echo "4. Check that all operations complete successfully"
```

---

## Skills That Work Without Changes

These Claude skills typically work in OpenCode without modification:

### Data Processing
- **pdf** - PDF manipulation (pypdf, pdfplumber work the same)
- **excel** - Spreadsheet operations
- **csv** - CSV processing
- **data-analysis** - Data analysis workflows

### Development
- **git** - Git workflows
- **testing** - Test frameworks
- **refactoring** - Code refactoring
- **documentation** - Documentation generation

### Utilities
- **web-search** - If using standard search APIs
- **api-integration** - API calling patterns
- **file-operations** - File manipulation

---

## Skills That Need Significant Adaptation

These skills are heavily Claude-specific:

### Evaluation Infrastructure
- **skill-creator** (Claude's version) - Uses Claude's eval system
- **eval-viewer** - Depends on Claude's viewer
- **benchmark** - Uses Claude-specific metrics

### Advanced Features
- Skills using `present_files` tool
- Skills with complex subagent orchestration
- Skills depending on Claude's browser automation

---

## Adaptation Checklist

When adapting a Claude skill:

- [ ] Search for "claude" references
- [ ] Search for "~/.claude" paths
- [ ] Check for subagent usage
- [ ] Check for `present_files` tool
- [ ] Verify tool names are OpenCode-compatible
- [ ] Update installation paths
- [ ] Test with a simple example
- [ ] Document any limitations

---

## Quick Reference: Adaptation Commands

```bash
# Find Claude references
grep -in "claude" SKILL.md

# Find Claude paths
grep -n "\.claude" SKILL.md

# Find subagent mentions
grep -in "subagent\|spawn.*agent" SKILL.md

# Find present_files
grep -in "present_files" SKILL.md

# Count occurrences
echo "Claude refs: $(grep -ic claude SKILL.md)"
echo "Subagent refs: $(grep -ic subagent SKILL.md)"
echo "Claude paths: $(grep -c '\.claude' SKILL.md)"
```

---

## Reporting Issues

If you find a Claude skill that doesn't work well in OpenCode:

1. Document the specific failure
2. Note which tools/commands failed
3. Check if it's a fundamental incompatibility
4. Consider creating an OpenCode-specific version
