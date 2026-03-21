# Troubleshooting Guide

Common issues when installing or using OpenCode skills and their solutions.

## Table of Contents

1. [Skill Not Appearing](#skill-not-appearing)
2. [Permission Errors](#permission-errors)
3. [Validation Failures](#validation-failures)
4. [Name Conflicts](#name-conflicts)
5. [Claude-Specific Issues](#claude-specific-issues)
6. [Loading Errors](#loading-errors)

---

## Skill Not Appearing

### Symptom
Installed a skill but it doesn't show up in `available_skills`.

### Diagnostic Steps

```bash
# 1. Verify the skill is installed
echo "=== Global Skills ==="
ls -la ~/.config/opencode/skills/

echo ""
echo "=== Local Skills ==="
ls -la .opencode/skills/ 2>/dev/null || echo "No local .opencode directory"
```

### Common Causes & Solutions

#### Cause 1: SKILL.md Missing or Wrong Name

```bash
# Check if SKILL.md exists
ls ~/.config/opencode/skills/my-skill/

# If it's named differently:
mv ~/.config/opencode/skills/my-skill/skill.md \
   ~/.config/opencode/skills/my-skill/SKILL.md
```

#### Cause 2: Frontmatter Missing

```bash
# Check first few lines
head -10 ~/.config/opencode/skills/my-skill/SKILL.md

# Should start with:
# ---
# name: my-skill
# description: ...
# ---
```

**Fix:** Add proper frontmatter:
```yaml
---
name: my-skill
description: What this skill does
---
```

#### Cause 3: Name Mismatch

```bash
# Check name in file vs directory
FILE_NAME=$(grep "^name:" ~/.config/opencode/skills/my-skill/SKILL.md | sed 's/name: //')
DIR_NAME=$(basename ~/.config/opencode/skills/my-skill)
echo "File says: $FILE_NAME"
echo "Directory is: $DIR_NAME"
```

**Fix:** Ensure they match. Rename directory OR update name in file.

#### Cause 4: File Permissions

```bash
# Check permissions
ls -l ~/.config/opencode/skills/my-skill/SKILL.md

# Should show: -rw-r--r-- or similar (readable)

# Fix permissions:
chmod 644 ~/.config/opencode/skills/my-skill/SKILL.md
```

#### Cause 5: OpenCode Not Reloaded

**Solution:** Skills are loaded at agent initialization.
- Restart OpenCode session
- Or wait for next agent initialization

---

## Permission Errors

### Symptom
Cannot write to skill directory or permission denied.

### Solutions

#### Global Installation Permission Denied

```bash
# Check directory ownership
ls -ld ~/.config/opencode/skills/

# If owned by root or different user:
# Option 1: Change ownership
sudo chown -R $(whoami) ~/.config/opencode/skills/

# Option 2: Use local installation instead
mkdir -p .opencode/skills/
# Install skill locally
```

#### Create Directory if Missing

```bash
# Create with proper permissions
mkdir -p ~/.config/opencode/skills
chmod 755 ~/.config/opencode/skills
```

---

## Validation Failures

### Symptom
Skill installed but validation fails.

### Name Validation

**Error:** `Invalid skill name format`

**Rules:**
- 1-64 characters
- Lowercase alphanumeric
- Single hyphens only (no consecutive `--`)
- Cannot start/end with hyphen
- Regex: `^[a-z0-9]+(-[a-z0-9]+)*$`

**Valid names:**
- `pdf`
- `git-workflow`
- `data-processor-v2`

**Invalid names:**
- `PDF` (uppercase)
- `my--skill` (double hyphen)
- `-skill` (starts with hyphen)
- `skill-` (ends with hyphen)
- `my_skill` (underscore)
- `my skill` (space)

### Description Validation

**Error:** `Description missing or too long`

**Rules:**
- Required field
- 1-1024 characters

**Fix:**
```yaml
---
name: my-skill
description: This is a valid description between 1 and 1024 characters
---
```

---

## Name Conflicts

### Symptom
Skill already exists with same name.

### Solutions

#### Option 1: Overwrite

```bash
# Backup first
cp -r ~/.config/opencode/skills/conflict-skill \
   ~/.config/opencode/skills/conflict-skill.backup

# Remove old
rm -rf ~/.config/opencode/skills/conflict-skill

# Install new
# ... install commands ...
```

#### Option 2: Use Different Name

```bash
# Install with modified name
mkdir -p ~/.config/opencode/skills/my-skill-v2
curl ... > ~/.config/opencode/skills/my-skill-v2/SKILL.md

# Update name in file
sed -i '' 's/name: my-skill/name: my-skill-v2/' \
  ~/.config/opencode/skills/my-skill-v2/SKILL.md
```

#### Option 3: Install Locally

```bash
# Keep global version, install different version locally
mkdir -p .opencode/skills/my-skill
curl ... > .opencode/skills/my-skill/SKILL.md
```

---

## Claude-Specific Issues

### Symptom
Claude skill references tools/commands that don't exist in OpenCode.

### Common Issues

#### Issue 1: `claude` CLI Command

**Claude skill says:**
```bash
claude -p "prompt"
```

**OpenCode equivalent:**
May not exist. Use direct tool calls or ask user for OpenCode-specific method.

**Workaround:**
```markdown
## Using with OpenCode
Note: This skill references `claude -p` which is Claude-specific.
In OpenCode, execute the task directly or use available tools.
```

#### Issue 2: `present_files` Tool

**Claude skill says:**
```markdown
Use the `present_files` tool to show results...
```

**OpenCode status:** Check if tool is available.

**Workaround:**
```markdown
## File Presentation
In Claude Code: Use `present_files` tool
In OpenCode: Files are saved to the specified path. Check the output location.
```

#### Issue 3: Subagent Spawning

**Claude skill says:**
```markdown
Spawn 5 subagents to process in parallel...
```

**OpenCode limitation:** Subagent support varies.

**Adaptation:**
```markdown
## Execution Strategy
This skill uses subagents for parallel processing.
In OpenCode: Tasks will be executed sequentially or as supported by your environment.
```

#### Issue 4: Browser Automation

**Claude skill says:**
```markdown
Open browser and navigate to...
```

**OpenCode:** Browser availability varies.

**Workaround:**
```markdown
## Browser Steps
If browser is available:
1. Open http://localhost:PORT
2. ...

If headless environment:
Results are saved to: /path/to/output
```

---

## Loading Errors

### Symptom
Error messages when skill tries to load.

### Debug Mode

Enable verbose output:

```bash
# Check OpenCode debug options
opencode --help | grep -i debug

# Or check config
cat ~/.config/opencode/opencode.json | grep -i verbose
```

### Common Loading Errors

#### Error: `Skill not found`

**Check:**
1. File exists: `ls ~/.config/opencode/skills/name/SKILL.md`
2. Name matches directory
3. Frontmatter is valid YAML

#### Error: `Invalid frontmatter`

**Fix:**
```bash
# Check YAML syntax
cat ~/.config/opencode/skills/my-skill/SKILL.md | head -20

# Must have:
# ---
# name: my-skill
# description: something
# ---
# (no extra spaces before ---)
```

#### Error: `Permission denied`

**Fix:**
```bash
# Check opencode.json permissions
cat ~/.config/opencode/opencode.json | grep -A 10 '"permission"'

# May need to add:
# {
#   "permission": {
#     "skill": {
#       "*": "allow"
#     }
#   }
# }
```

---

## Diagnostic Script

```bash
#!/bin/bash
# diagnose_skill.sh

SKILL_NAME="$1"

echo "=== Skill Diagnostic Tool ==="
echo "Checking skill: $SKILL_NAME"
echo ""

# Find skill location
GLOBAL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME"
LOCAL_PATH="./.opencode/skills/$SKILL_NAME"

if [ -d "$GLOBAL_PATH" ]; then
    SKILL_PATH="$GLOBAL_PATH"
    echo "✓ Found globally: $SKILL_PATH"
elif [ -d "$LOCAL_PATH" ]; then
    SKILL_PATH="$LOCAL_PATH"
    echo "✓ Found locally: $SKILL_PATH"
else
    echo "✗ Skill not found!"
    echo ""
    echo "Searched:"
    echo "  $GLOBAL_PATH"
    echo "  $LOCAL_PATH"
    exit 1
fi

echo ""
echo "=== File Structure ==="
ls -la "$SKILL_PATH/"

echo ""
echo "=== SKILL.md Content (first 30 lines) ==="
head -30 "$SKILL_PATH/SKILL.md"

echo ""
echo "=== Validation Checks ==="

# Check 1: File exists
[ -f "$SKILL_PATH/SKILL.md" ] && echo "✓ SKILL.md exists" || echo "✗ SKILL.md missing"

# Check 2: Frontmatter
head -1 "$SKILL_PATH/SKILL.md" | grep -q "^---" && echo "✓ Has frontmatter" || echo "✗ No frontmatter"

# Check 3: Name field
if grep -q "^name:" "$SKILL_PATH/SKILL.md" 2>/dev/null; then
    NAME=$(grep "^name:" "$SKILL_PATH/SKILL.md" | head -1 | sed 's/name: //' | tr -d ' ')
    echo "✓ Name field: $NAME"
    
    if [ "$NAME" = "$SKILL_NAME" ]; then
        echo "✓ Name matches directory"
    else
        echo "⚠ Name mismatch: file='$NAME' dir='$SKILL_NAME'"
    fi
else
    echo "✗ No name field"
fi

# Check 4: Description
if grep -q "^description:" "$SKILL_PATH/SKILL.md" 2>/dev/null; then
    DESC=$(grep "^description:" "$SKILL_PATH/SKILL.md" | head -1 | sed 's/description: //')
    echo "✓ Description: ${#DESC} chars"
else
    echo "✗ No description field"
fi

# Check 5: Name format
if echo "$NAME" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'; then
    echo "✓ Name format valid"
else
    echo "⚠ Name format may be invalid"
fi

# Check 6: Permissions
[ -r "$SKILL_PATH/SKILL.md" ] && echo "✓ File readable" || echo "✗ File not readable"
[ -w "$SKILL_PATH/SKILL.md" ] && echo "✓ File writable" || echo "⚠ File not writable"

echo ""
echo "=== Claude-Specific Check ==="
CLAUDE_REFS=$(grep -ic "claude" "$SKILL_PATH/SKILL.md" 2>/dev/null || echo "0")
if [ "$CLAUDE_REFS" -gt 0 ]; then
    echo "⚠ Found $CLAUDE_REFS Claude references"
    echo "  This may be a Claude-specific skill"
else
    echo "✓ No obvious Claude references"
fi

echo ""
echo "=== Recommendations ==="

# Provide recommendations based on findings
if [ ! -f "$SKILL_PATH/SKILL.md" ]; then
    echo "• Create SKILL.md file"
fi

if ! head -1 "$SKILL_PATH/SKILL.md" 2>/dev/null | grep -q "^---"; then
    echo "• Add YAML frontmatter with name and description"
fi

if [ "$CLAUDE_REFS" -gt 0 ]; then
    echo "• Review for Claude-specific content that may need adaptation"
fi

echo ""
echo "=== Diagnostic Complete ==="
```

---

## Getting Help

If issues persist:

1. **Check documentation**: OpenCode docs at https://opencode.ai/docs/
2. **Validate skill**: Run the diagnostic script above
3. **Test minimal example**: Create a simple test skill
4. **Check permissions**: Verify file and directory permissions
5. **Restart OpenCode**: Some changes require session restart

---

## Quick Fixes

```bash
# Fix 1: Skill not appearing
ls ~/.config/opencode/skills/my-skill/SKILL.md  # Verify exists
head -5 ~/.config/opencode/skills/my-skill/SKILL.md  # Verify frontmatter

# Fix 2: Permission denied
chmod 644 ~/.config/opencode/skills/my-skill/SKILL.md
chmod 755 ~/.config/opencode/skills/my-skill/

# Fix 3: Name mismatch
# Either rename directory:
mv ~/.config/opencode/skills/old-name ~/.config/opencode/skills/new-name
# Or edit file:
sed -i '' 's/name: old-name/name: new-name/' ~/.config/opencode/skills/old-name/SKILL.md

# Fix 4: Reset skill
rm -rf ~/.config/opencode/skills/my-skill
# Then reinstall
```
