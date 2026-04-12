# Detailed Installation Guide

Complete workflows for installing OpenCode skills from various sources.

## Table of Contents

1. [Pre-Installation Checklist](#pre-installation-checklist)
2. [Requirement Check Policy](#requirement-check-policy)
3. [Installing from Claude's Repository](#installing-from-claudes-repository)
4. [Installing from Arbitrary GitHub](#installing-from-arbitrary-github)
5. [Installing from Local Files](#installing-from-local-files)
6. [Post-Installation Verification](#post-installation-verification)
7. [Handling Supplementary Files](#handling-supplementary-files)

---

## Pre-Installation Checklist

Before installing any skill:

### 1. Check Current Directory

```bash
# Are you in a git repository?
git rev-parse --git-dir > /dev/null 2>&1 && echo "✓ In git repo" || echo "⚠ Not in git repo"

# Current working directory
pwd
```

### 2. Decide Installation Scope

**Choose global if:**
- Skill is universally useful (pdf, git workflows, etc.)
- You want it available in all projects
- No project-specific customizations needed

**Choose local if:**
- Skill is specific to this project
- You're testing a new skill
- Different projects need different versions
- You want to version-control the skill with the project

### 3. Check for Conflicts

```bash
SKILL_NAME="pdf"

# Check global
global_path="$HOME/.config/opencode/skills/$SKILL_NAME"
[ -d "$global_path" ] && echo "⚠ Already exists globally: $global_path" || echo "✓ No global conflict"

# Check local
local_path="./.opencode/skills/$SKILL_NAME"
[ -d "$local_path" ] && echo "⚠ Already exists locally: $local_path" || echo "✓ No local conflict"
```

### 4. Ensure Write Permissions

```bash
# Test global directory
touch "$HOME/.config/opencode/skills/.write_test" 2>/dev/null && \
  (rm "$HOME/.config/opencode/skills/.write_test" && echo "✓ Global directory writable") || \
  echo "✗ Cannot write to global directory"

# Test local directory
mkdir -p "./.opencode/skills" 2>/dev/null && echo "✓ Local directory writable" || echo "✗ Cannot write to local directory"
```

### 5. Requirement Discovery Plan (Before Final Success Report)

Before declaring installation success, plan to inspect skill documentation for dependencies and prerequisites.

Minimum files to scan (if present):
- `SKILL.md`
- `reference.md`
- `forms.md`
- `README*`

---

## Requirement Check Policy

When installing a skill from GitHub, requirement checking is mandatory.

### Required behavior

1. Download `SKILL.md` first, then scan for requirement indicators in skill docs.
2. Search for keywords: `requirements`, `prerequisites`, `dependencies`, `pip install`, `npm install`, `brew install`, `apt install`, `conda install`.
3. Verify requirements when possible (examples):
   - Command exists: `command -v <tool>`
   - Python package exists: `python3 -m pip show <package>`
   - Node CLI exists: `command -v <cli>`
4. Do not auto-install missing dependencies unless user explicitly asks.
5. If requirements are missing, report status as **installed with warnings**.
6. Include requirement-check output in the success/failure report.

### Suggested quick check block

```bash
REQ_PATTERN="requirements?|prerequisites?|dependenc|pip install|python -m pip|npm install|pnpm add|yarn add|brew install|apt(-get)? install|conda install"

for file in "$INSTALL_PATH/SKILL.md" "$INSTALL_PATH/reference.md" "$INSTALL_PATH/forms.md"; do
  [ -f "$file" ] || continue
  echo "=== Requirement scan: $(basename "$file") ==="
  grep -Ein "$REQ_PATTERN" "$file" || echo "No requirement lines found"
done
```

---

## Installing from Claude's Repository

**Source**: `https://github.com/anthropics/skills/tree/main/skills/`

### Step-by-Step Workflow

#### Step 1: Extract Skill Name

From the GitHub URL, extract the skill name:

```bash
# Example URL: https://github.com/anthropics/skills/tree/main/skills/pdf
# Skill name: pdf

SKILL_NAME="pdf"
echo "Installing skill: $SKILL_NAME"
```

#### Step 2: Check What's Available

```bash
# View the directory in browser or use GitHub API
curl -s "https://api.github.com/repos/anthropics/skills/contents/skills/$SKILL_NAME" | \
  grep -o '"name":"[^"]*"' | cut -d'"' -f4
```

Common files in Claude skills:
- `SKILL.md` (required)
- `reference.md` (detailed reference)
- `forms.md` (form handling guide)
- `LICENSE.txt` (license)
- `scripts/` (helper scripts directory)

#### Step 3: Create Installation Script

```bash
#!/bin/bash
# install_claude_skill.sh

SKILL_NAME="${1:-pdf}"
INSTALL_TYPE="${2:-global}"  # global or local

echo "=== Installing Claude Skill: $SKILL_NAME ==="
echo ""

# Set installation path
if [ "$INSTALL_TYPE" = "global" ]; then
    INSTALL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME"
else
    INSTALL_PATH="./.opencode/skills/$SKILL_NAME"
fi

REPO_URL="https://raw.githubusercontent.com/anthropics/skills/main/skills/$SKILL_NAME"

echo "Installation path: $INSTALL_PATH"
echo "Source: $REPO_URL"
echo ""

# Create directory
echo "Step 1: Creating directory..."
mkdir -p "$INSTALL_PATH"
echo "✓ Directory created"
echo ""

# Download SKILL.md
echo "Step 2: Downloading SKILL.md..."
curl -sL "$REPO_URL/SKILL.md" > "$INSTALL_PATH/SKILL.md"
if [ -f "$INSTALL_PATH/SKILL.md" ]; then
    echo "✓ SKILL.md downloaded ($(wc -c < "$INSTALL_PATH/SKILL.md") bytes)"
else
    echo "✗ Failed to download SKILL.md"
    exit 1
fi
echo ""

# Download reference.md
echo "Step 3: Checking for reference.md..."
HTTP_STATUS=$(curl -sL -o "$INSTALL_PATH/reference.md" -w "%{http_code}" "$REPO_URL/reference.md")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ reference.md downloaded ($(wc -c < "$INSTALL_PATH/reference.md") bytes)"
else
    rm -f "$INSTALL_PATH/reference.md"
    echo "⚠ No reference.md (HTTP $HTTP_STATUS)"
fi
echo ""

# Download forms.md
echo "Step 4: Checking for forms.md..."
HTTP_STATUS=$(curl -sL -o "$INSTALL_PATH/forms.md" -w "%{http_code}" "$REPO_URL/forms.md")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ forms.md downloaded ($(wc -c < "$INSTALL_PATH/forms.md") bytes)"
else
    rm -f "$INSTALL_PATH/forms.md"
    echo "⚠ No forms.md (HTTP $HTTP_STATUS)"
fi
echo ""

# Download LICENSE.txt
echo "Step 5: Checking for LICENSE.txt..."
HTTP_STATUS=$(curl -sL -o "$INSTALL_PATH/LICENSE.txt" -w "%{http_code}" "$REPO_URL/LICENSE.txt")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ LICENSE.txt downloaded"
else
    rm -f "$INSTALL_PATH/LICENSE.txt"
    echo "⚠ No LICENSE.txt (HTTP $HTTP_STATUS)"
fi
echo ""

# Check for scripts directory
echo "Step 6: Checking for scripts directory..."
SCRIPTS_CHECK=$(curl -sL -o /dev/null -w "%{http_code}" "$REPO_URL/scripts/")
if [ "$SCRIPTS_CHECK" = "200" ] || [ "$SCRIPTS_CHECK" = "301" ] || [ "$SCRIPTS_CHECK" = "302" ]; then
    echo "⚠ Scripts directory exists at $REPO_URL/scripts/"
    echo "  You may need to manually download scripts:"
    echo "  Visit: https://github.com/anthropics/skills/tree/main/skills/$SKILL_NAME/scripts"
else
    echo "✓ No scripts directory"
fi
echo ""

# Validate installation
echo "=== Validation ==="
echo ""

# Check frontmatter
if head -5 "$INSTALL_PATH/SKILL.md" | grep -q "^---"; then
    echo "✓ Frontmatter present"
    
    # Extract name
    FILE_NAME=$(grep "^name:" "$INSTALL_PATH/SKILL.md" | head -1 | sed 's/name: //' | tr -d ' ')
    echo "  Name: $FILE_NAME"
    
    # Check name matches
    if [ "$FILE_NAME" = "$SKILL_NAME" ]; then
        echo "✓ Name matches directory"
    else
        echo "⚠ Warning: Name in file ($FILE_NAME) ≠ directory ($SKILL_NAME)"
    fi
    
    # Check description
    if grep -q "^description:" "$INSTALL_PATH/SKILL.md"; then
        echo "✓ Description field present"
    else
        echo "⚠ Warning: No description field"
    fi
else
    echo "✗ No frontmatter found!"
fi
echo ""

# List installed files
echo "=== Installed Files ==="
ls -la "$INSTALL_PATH/"
echo ""

# Check for Claude references
echo "=== Claude Compatibility Check ==="
CLAUDE_REFS=$(grep -ic "claude" "$INSTALL_PATH/SKILL.md" 2>/dev/null || echo "0")
if [ "$CLAUDE_REFS" -gt 0 ]; then
    echo "⚠ Found $CLAUDE_REFS references to 'Claude' in SKILL.md"
    echo "  This skill may have been designed for Claude Code."
    echo "  Some features may need adaptation for OpenCode."
    echo ""
    echo "  References found:"
    grep -in "claude" "$INSTALL_PATH/SKILL.md" | head -5
else
    echo "✓ No obvious Claude-specific references"
fi
echo ""

echo "=== Installation Complete ==="
echo ""
echo "To use this skill, mention it in conversation or the agent will"
echo "automatically trigger it based on the description."
echo ""
echo "To verify it's working, restart OpenCode or wait for the"
echo "next agent initialization."
```

**Usage:**
```bash
chmod +x install_claude_skill.sh
./install_claude_skill.sh pdf global    # Install PDF skill globally
./install_claude_skill.sh pdf local     # Install PDF skill locally
```

---

## Installing from Arbitrary GitHub

For skills hosted in other repositories:

```bash
#!/bin/bash
# install_github_skill.sh

GITHUB_URL="$1"  # Full URL to skill directory
INSTALL_TYPE="${2:-global}"

# Parse URL components
# URL format: https://github.com/OWNER/REPO/tree/BRANCH/PATH/TO/SKILL
# Raw format: https://raw.githubusercontent.com/OWNER/REPO/BRANCH/PATH/TO/SKILL

# Extract components using sed/regex
OWNER=$(echo "$GITHUB_URL" | sed -n 's|https://github.com/\([^/]*\)/.*|\1|p')
REPO=$(echo "$GITHUB_URL" | sed -n 's|https://github.com/[^/]*/\([^/]*\)/.*|\1|p')
BRANCH=$(echo "$GITHUB_URL" | sed -n 's|https://github.com/[^/]*/[^/]*/tree/\([^/]*\)/.*|\1|p')
PATH=$(echo "$GITHUB_URL" | sed -n 's|https://github.com/[^/]*/[^/]*/tree/[^/]*/\(.*\)|\1|p')
SKILL_NAME=$(basename "$PATH")

echo "Owner: $OWNER"
echo "Repo: $REPO"
echo "Branch: $BRANCH"
echo "Path: $PATH"
echo "Skill name: $SKILL_NAME"

# Construct raw URL
RAW_URL="https://raw.githubusercontent.com/$OWNER/$REPO/$BRANCH/$PATH"
echo "Raw URL: $RAW_URL"

# Set installation path
if [ "$INSTALL_TYPE" = "global" ]; then
    INSTALL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME"
else
    INSTALL_PATH="./.opencode/skills/$SKILL_NAME"
fi

# Download files
mkdir -p "$INSTALL_PATH"
curl -sL "$RAW_URL/SKILL.md" > "$INSTALL_PATH/SKILL.md"

# Download other files as needed...
```

---

## Installing from Local Files

When you have skill files locally:

```bash
# Copy entire skill directory
SOURCE="/path/to/my-skill"
DEST="$HOME/.config/opencode/skills/my-skill"

cp -r "$SOURCE" "$DEST"

# Or copy specific files
mkdir -p "$DEST"
cp "$SOURCE/SKILL.md" "$DEST/"
cp "$SOURCE/reference.md" "$DEST/" 2>/dev/null || true
```

---

## Post-Installation Verification

Always verify after installation:

### Automated Verification Script

```bash
#!/bin/bash
# verify_skill.sh

SKILL_NAME="$1"
INSTALL_PATH="${2:-$HOME/.config/opencode/skills/$SKILL_NAME}"

if [ -z "$SKILL_NAME" ]; then
    echo "Usage: verify_skill.sh <skill-name> [path]"
    exit 1
fi

echo "=== Verifying Skill: $SKILL_NAME ==="
echo "Path: $INSTALL_PATH"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Directory exists
if [ -d "$INSTALL_PATH" ]; then
    echo "✓ Directory exists"
else
    echo "✗ Directory does not exist: $INSTALL_PATH"
    exit 1
fi

# Check 2: SKILL.md exists
if [ -f "$INSTALL_PATH/SKILL.md" ]; then
    echo "✓ SKILL.md exists"
else
    echo "✗ SKILL.md missing!"
    ((ERRORS++))
fi

# Check 3: File is readable
if [ -r "$INSTALL_PATH/SKILL.md" ]; then
    echo "✓ SKILL.md is readable"
else
    echo "✗ SKILL.md is not readable!"
    ((ERRORS++))
fi

# Check 4: Frontmatter exists
if head -1 "$INSTALL_PATH/SKILL.md" | grep -q "^---"; then
    echo "✓ Frontmarker present"
else
    echo "✗ No frontmatter found!"
    ((ERRORS++))
fi

# Check 5: Name field exists
FILE_NAME=$(grep "^name:" "$INSTALL_PATH/SKILL.md" 2>/dev/null | head -1 | sed 's/name: //' | tr -d ' ')
if [ -n "$FILE_NAME" ]; then
    echo "✓ Name field: $FILE_NAME"
    
    # Check 6: Name matches directory
    DIR_NAME=$(basename "$INSTALL_PATH")
    if [ "$FILE_NAME" = "$DIR_NAME" ]; then
        echo "✓ Name matches directory"
    else
        echo "⚠ Warning: Name ($FILE_NAME) ≠ directory ($DIR_NAME)"
        ((WARNINGS++))
    fi
else
    echo "✗ Missing name field!"
    ((ERRORS++))
fi

# Check 7: Description field exists
if grep -q "^description:" "$INSTALL_PATH/SKILL.md" 2>/dev/null; then
    DESC=$(grep "^description:" "$INSTALL_PATH/SKILL.md" | head -1 | sed 's/description: //')
    DESC_LEN=${#DESC}
    echo "✓ Description field present ($DESC_LEN chars)"
    
    if [ "$DESC_LEN" -gt 1024 ]; then
        echo "⚠ Warning: Description exceeds 1024 characters"
        ((WARNINGS++))
    fi
else
    echo "✗ Missing description field!"
    ((ERRORS++))
fi

# Check 8: Name format validation
if echo "$FILE_NAME" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'; then
    echo "✓ Name format is valid"
else
    echo "⚠ Warning: Name format may be invalid"
    echo "  Must be: lowercase alphanumeric with single hyphens"
    ((WARNINGS++))
fi

echo ""
echo "=== Results ==="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✓ All checks passed!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠ Passed with warnings"
    exit 0
else
    echo "✗ Failed with errors"
    exit 1
fi
```

---

## Handling Supplementary Files

Many skills include supplementary files that must be downloaded manually.

### Scripts Directory

If a skill has a `scripts/` directory:

```bash
# Method 1: Download via GitHub web interface
# Visit: https://github.com/anthropics/skills/tree/main/skills/NAME/scripts
# Click each file → Raw → Save

# Method 2: Clone and copy
git clone --depth 1 --filter=blob:none --sparse https://github.com/anthropics/skills.git /tmp/claude-skills
cd /tmp/claude-skills
git sparse-checkout set skills/$SKILL_NAME/scripts
cp -r skills/$SKILL_NAME/scripts/* ~/.config/opencode/skills/$SKILL_NAME/scripts/
rm -rf /tmp/claude-skills
```

### References Directory

```bash
# Similar to scripts - may need manual download
# Check: https://github.com/anthropics/skills/tree/main/skills/NAME/references/
```

### Assets Directory

```bash
# For images, fonts, etc.
# Download as needed based on skill documentation
```

---

## Summary

**Always:**
1. Check for conflicts before installing
2. Download ALL files (not just SKILL.md)
3. Validate after installation
4. Check for Claude-specific content
5. Verify the skill actually loads

**Never:**
1. Create empty files with the right name (agent will hallucinate it's installed)
2. Skip validation
3. Ignore supplementary files
4. Install without checking permissions
