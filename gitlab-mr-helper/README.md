# GitLab MR Helper

Claude Code plugin for GitLab Merge Request management.

## Status

**Demo/Placeholder** - Scripts print placeholder output. See [PLAN.md](PLAN.md) for roadmap.

## Usage

Ask Claude to perform MR operations:

- "Create a merge request from feature-branch to main"
- "List my open merge requests"
- "Update MR #123 description"

Claude will use the **GitLab MR Specialist** agent to handle requests.

## Structure

```
gitlab-mr-helper/
├── .claude-plugin/plugin.json    # Plugin metadata
├── PLAN.md                       # Development roadmap
├── README.md                     # This file
├── agents/
│   └── gitlab-mr-specialist.md   # Agent (entry point)
└── skills/
    └── managing-gitlab-mrs/
        ├── SKILL.md              # Skill definition
        └── scripts/
            ├── create_mr.go      # Create MR
            ├── list_mrs.go       # List MRs
            └── update_mr.go      # Update MR
```

## Architecture

- **Agent**: User-facing entry point for MR requests
- **Skill**: Technical implementation loaded by agent only
- **Scripts**: Go scripts for GitLab API operations (currently demo)
