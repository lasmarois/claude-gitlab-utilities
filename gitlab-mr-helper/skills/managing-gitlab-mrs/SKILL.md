---
name: managing-gitlab-mrs
description: Go-based GitLab MR automation scripts for creating, listing, and updating merge requests. Technical foundation invoked by gitlab-mr-specialist agent. (plugin:gitlab-mr-helper@claude-gitlab-utilities)
allowed-tools: Bash, Read
---

# Managing GitLab MRs

Go scripts for GitLab Merge Request operations.

## Scripts

| Script | Purpose |
|--------|---------|
| `create_mr.go` | Create a new merge request |
| `list_mrs.go` | List merge requests |
| `update_mr.go` | Update an existing MR |

## Script Location

```
gitlab-mr-helper/skills/managing-gitlab-mrs/scripts/
```

## Usage

### Create MR

```bash
go run gitlab-mr-helper/skills/managing-gitlab-mrs/scripts/create_mr.go
```

### List MRs

```bash
go run gitlab-mr-helper/skills/managing-gitlab-mrs/scripts/list_mrs.go
```

### Update MR

```bash
go run gitlab-mr-helper/skills/managing-gitlab-mrs/scripts/update_mr.go
```

## Current Status

**Demo/Placeholder Phase**: Scripts print placeholder output. Real GitLab API integration planned for future phases.
