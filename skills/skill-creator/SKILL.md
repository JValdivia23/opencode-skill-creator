---
name: skill-creator
description: Install, manage, and create OpenCode skills. Use this when the user wants to install a skill from GitHub (especially Claude's skills repository), set up a new skill locally, modify an existing skill, or troubleshoot skill loading issues. This skill guides proper installation, validation, and Claude-to-OpenCode adaptation.
version: 1.0.0
---

# Skill Creator

A comprehensive guide for installing, managing, and creating OpenCode skills.

## What I Do

- **Install skills** from GitHub repositories (especially Claude's skills)
- **Create new skills** from templates
- **Validate** skill structure and frontmatter
- **Adapt** Claude skills for OpenCode compatibility
- **Manage** installed skills (list, update, remove)
- **Troubleshoot** skill loading issues

## Quick Start

### Install a Skill from Claude's Repository

```bash
# Install PDF skill globally (available in all projects)
mkdir -p ~/.config/opencode/skills/pdf
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md \
  > ~/.config/opencode/skills/pdf/SKILL.md
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/reference.md \
  > ~/.config/opencode/skills/pdf/reference.md 2>/dev/null || echo "No reference.md"
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/LICENSE.txt \
  > ~/.config/opencode/skills/pdf/LICENSE.txt 2>/dev/null || echo "No LICENSE.txt"

# Verify installation
ls -la ~/.config/opencode/skills/pdf/
```

### Install a Skill in Current Project Only

```bash
# Install PDF skill locally (only in this project)
mkdir -p .opencode/skills/pdf
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md \
  > .opencode/skills/pdf/SKILL.md
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/reference.md \
  > .opencode/skills/pdf/reference.md 2>/dev/null || echo "No reference.md"
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/LICENSE.txt \
  > .opencode/skills/pdf/LICENSE.txt 2>/dev/null || echo "No LICENSE.txt"

# Verify installation
ls -la .opencode/skills/pdf/
```

### Create a New Skill from Template

```bash
# Copy basic template
cp ~/.config/opencode/skills/skill-creator/references/templates/basic-skill.md \
  ~/.config/opencode/skills/my-skill/SKILL.md

# Edit and customize
```

## Installation Methods

### Method 1: From Claude's Skills Repository (Recommended)

Claude's skills are at: `https://github.com/anthropics/skills/tree/main/skills/`

**Step 1**: Identify the skill name from the URL
- URL: `https://github.com/anthropics/skills/tree/main/skills/pdf`
- Skill name: `pdf`

**Step 2**: Download all skill files

```bash
SKILL_NAME="pdf"
INSTALL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME"
REPO_URL="https://raw.githubusercontent.com/anthropics/skills/main/skills/$SKILL_NAME"

# Create directory
mkdir -p "$INSTALL_PATH"

# Download SKILL.md (required)
echo "Downloading SKILL.md..."
curl -sL "$REPO_URL/SKILL.md" > "$INSTALL_PATH/SKILL.md"

# Download reference.md (optional but common)
echo "Checking for reference.md..."
curl -sL "$REPO_URL/reference.md" > "$INSTALL_PATH/reference.md" 2>/dev/null \
  && echo "✓ reference.md downloaded" || echo "⚠ No reference.md"

# Download LICENSE.txt (optional)
echo "Checking for LICENSE.txt..."
curl -sL "$REPO_URL/LICENSE.txt" > "$INSTALL_PATH/LICENSE.txt" 2>/dev/null \
  && echo "✓ LICENSE.txt downloaded" || echo "⚠ No LICENSE.txt"

# Check for scripts directory
echo "Checking for scripts..."
curl -sL "$REPO_URL/scripts/" > /dev/null 2>&1 \
  && echo "⚠ Scripts directory exists - manual download needed" || echo "No scripts directory"

# List what we have
echo ""
echo "Installed files:"
ls -la "$INSTALL_PATH/"
```

**Step 3**: Validate the installation

```bash
# Check frontmatter
grep -A 5 "^---" "$INSTALL_PATH/SKILL.md" | head -10

# Verify name matches directory
SKILL_FILE_NAME=$(grep "^name:" "$INSTALL_PATH/SKILL.md" | head -1 | sed 's/name: //' | tr -d ' ')
echo "Skill name in file: $SKILL_FILE_NAME"
echo "Directory name: $SKILL_NAME"
[ "$SKILL_FILE_NAME" = "$SKILL_NAME" ] && echo "✓ Names match" || echo "⚠ Names don't match!"
```

**Step 4**: Check for Claude-specific content

```bash
# Search for potential Claude-specific references
echo "Checking for Claude-specific content..."
grep -i "claude" "$INSTALL_PATH/SKILL.md" && echo "⚠ Found Claude references - may need adaptation" || echo "✓ No obvious Claude references"
```

### Method 2: From Any GitHub Repository

```bash
# Format: github.com/OWNER/REPO/tree/BRANCH/PATH/TO/SKILL
# Example: https://github.com/someuser/custom-skills/tree/main/skills/excel

OWNER="someuser"
REPO="custom-skills"
BRANCH="main"
SKILL_PATH="skills/excel"
SKILL_NAME="excel"
INSTALL_PATH="$HOME/.config/opencode/skills/$SKILL_NAME"
REPO_URL="https://raw.githubusercontent.com/$OWNER/$REPO/$BRANCH/$SKILL_PATH"

mkdir -p "$INSTALL_PATH"
curl -sL "$REPO_URL/SKILL.md" > "$INSTALL_PATH/SKILL.md"
# Download other files as needed...
```

### Method 3: From Local Files

```bash
# Copy from local directory
SOURCE="./my-custom-skill"
DEST="$HOME/.config/opencode/skills/my-skill"

mkdir -p "$DEST"
cp -r "$SOURCE"/* "$DEST/"

# Verify
echo "Installed files:"
ls -la "$DEST/"
```

## Global vs Project-Local Installation

### Global Installation
- **Location**: `~/.config/opencode/skills/<skill-name>/`
- **Available**: In all projects
- **Use when**: Skill is universally useful (pdf, git, etc.)

### Project-Local Installation
- **Location**: `./.opencode/skills/<skill-name>/`
- **Available**: Only in current project
- **Use when**: Project-specific skill, testing, or avoiding conflicts

### Installation Path Decision Tree

```
Is this skill specific to one project?
├── YES → Install to ./.opencode/skills/<name>/
└── NO → Is this a widely useful skill?
    ├── YES → Install to ~/.config/opencode/skills/<name>/
    └── NO → Install locally (you can always move it later)
```

## Creating a New Skill

### Option 1: Basic Skill (Quick Start)

```bash
# Create skill directory
mkdir -p ~/.config/opencode/skills/my-skill

# Copy basic template
cp ~/.config/opencode/skills/skill-creator/references/templates/basic-skill.md \
  ~/.config/opencode/skills/my-skill/SKILL.md

# Edit the file and customize
```

### Option 2: Full Skill (Complete Structure)

```bash
# Create skill with all sections
mkdir -p ~/.config/opencode/skills/my-skill/references
cp ~/.config/opencode/skills/skill-creator/references/templates/full-skill.md \
  ~/.config/opencode/skills/my-skill/SKILL.md

# Edit and add supplementary files as needed
```

### Required Frontmatter Fields

Every SKILL.md must have:

```yaml
---
name: my-skill              # Must match directory name
description: What this skill does and when to use it
---
```

**Name Validation Rules**:
- 1-64 characters
- Lowercase alphanumeric with single hyphens
- Must match directory name
- Regex: `^[a-z0-9]+(-[a-z0-9]+)*$`

**Description Guidelines**:
- 1-1024 characters
- Include what the skill does AND when to use it
- Be specific enough for the agent to choose correctly

## Validation Checklist

After installing or creating a skill, verify:

```bash
SKILL_PATH="~/.config/opencode/skills/my-skill"

echo "=== Skill Validation ==="
echo ""

# 1. Check SKILL.md exists
[ -f "$SKILL_PATH/SKILL.md" ] && echo "✓ SKILL.md exists" || echo "✗ SKILL.md missing!"

# 2. Check frontmatter exists
head -1 "$SKILL_PATH/SKILL.md" | grep -q "^---" && echo "✓ Frontmatter present" || echo "✗ No frontmatter!"

# 3. Check name field
NAME=$(grep "^name:" "$SKILL_PATH/SKILL.md" | head -1 | sed 's/name: //' | tr -d ' ')
[ -n "$NAME" ] && echo "✓ Name field: $NAME" || echo "✗ Missing name field!"

# 4. Check description field
DESC=$(grep "^description:" "$SKILL_PATH/SKILL.md" | head -1 | sed 's/description: //')
[ -n "$DESC" ] && echo "✓ Description field present" || echo "✗ Missing description field!"

# 5. Verify name matches directory
DIR_NAME=$(basename "$SKILL_PATH")
[ "$NAME" = "$DIR_NAME" ] && echo "✓ Name matches directory" || echo "⚠ Name ($NAME) ≠ directory ($DIR_NAME)"

# 6. Check file permissions
[ -r "$SKILL_PATH/SKILL.md" ] && echo "✓ File is readable" || echo "✗ File not readable!"

echo ""
echo "=== Validation Complete ==="
```

## Managing Skills

### List Installed Skills

```bash
# List global skills
echo "=== Global Skills ==="
ls -1 ~/.config/opencode/skills/ 2>/dev/null || echo "No global skills"

# List local skills (from current directory)
echo ""
echo "=== Project-Local Skills ==="
ls -1 .opencode/skills/ 2>/dev/null || echo "No local skills"
```

### Remove a Skill

```bash
# Remove global skill
rm -rf ~/.config/opencode/skills/skill-name
echo "Removed global skill: skill-name"

# Remove local skill
rm -rf .opencode/skills/skill-name
echo "Removed local skill: skill-name"
```

### Move Skill (Global ↔ Local)

```bash
# Move from global to local
cp -r ~/.config/opencode/skills/skill-name .opencode/skills/
rm -rf ~/.config/opencode/skills/skill-name
echo "Moved skill-name to project-local"

# Move from local to global
mkdir -p ~/.config/opencode/skills
cp -r .opencode/skills/skill-name ~/.config/opencode/skills/
rm -rf .opencode/skills/skill-name
echo "Moved skill-name to global"
```

## Quick Reference

| Task | Command |
|------|---------|
| Install from Claude | See Method 1 above |
| Install from GitHub | See Method 2 above |
| Create basic skill | Copy `templates/basic-skill.md` |
| Create full skill | Copy `templates/full-skill.md` |
| Validate skill | Run validation checklist above |
| List skills | `ls ~/.config/opencode/skills/` |
| Remove skill | `rm -rf ~/.config/opencode/skills/NAME` |

## Version Management

### Check for Updates

```bash
# Get installed version
grep "^version:" ~/.config/opencode/skills/skill-creator/SKILL.md | sed 's/version: //'

# Get latest version from GitHub
curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/SKILL.md | grep "^version:" | sed 's/version: //'
```

If no version is found in the installed skill, it can still be updated by re-downloading all files.

### Update skill-creator

Re-download all files from the source URL to update to the latest version.

## Next Steps

- For detailed installation workflows, see `references/installation-guide.md`
- For Claude skill adaptation notes, see `references/claude-adaptation.md`
- For troubleshooting common issues, see `references/troubleshooting.md`
