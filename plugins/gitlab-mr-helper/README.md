# GitLab MR Helper

Claude Code plugin for GitLab Merge Request management.

## Features

- **Create MRs**: Create merge requests with automatic branch detection and title generation
- **List MRs**: View merge requests with status icons, labels, and age
- **Update MRs**: Modify title, description, labels, or close/reopen MRs

## Usage

Ask Claude to perform MR operations:

- "Create a merge request from my current branch"
- "List my open merge requests"
- "Update MR #123 with a new title"
- "Close MR #45"

Claude will use the **GitLab MR Specialist** agent to handle requests.

## Authentication

Set up authentication using one of these methods:

**Option 1: Environment Variable (recommended)**
```bash
export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'
```

**Option 2: ~/.netrc file**
```bash
machine gitlab.com
login oauth2
password glpat-xxxxxxxxxxxxxxxxxxxxx
```

**Option 3: ~/.git-credentials**
```bash
https://oauth2:glpat-xxxxxxxxxxxxxxxxxxxxx@gitlab.com
```

**Optional**: Set `GITLAB_URL` to use a self-hosted GitLab instance.

## Installation

```bash
/plugin install gitlab-mr-helper@claude-gitlab-utilities
```

## Architecture

| Component | Description |
|-----------|-------------|
| **Agent** (`gitlab-mr-specialist`) | Entry point for MR requests |
| **Skill** (`managing-gitlab-mrs`) | Technical implementation (agent-only) |
| **Scripts** | Go scripts for GitLab API operations |

## Scripts

All scripts support `--auto` for automatic project detection from git remote.

| Script | Purpose | Example |
|--------|---------|---------|
| `create_mr.go` | Create MR | `go run scripts/create_mr.go --auto` |
| `list_mrs.go` | List MRs | `go run scripts/list_mrs.go --auto --state opened` |
| `update_mr.go` | Update MR | `go run scripts/update_mr.go --auto --mr 123 --title "New"` |

See [PLAN.md](PLAN.md) for development roadmap.
