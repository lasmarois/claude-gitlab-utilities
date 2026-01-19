---
name: gitlab-status
description: "Quick access to GitLab pipeline status and structure. View jobs, stages, and pipeline tree without the full agent."
allowed-tools: Bash, Read
---

# GitLab Status - Quick Reference

Lightweight command for viewing pipeline status, job tree, and structure. For complex multi-step workflows, use the `gitlab-cicd-specialist` agent instead.

## Script Location

```bash
SCRIPT_DIR="$HOME/.claude/plugins/cache/claude-gitlab-utilities/gitlab-cicd-helper/1.0.0/skills/managing-gitlab-pipelines/scripts"
```

## Quick Commands

### Pipeline Overview

```bash
# Basic status
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto

# With all jobs listed
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --show-jobs

# Full structure analysis (jobs by status + by stage)
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --structure
```

### Pipeline Structure Output Example

```
================================================================================
📊 Pipeline Structure Analysis
================================================================================

Total Jobs: 90

Jobs by Status:
   ✅ success: 45
   ❌ failed: 6
   ▶️ running: 2
   ⚙️ manual: 13
   ◯ created: 24

Jobs by Stage:
   build (5 jobs):
      ✅ build-backend
      ✅ build-frontend
      ...
   test (40 jobs):
      ✅ unit-tests
      ❌ integration-test
      ▶️ e2e-tests
      ...
   deploy (10 jobs):
      ⚙️ deploy-staging
      ⚙️ deploy-production
      ...
================================================================================
```

### Compare Config vs Actual

```bash
# Compare .gitlab-ci.yml with actual pipeline state
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --compare
```

Shows which jobs were created vs expected from config - useful for debugging missing or unexpected jobs.

### Single Job Details

```bash
# Get details for a specific job
$SCRIPT_DIR/monitor_status.py --job JOB_ID --auto
```

### Watch Mode (Live Updates)

```bash
# Watch until pipeline completes
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --watch

# Custom refresh interval (default: 5s)
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --watch --interval 10

# Stop when specific jobs complete (pattern-aware)
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --watch --watch-pattern "test-*"
```

Watch mode automatically shows:
- Progress summary (completion %, job counts by status)
- Currently running jobs with durations
- Recently changed jobs (status transitions)

## Key Options Reference

| Option | Description |
|--------|-------------|
| `--pipeline ID` | Target pipeline ID |
| `--job ID` | Single job details |
| `--auto` | Auto-detect project from git remote |
| `--show-jobs` | List all jobs in pipeline |
| `--structure` | Full structure analysis (by status + stage) |
| `--compare` | Compare .gitlab-ci.yml vs actual |
| `--watch` | Live updates until completion |
| `--watch-pattern GLOB` | Stop when matching jobs complete |
| `--interval N` | Refresh interval in seconds (default: 5) |

## Finding Pipeline ID

```bash
# List recent pipelines
$SCRIPT_DIR/list_pipelines.py --auto

# Get latest pipeline ID
PIPELINE_ID=$($SCRIPT_DIR/list_pipelines.py --auto --latest)

# List failed pipelines only
$SCRIPT_DIR/list_pipelines.py --auto --status failed
```

## Examples by Use Case

**"Show me the pipeline structure"**
```bash
$SCRIPT_DIR/monitor_status.py --pipeline 12345 --auto --structure
```

**"What jobs are in this pipeline?"**
```bash
$SCRIPT_DIR/monitor_status.py --pipeline 12345 --auto --show-jobs
```

**"Why are some jobs missing?"**
```bash
$SCRIPT_DIR/monitor_status.py --pipeline 12345 --auto --compare
```

**"Watch the test jobs until they finish"**
```bash
$SCRIPT_DIR/monitor_status.py --pipeline 12345 --auto --watch --watch-pattern "test-*"
```

**"Quick check on latest pipeline"**
```bash
PIPELINE_ID=$($SCRIPT_DIR/list_pipelines.py --auto --latest)
$SCRIPT_DIR/monitor_status.py --pipeline $PIPELINE_ID --auto --structure
```
