# GitLab MR Helper - Development Plan

## Current Phase: Demo/Placeholder

Demo Go scripts that print placeholder output. No actual GitLab API integration yet.

## Roadmap

### Phase 1: Core MR Operations (Current)
- [x] Plugin structure created
- [x] Demo scripts (placeholder output)
- [ ] GitLab API authentication
- [ ] Create MR functionality
- [ ] List MRs functionality
- [ ] Update MR functionality

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

## API Integration Notes

Future scripts will use GitLab REST API v4:
- Base URL: `https://gitlab.example.com/api/v4`
- Authentication: Private token or OAuth
- Key endpoints:
  - `POST /projects/:id/merge_requests` - Create MR
  - `GET /projects/:id/merge_requests` - List MRs
  - `PUT /projects/:id/merge_requests/:mr_iid` - Update MR

## Architecture

```
gitlab-mr-helper/
├── .claude-plugin/plugin.json     # Plugin metadata
├── PLAN.md                        # This file
├── README.md                      # Usage documentation
├── agents/
│   └── gitlab-mr-specialist.md    # Agent (entry point)
└── skills/
    └── managing-gitlab-mrs/
        ├── SKILL.md               # Skill (invoked by agent only)
        └── scripts/
            ├── create_mr.go       # Create MR
            ├── list_mrs.go        # List MRs
            └── update_mr.go       # Update MR
```

## Design Principles

1. **Agent as Entry Point**: The agent is the only user-facing component
2. **Skill for Implementation**: The skill provides technical capabilities, invoked only by the agent
3. **Go Scripts**: Lightweight, compiled scripts for GitLab API operations
4. **Incremental Development**: Start with demos, add real API calls progressively
