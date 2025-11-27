---
name: managing-gitlab-mrs
description: "Reference scripts for the gitlab-mr-specialist agent. Contains Go-based GitLab MR automation for creating, listing, and updating merge requests. NOT for direct use - always use the gitlab-mr-specialist agent instead."
allowed-tools: Bash, Read
---

# Managing GitLab MRs

> **Note:** This skill is a reference library for the `gitlab-mr-specialist` agent. Do not invoke directly - use the agent for MR operations.

Go scripts for GitLab Merge Request operations.

## Scripts

| Script | Purpose |
|--------|---------|
| `create_mr.go` | Create a new merge request |
| `list_mrs.go` | List merge requests |
| `update_mr.go` | Update an existing MR |

## Script Location

```
scripts/
```

## Usage

### Create MR

```bash
go run scripts/create_mr.go
```

### List MRs

```bash
go run scripts/list_mrs.go
```

### Update MR

```bash
go run scripts/update_mr.go
```

## Current Status

**Demo/Placeholder Phase**: Scripts print placeholder output. Real GitLab API integration planned for future phases.
