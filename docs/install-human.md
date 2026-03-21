# Human Installation Guide

This guide is for people installing the `skill-creator` skill.

Important: this project does **not** auto-install third-party skills by itself. You decide which skills to install, when to install them, and where to install them.

## Installation Method: Use Your AI Agent

The easiest way to install skill-creator is to give the URL to your AI agent (OpenCode, Claude, etc.):

```
Install skill-creator from https://github.com/JValdivia23/opencode-skill-creator
```

Your agent will read the installation instructions and download the necessary files.

## Manual Installation (Terminal)

If you prefer to install manually using curl:

```bash
# Create directories
mkdir -p ~/.config/opencode/skills/skill-creator/references/templates

# Download SKILL.md
curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/SKILL.md \
  > ~/.config/opencode/skills/skill-creator/SKILL.md

# Download references
curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/installation-guide.md \
  > ~/.config/opencode/skills/skill-creator/references/installation-guide.md

curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/troubleshooting.md \
  > ~/.config/opencode/skills/skill-creator/references/troubleshooting.md

curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/claude-adaptation.md \
  > ~/.config/opencode/skills/skill-creator/references/claude-adaptation.md

# Download templates
curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/templates/basic-skill.md \
  > ~/.config/opencode/skills/skill-creator/references/templates/basic-skill.md

curl -sL https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/templates/full-skill.md \
  > ~/.config/opencode/skills/skill-creator/references/templates/full-skill.md

# Verify installation
ls -la ~/.config/opencode/skills/skill-creator/
```

## Install Third-Party Skills

Once skill-creator is installed, give your agent any skill URL:

```
Install the skill from https://github.com/anthropics/skills/tree/main/skills/pdf
```

Your agent will handle the installation.

## Uninstall

To remove a skill:

```bash
# Remove skill-creator
rm -rf ~/.config/opencode/skills/skill-creator/

# Remove any other skill
rm -rf ~/.config/opencode/skills/<skill-name>/
```

## Installation Paths

- **Local**: `./.opencode/skills/<name>/` (current project only)
- **Global**: `~/.config/opencode/skills/<name>/` (all projects)

## Verification

Check that the skill is properly installed:

```bash
# Check SKILL.md exists
ls ~/.config/opencode/skills/skill-creator/SKILL.md

# Check frontmatter
head -5 ~/.config/opencode/skills/skill-creator/SKILL.md

# List all installed skills
ls ~/.config/opencode/skills/
```
