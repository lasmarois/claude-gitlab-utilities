---
name: managing-gitlab-mrs
description: "REQUIRED Go scripts for GitLab Merge Request automation. MUST be loaded before creating merge requests, listing project MRs, or updating MR metadata (title, description, labels, state). Contains authoritative documentation on MR workflows and GitLab API integration. Invoked by gitlab-mr-specialist agent."
allowed-tools: Bash, Read
---

# Managing GitLab MRs

> **Note:** This skill is a reference library for the `gitlab-mr-specialist` agent. Do not invoke directly - use the agent for MR operations.

Go scripts for GitLab Merge Request operations using the GitLab REST API v4.

## Authentication

Scripts use standard GitLab authentication (same as official tools):

1. **GITLAB_TOKEN** environment variable (recommended)
2. **~/.netrc** file with GitLab credentials
3. **~/.git-credentials** file

Optional: Set `GITLAB_URL` to override the default GitLab instance (defaults to `https://gitlab.com`).

## Scripts

| Script | Purpose |
|--------|---------|
| `create_mr.go` | Create a new merge request |
| `list_mrs.go` | List merge requests |
| `update_mr.go` | Update an existing MR |

## Usage

All scripts support `--auto` flag for automatic project resolution from git remote.

### Create MR

```bash
cd /path/to/repo
go run scripts/create_mr.go --auto
```

**Options:**
- `--auto` - Auto-detect project from git remote
- `--source BRANCH` - Source branch (default: current branch)
- `--target BRANCH` - Target branch (default: main)
- `--title "Title"` - MR title (default: derived from branch name)
- `--description "Desc"` - MR description
- `--labels "l1,l2"` - Comma-separated labels
- `--remove-source-branch` - Remove source branch after merge

**Examples:**
```bash
# Simple MR from current branch to main
go run scripts/create_mr.go --auto

# With custom title and description
go run scripts/create_mr.go --auto --title "Add feature X" --description "Implements feature X"

# With labels and target branch
go run scripts/create_mr.go --auto --target develop --labels "enhancement,review-needed"
```

### List MRs

```bash
cd /path/to/repo
go run scripts/list_mrs.go --auto
```

**Options:**
- `--auto` - Auto-detect project from git remote
- `--state STATE` - Filter by state: opened, closed, merged, all (default: opened)
- `--limit N` - Maximum MRs to list (default: 20)

**Examples:**
```bash
# List open MRs
go run scripts/list_mrs.go --auto

# List all MRs
go run scripts/list_mrs.go --auto --state all

# List merged MRs (last 50)
go run scripts/list_mrs.go --auto --state merged --limit 50
```

### Update MR

```bash
cd /path/to/repo
go run scripts/update_mr.go --auto --mr 123 --title "New title"
```

**Options:**
- `--auto` - Auto-detect project from git remote
- `--mr IID` - MR IID to update (required)
- `--title "Title"` - New title
- `--description "Desc"` - New description
- `--target BRANCH` - New target branch
- `--labels "l1,l2"` - New labels (replaces existing)
- `--state EVENT` - State event: close, reopen

**Examples:**
```bash
# Update title
go run scripts/update_mr.go --auto --mr 123 --title "Updated title"

# Close an MR
go run scripts/update_mr.go --auto --mr 123 --state close

# Update multiple fields
go run scripts/update_mr.go --auto --mr 123 --title "New title" --labels "ready,reviewed"
```

## Output Examples

### Create MR
```
✓ Project: mygroup/myproject
Creating MR: feature-branch → main
  Title: Feature branch

✓ MR !45 created successfully
  URL: https://gitlab.com/mygroup/myproject/-/merge_requests/45
  State: opened
```

### List MRs
```
✓ Project: mygroup/myproject

Merge Requests (opened):
--------------------------------------------------------------------------------
🟢 !45  Add new feature
     feature-branch → main  |  @username  |  2h ago

🟢 !44  [Draft] Work in progress
     wip-branch → main  |  @username  |  1d ago
     Labels: draft, needs-review

Total: 2 merge request(s)
```

### Update MR
```
✓ Project: mygroup/myproject
Updating MR !45:
  • title → "Updated title"
  • labels → [ready, reviewed]

✓ MR !45 updated successfully
  Title: Updated title
  State: opened
  URL: https://gitlab.com/mygroup/myproject/-/merge_requests/45
```
