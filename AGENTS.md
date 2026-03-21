# Instructions for opencode-skill-creator

This repository is a skill for Opencode so the agents know how to install other skills from GitHub. The user should find the skill that wants and just provide the link the the agent and the agent should know (based on the instructions of this skill) how to install and test the skill properly.

## Think as a new user

1. This repo will be at GitHub, so the files are not locally installed for the user.
2. We want the user to install this repo easily with the minimum human intervention.
3. The user should be able to just copy a prompt to an agent in Opencode and the agent should know how to install the skill properly from the web.
4. If the user is not happy about the project, they should easily find a way to uninstall or update to the last version without cloning the whole project.

## NOTE: Every time you make a change that modify the project structure update the AGENTS..md
## Project Structure

```
opencode-skill-creator/
├── skills/skill-creator/       # The skill to install
│   ├── SKILL.md                # Main skill definition (frontmatter + instructions)
│   ├── manifest.yaml           # Skill manifest (deterministic installation)
│   └── references/             # Supporting documentation
│       ├── installation-guide.md
│       ├── claude-adaptation.md
│       ├── troubleshooting.md
│       └── templates/
│           ├── basic-skill.md
│           └── full-skill.md
```

## Installation Paths for an OpenCode skill

- **Local**: `./.opencode/skills/<skill-name>/` (current project only)
- **Global**: `~/.config/opencode/skills/<skill-name>/` (all projects)

