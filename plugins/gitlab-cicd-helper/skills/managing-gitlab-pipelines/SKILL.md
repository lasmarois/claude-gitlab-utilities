---
name: managing-gitlab-pipelines
description: "REQUIRED Python scripts for GitLab CI/CD pipeline automation. MUST be loaded before triggering pipelines, launching manual jobs, monitoring pipeline status, or collecting job logs. Contains authoritative documentation on batch operations, pattern matching, watch mode, and failure analysis workflows. Invoked by gitlab-cicd-specialist agent."
allowed-tools: Bash, Read
---

# Managing GitLab Pipelines

> **Note:** This skill is a reference library for the `gitlab-cicd-specialist` agent. Do not invoke directly - use the agent for pipeline operations.

GitLab CI/CD operations providing comprehensive pipeline management through efficient Python scripts.

## Core Capabilities

1. **Pipeline Discovery**: List and find existing pipelines by status, branch, or source
2. **Pipeline Triggering**: Start pipelines with variables/inputs on any branch
3. **Manual Job Launching**: Trigger manual/delayed jobs (single or batch operations)
4. **Status Monitoring**: Real-time pipeline and job status with optional watch mode
5. **Log Retrieval**: Download and analyze job traces with filtering
6. **Auto Project Resolution**: Automatically determine project IDs from git remotes
7. **Pipeline Intelligence**: Full pipeline awareness with proper pagination (finds ALL jobs!)
8. **Config Analysis**: Compare .gitlab-ci.yml configuration vs actual pipeline state

## Quick Start

### List Pipelines
```bash
cd /path/to/repo

# List recent pipelines
./scripts/list_pipelines.py --auto

# List failed pipelines
./scripts/list_pipelines.py --auto --status failed

# Get latest pipeline ID (for scripting)
./scripts/list_pipelines.py --auto --latest
```

### Trigger Pipeline
```bash
cd /path/to/repo
./scripts/trigger_pipeline.py --auto --ref main
```

### Launch Manual Jobs
```bash
# Single job
./scripts/launch_jobs.py --pipeline 12345 --job-name "deploy-production"

# Batch launch with pattern
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "test-*"
```

### Monitor Status
```bash
# Watch pipeline with progress tracking
./scripts/monitor_status.py --pipeline 12345 --auto --watch

# Pattern-aware watch (stops when pattern jobs complete)
./scripts/monitor_status.py --pipeline 12345 --auto --watch --watch-pattern "test-*"
```

### Get Logs
```bash
# Single job
./scripts/get_logs.py --job 67890 --auto

# Batch mode - all failed jobs
./scripts/get_logs.py --pipeline 12345 --batch --failed-only --summary --auto
```

## Detailed Documentation

### Setup and Configuration
See [SETUP.md](SETUP.md) for:
- **Prerequisites**: uv package manager installation
- **Authentication**: PAT tokens, .netrc, .git-credentials
- **Architecture**: python-gitlab library, automatic pagination
- **Script Locations**: Relative paths for script execution

### Complete Script Reference
See [SCRIPTS.md](SCRIPTS.md) for:
- **list_pipelines.py**: List and find existing pipelines
- **trigger_pipeline.py**: Trigger pipelines with variables
- **launch_jobs.py**: Launch manual jobs (single or batch)
- **monitor_status.py**: Monitor status with watch mode
- **get_logs.py**: Retrieve logs (single or batch)
- **Job Status Types**: Understanding job lifecycle and launchability

### Common Workflows
See [WORKFLOWS.md](WORKFLOWS.md) for:
- **Find and Work with Existing Pipelines**: List, select, and operate on pipelines
- **Trigger and Monitor**: Start pipeline and watch progress
- **Variables and Manual Jobs**: Deploy to environments
- **Batch Launch by Pattern**: Run specific job sets
- **Troubleshoot Failed Jobs**: Debug CI failures
- **Batch Log Collection**: Archive and analyze logs
- **Best Practices**: Proven patterns for each operation

### Troubleshooting
See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- **Authentication Issues**: Token validation, scope problems
- **Project Resolution**: Git remote errors
- **Job Launch Errors**: Unplayable jobs, status confusion
- **API Errors**: Rate limiting, timeouts
- **General Issues**: Common problems and solutions

## Key Features

### Automatic Pagination (CRITICAL FIX)
All scripts use `get_all=True` to fetch ALL jobs:
```bash
# Now finds all 90 jobs, not just first 20!
./scripts/launch_jobs.py --pipeline 12345 --batch
```

### Pattern Matching
Selective job operations with glob-style patterns:
```bash
# Launch test jobs
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "test-*"

# Get logs from CA cert tests
./scripts/get_logs.py --pipeline 12345 --batch --pattern "ca-cert:*" --auto
```

### Watch Mode with Progress Tracking
Real-time monitoring with automatic progress display:
```bash
./scripts/monitor_status.py --pipeline 12345 --auto --watch
# Shows: completion %, running jobs, recent changes
```

### Pattern-Aware Watch (Smart Monitoring)
Stop monitoring when specific jobs complete:
```bash
# Traditional: waits for entire pipeline
./scripts/monitor_status.py --pipeline 12345 --auto --watch

# Smart: stops when test-* jobs complete
./scripts/monitor_status.py --pipeline 12345 --auto --watch --watch-pattern "test-*"
```

### Batch Log Collection
Organized log retrieval with analysis:
```bash
# All failed jobs with summary
./scripts/get_logs.py --pipeline 12345 --batch --failed-only --summary --auto

# Complete archive with aggregate log
./scripts/get_logs.py --pipeline 12345 --batch --all --aggregate --summary --auto
```

**Output structure:**
```
/tmp/gitlab-logs-12345/
├── summary.txt          # Overview report
├── manifest.json        # Metadata
├── aggregate.log        # All logs combined
├── by-status/           # Organized by status
├── by-stage/            # Organized by stage
└── all/                 # All logs flat
```

## Best Practices Summary

**Project Resolution:**
- Always use `--auto` when in git repository
- Scripts auto-detect project from git remote

**Pipeline Triggering:**
- Use descriptive variable names
- Wait 5-10 seconds after triggering before launching jobs

**Batch Operations:**
- Use patterns for selective launching: `--pattern "deploy-*"`
- Use `--status manual` to target jobs ready to launch

**Monitoring:**
- Use `--watch` mode for long-running operations
- Use `--watch-pattern` when monitoring specific job sets
- Set appropriate `--interval` (default: 5s) to avoid rate limits

**Log Analysis:**
- Use `--tail N` to limit output for long logs
- Use `--grep` with regex for filtering
- Use `--summary` for overview before detailed analysis
- Use `--aggregate` for single-file analysis

## Common Patterns

### Work with Existing Pipeline
```bash
cd /path/to/repo

# 1. List recent pipelines to find the one you want
./scripts/list_pipelines.py --auto

# 2. Or find specific pipeline (failed, on main branch, etc.)
./scripts/list_pipelines.py --auto --status failed --ref main

# 3. Work with the pipeline using its ID
PIPELINE_ID=12345
./scripts/monitor_status.py --pipeline $PIPELINE_ID --auto --show-jobs
./scripts/launch_jobs.py --pipeline $PIPELINE_ID --batch --pattern "test-*"
./scripts/get_logs.py --pipeline $PIPELINE_ID --batch --failed-only --summary --auto
```

### End-to-End: Trigger → Launch → Monitor → Logs
```bash
cd /path/to/repo

# 1. Trigger
PIPELINE_OUTPUT=$(./scripts/trigger_pipeline.py --auto --ref main)
PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')

# 2. Wait for initialization
sleep 10

# 3. Launch specific jobs
./scripts/launch_jobs.py --pipeline $PIPELINE_ID --batch --pattern "test-*"

# 4. Monitor with pattern-aware watch
./scripts/monitor_status.py --pipeline $PIPELINE_ID --auto --watch --watch-pattern "test-*"

# 5. Get failed logs if any
./scripts/get_logs.py --pipeline $PIPELINE_ID --batch --failed-only --summary --auto
```

### Debug Failed Pipeline
```bash
# 1. Check status
./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs

# 2. Get all failed logs
./scripts/get_logs.py --pipeline 12345 --batch --failed-only --grep "ERROR" --summary --auto

# 3. Review summary
cat /tmp/gitlab-logs-12345/summary.txt

# 4. Examine specific log
less /tmp/gitlab-logs-12345/by-status/failed/job-456-test-integration.log
```

## Important Notes

1. **uv required**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Pagination fixed**: Now finds ALL jobs (e.g., 90 jobs, not just 20!)
3. **Always use --auto**: Most convenient when in git repo
4. **Wait after triggering**: Pipeline needs time to initialize (5-10 seconds)
5. **Batch operations are powerful**: Use patterns for selective operations
6. **Watch mode is interactive**: User can Ctrl+C to stop
7. **Pattern-aware watch**: Stops when YOUR jobs complete (not entire pipeline)
8. **Logs may not exist yet**: Jobs must start running first

## Response Format

When executing GitLab operations, provide:

1. **Context**: What you're going to do
2. **Command**: The exact script with arguments
3. **Output**: Parse and explain the results
4. **Next Steps**: Suggest logical follow-up actions or provide URLs

Example:
```
I'll trigger a new pipeline for the current project:

[command executed]

✅ Pipeline #24 created successfully
🔗 Monitor at: https://gitlab.example.com/your-org/your-project/-/pipelines/12345

The pipeline has 20 jobs across 3 stages. Would you like me to:
- Launch specific manual jobs?
- Monitor the pipeline progress?
- Check job logs when they complete?
```

## Success Indicators

- ✅ Token validation passes
- ✅ Project auto-resolved (shows project name and ID)
- ✅ Pipeline triggered (shows pipeline ID and URL)
- ✅ Jobs launched (shows job IDs)
- ✅ Status displays with emojis and formatting
- ✅ Logs retrieved successfully

You are now ready to provide professional GitLab CI/CD automation support!
