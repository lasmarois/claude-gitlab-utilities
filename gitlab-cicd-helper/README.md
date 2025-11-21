# GitLab CI/CD Helper Plugin

A comprehensive Claude Code plugin for GitLab CI/CD operations via API. Trigger pipelines, launch manual jobs, monitor status, and retrieve logs - all from your terminal through Claude.

## Features

- 🚀 **Pipeline Triggering**: Start pipelines on any branch with variables
- ⚙️ **Manual Job Launching**: Trigger manual/delayed jobs individually or in batch
- 👁️ **Status Monitoring**: Real-time pipeline and job status with watch mode
- 📝 **Log Retrieval**: Download and filter job traces
- 🔍 **Auto Project Resolution**: Automatically detects project ID from git remotes
- 🔐 **Secure Token Management**: Centralized token storage with validation

## Installation

1. **Plugin is already installed** at: `~/.claude/plugins/custom/gitlab-cicd-helper/`

2. **Create token file**:
```bash
touch ~/.claude/.cicd-tokens
chmod 600 ~/.claude/.cicd-tokens
```

3. **Add your GitLab tokens** to `~/.claude/.cicd-tokens`:
```bash
# GitLab CI/CD Tokens
TRIGGER_TOKEN="glptt-xxxxxxxxxxxxxxxxxxxxx"  # From Project Settings → CI/CD → Pipeline Triggers
PAT_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxxx"      # From User Settings → Access Tokens (api scope)
```

## Quick Start

### Trigger a Pipeline
```bash
cd /path/to/your/repo
./skills/gitlab-cicd-helper/scripts/trigger_pipeline.py --auto --ref main
```

### Launch Manual Jobs
```bash
# Launch specific job
./skills/gitlab-cicd-helper/scripts/launch_jobs.py \
  --pipeline 12345 --job-name "deploy-production"

# Launch all manual jobs matching pattern
./skills/gitlab-cicd-helper/scripts/launch_jobs.py \
  --pipeline 12345 --batch --pattern "ca-cert:*"
```

### Monitor Pipeline
```bash
# One-time status check
./skills/gitlab-cicd-helper/scripts/monitor_status.py \
  --pipeline 12345 --auto --show-jobs

# Watch until completion
./skills/gitlab-cicd-helper/scripts/monitor_status.py \
  --pipeline 12345 --auto --watch
```

### Get Job Logs
```bash
# Full logs
./skills/gitlab-cicd-helper/scripts/get_logs.py \
  --job 67890 --auto

# Last 50 lines
./skills/gitlab-cicd-helper/scripts/get_logs.py \
  --job 67890 --auto --tail 50

# Filter for errors
./skills/gitlab-cicd-helper/scripts/get_logs.py \
  --job 67890 --auto --grep "ERROR" -i
```

## Complete Workflow Example

```bash
cd /path/to/repo

# 1. Trigger pipeline
PIPELINE_OUTPUT=$(./skills/gitlab-cicd-helper/scripts/trigger_pipeline.py \
  --auto --ref main --var ENVIRONMENT=staging)
echo "$PIPELINE_OUTPUT"

# Extract pipeline ID
PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')
echo "Pipeline ID: $PIPELINE_ID"

# 2. Wait for pipeline initialization
sleep 10

# 3. Launch deployment jobs
./skills/gitlab-cicd-helper/scripts/launch_jobs.py \
  --pipeline $PIPELINE_ID --batch --pattern "deploy-*"

# 4. Monitor until complete
./skills/gitlab-cicd-helper/scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --watch
```

## Scripts Reference

### trigger_pipeline.py
Trigger a new pipeline with optional variables.

**Options**:
- `--auto` - Auto-resolve project from git remote
- `--project ID` - Explicit project ID or path
- `--project-path PATH` - Project path (e.g., 'group/project')
- `--ref BRANCH` - Branch or tag name (default: main)
- `--var KEY=VALUE` - Pipeline variables (repeatable)

### launch_jobs.py
Launch manual or created jobs.

**Options**:
- `--pipeline ID` - Pipeline ID (required)
- `--job-id ID` - Specific job ID to launch
- `--job-name NAME` - Job name to launch
- `--batch` - Launch multiple jobs
- `--pattern PATTERN` - Job name pattern (e.g., 'deploy-*', 'ca-cert:*')
- `--status STATUS` - Filter by job status (default: manual)
- `--var KEY=VALUE` - Job variables (repeatable)

### monitor_status.py
Monitor pipeline or job status.

**Options**:
- `--pipeline ID` - Monitor pipeline
- `--job ID` - Monitor job
- `--show-jobs` - Show jobs list for pipelines
- `--watch` - Auto-refresh until completion
- `--interval SECONDS` - Refresh interval for watch mode (default: 5)

### get_logs.py
Retrieve job logs/traces.

**Options**:
- `--job ID` - Job ID (required)
- `--tail N` - Show only last N lines
- `--grep PATTERN` - Filter lines matching regex pattern
- `--ignore-case, -i` - Case-insensitive pattern matching
- `--context N, -C N` - Show N lines of context around matches
- `--line-numbers, -n` - Show line numbers
- `--output FILE, -o FILE` - Save logs to file

## Token Setup

### Creating Tokens in GitLab

**Trigger Token** (for triggering pipelines):
1. Go to your GitLab project
2. Settings → CI/CD → Pipeline triggers
3. Add trigger → Give it a description
4. Copy the token (starts with `glptt-`)

**Personal Access Token** (for API operations):
1. Go to GitLab User Settings
2. Access Tokens
3. Create token with:
   - Name: "Claude CI/CD Operations"
   - Scopes: `api` (full API access)
   - Expiration: Set according to your policy
4. Copy the token (starts with `glpat-`)

### Token File Format
```bash
# ~/.claude/.cicd-tokens
TRIGGER_TOKEN="glptt-xxxxxxxxxxxxxxxxxxxxx"
PAT_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxxx"

# Optional: Override GitLab URL (defaults to gitlab.pitchblackcompany.com)
# GITLAB_URL="https://gitlab.example.com"
```

**Important**: Set file permissions to `600`:
```bash
chmod 600 ~/.claude/.cicd-tokens
```

## Common Use Cases

### CA Certificate Testing
Test CA certificate volume mounts across distributions:
```bash
cd /home/nmarois/gits/runner-troubleshooter
PIPELINE_ID=$(./skills/gitlab-cicd-helper/scripts/trigger_pipeline.py \
  --auto --ref main | grep -oP 'Pipeline #\d+ \(ID: \K\d+')
sleep 10
./skills/gitlab-cicd-helper/scripts/launch_jobs.py \
  --pipeline $PIPELINE_ID --batch --pattern "ca-cert:*"
```

### Deployment Workflow
Deploy to staging:
```bash
cd /path/to/project
PIPELINE_ID=$(./skills/gitlab-cicd-helper/scripts/trigger_pipeline.py \
  --auto --ref main --var ENVIRONMENT=staging | grep -oP 'Pipeline #\d+ \(ID: \K\d+')
sleep 10
./skills/gitlab-cicd-helper/scripts/launch_jobs.py \
  --pipeline $PIPELINE_ID --job-name "deploy-staging"
```

### Debugging Failed Jobs
Find and analyze failed jobs:
```bash
# Check pipeline status
./skills/gitlab-cicd-helper/scripts/monitor_status.py \
  --pipeline 12345 --auto --show-jobs

# Get logs for failed job
./skills/gitlab-cicd-helper/scripts/get_logs.py \
  --job 67890 --auto --tail 100 --grep "ERROR"
```

## Troubleshooting

### Token Validation Fails
**Problem**: "Token file not found" or "Missing required tokens"

**Solution**:
1. Create the token file: `touch ~/.claude/.cicd-tokens`
2. Set correct permissions: `chmod 600 ~/.claude/.cicd-tokens`
3. Add both TRIGGER_TOKEN and PAT_TOKEN
4. Verify PAT has `api` scope in GitLab

### Project Resolution Fails
**Problem**: "Failed to get git remote URL"

**Solution**:
1. Ensure you're in a git repository: `git status`
2. Verify remote exists: `git remote -v`
3. Use explicit `--project ID` if not in a git repo

### No Manual Jobs Found
**Problem**: "No manual jobs found"

**Solution**:
1. Wait 10-15 seconds after triggering pipeline
2. Check job status first with `monitor_status.py`
3. Try different `--status` filter (created, pending, manual)
4. Verify pattern matches job names

### API Errors (401, 403)
**Problem**: "401 Unauthorized" or "403 Forbidden"

**Solution**:
1. Verify PAT_TOKEN has `api` scope
2. Check if token expired (regenerate in GitLab)
3. Ensure you have project permissions

## Architecture

### Plugin Structure
```
~/.claude/plugins/custom/gitlab-cicd-helper/
├── .claude-plugin/
│   └── plugin.json               # Plugin metadata
├── skills/
│   └── gitlab-cicd-helper/
│       ├── SKILL.md              # Claude skill instructions
│       └── scripts/
│           ├── trigger_pipeline.py       # Pipeline triggering
│           ├── launch_jobs.py            # Job launching
│           ├── monitor_status.py         # Status monitoring
│           ├── get_logs.py              # Log retrieval
│           └── lib/
│               ├── __init__.py
│               ├── token_manager.py      # Token validation & loading
│               ├── gitlab_client.py      # GitLab API wrapper
│               ├── project_resolver.py   # Auto project ID resolution
│               └── output_formatter.py   # Terminal output formatting
└── README.md                     # This file
```

### Design Principles
- **Self-contained**: No external dependencies (uses system Python3)
- **Secure**: Tokens stored separately with restricted permissions
- **Efficient**: Minimal API calls with smart caching
- **User-friendly**: Beautiful terminal output with emojis and colors
- **Auto-detection**: Resolves project IDs automatically from git

## Using with Claude

This plugin is designed to work seamlessly with Claude Code. Simply ask Claude to:

- "Trigger a pipeline for this project"
- "Launch the CA certificate tests"
- "Monitor pipeline 12345"
- "Show me the logs for job 67890"
- "Deploy to staging"

Claude will use the plugin automatically to execute your requests.

## Requirements

- Python 3.6+
- Git (for auto project resolution)
- GitLab instance with API access
- Valid GitLab tokens (trigger token + PAT)

## License

MIT License - Use freely in your projects

## Contributing

This is a custom plugin for your environment. Enhance as needed!

## Support

For issues or questions:
1. Check the SKILL.md for detailed usage
2. Verify token configuration in ~/.claude/.cicd-tokens
3. Test scripts individually before complex workflows
4. Check GitLab API documentation for specific operations

---

**Happy CI/CD automating! 🚀**
