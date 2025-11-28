# GitLab MR Helper - Development Plan

## Current Phase: Phase 1 Complete

Go scripts with full GitLab API v4 integration for MR management.

## Roadmap

### Phase 1: Core MR Operations ✅
- [x] Plugin structure created
- [x] GitLab API authentication (GITLAB_TOKEN, .netrc, .git-credentials)
- [x] Auto project resolution from git remote
- [x] Create MR functionality
- [x] List MRs functionality
- [x] Update MR functionality

### Phase 2: Enhanced Features
- [ ] MR templates support
- [ ] Auto-assign reviewers
- [ ] Label management
- [ ] Milestone assignment
- [ ] Draft MR support

### Phase 3: Advanced Workflows
- [ ] MR status monitoring
- [ ] Merge when pipeline succeeds
- [ ] Conflict detection
- [ ] Cross-project MRs

## API Integration

Scripts use GitLab REST API v4:
- Base URL: `https://gitlab.com/api/v4` (or GITLAB_URL)
- Authentication: Private token via GITLAB_TOKEN, .netrc, or .git-credentials
- Key endpoints:
  - `POST /projects/:id/merge_requests` - Create MR
  - `GET /projects/:id/merge_requests` - List MRs
  - `PUT /projects/:id/merge_requests/:mr_iid` - Update MR

## Architecture

```
plugins/gitlab-mr-helper/
├── .claude-plugin/plugin.json     # Plugin metadata
├── PLAN.md                        # This file
├── README.md                      # Usage documentation
├── agents/
│   └── gitlab-mr-specialist.md    # Agent (entry point)
└── skills/
    └── managing-gitlab-mrs/
        ├── SKILL.md               # Skill (invoked by agent only)
        └── scripts/
            ├── go.mod             # Go module definition
            ├── lib/
            │   ├── api.go         # GitLab API client
            │   └── config.go      # Configuration/auth handling
            ├── create_mr.go       # Create MR
            ├── list_mrs.go        # List MRs
            └── update_mr.go       # Update MR
```

## Design Principles

1. **Agent as Entry Point**: The agent is the only user-facing component
2. **Skill for Implementation**: The skill provides technical capabilities, invoked only by the agent
3. **Go Scripts**: Lightweight scripts using standard library only (no external dependencies)
4. **Standard Auth**: Same authentication as official GitLab tools
5. **Auto Resolution**: `--auto` flag for seamless project detection
