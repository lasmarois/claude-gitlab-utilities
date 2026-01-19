---
name: gitlab-logs
description: "Quick access to GitLab job/pipeline logs. Download, filter, and analyze logs without the full agent."
allowed-tools: Bash, Read
---

# GitLab Logs - Quick Reference

Lightweight command for retrieving GitLab job and pipeline logs. For complex multi-step workflows, use the `gitlab-cicd-specialist` agent instead.

## Script Location

```bash
SCRIPT_DIR="$HOME/.claude/plugins/cache/claude-gitlab-utilities/gitlab-cicd-helper/1.0.0/skills/managing-gitlab-pipelines/scripts"
```

## Quick Commands

### Single Job Logs

```bash
# By job ID (most direct)
$SCRIPT_DIR/get_logs.py --job JOB_ID --auto

# By job name in pipeline
$SCRIPT_DIR/get_logs.py --pipeline PIPELINE_ID --job-name "job-name" --auto

# Last 100 lines only
$SCRIPT_DIR/get_logs.py --job JOB_ID --auto --tail 100

# Filter for errors
$SCRIPT_DIR/get_logs.py --job JOB_ID --auto --grep "ERROR|FAIL" -i

# Save to file
$SCRIPT_DIR/get_logs.py --job JOB_ID --auto --output /tmp/job.log
```

### Batch Log Collection (Multiple Jobs)

```bash
# All failed jobs with summary report
$SCRIPT_DIR/get_logs.py --pipeline PIPELINE_ID --batch --failed-only --summary --auto

# Specific pattern (e.g., all test jobs)
$SCRIPT_DIR/get_logs.py --pipeline PIPELINE_ID --batch --pattern "test-*" --summary --auto

# Specific stage
$SCRIPT_DIR/get_logs.py --pipeline PIPELINE_ID --batch --stage test --summary --auto

# Complete archive with aggregate log
$SCRIPT_DIR/get_logs.py --pipeline PIPELINE_ID --batch --all --aggregate --summary --auto
```

### Output Structure (Batch Mode)

```
/tmp/gitlab-logs-PIPELINE_ID/
├── summary.txt          # Overview report - READ THIS FIRST
├── manifest.json        # Metadata for automation
├── aggregate.log        # All logs combined (if --aggregate)
├── by-status/
│   ├── failed/          # Failed job logs
│   └── success/         # Successful job logs
├── by-stage/
│   ├── build/           # Build stage logs
│   └── test/            # Test stage logs
└── all/                 # All logs flat
```

### Post-Collection Analysis

```bash
# View summary
cat /tmp/gitlab-logs-PIPELINE_ID/summary.txt

# Search for errors across all logs
grep -r "ERROR\|FAIL" /tmp/gitlab-logs-PIPELINE_ID/all/

# Compare failed vs successful job
diff /tmp/gitlab-logs-PIPELINE_ID/by-status/failed/job-123.log \
     /tmp/gitlab-logs-PIPELINE_ID/by-status/success/job-456.log
```

## Key Options Reference

| Option | Description |
|--------|-------------|
| `--job ID` | Single job by ID |
| `--job-name NAME` | Find job by name in pipeline |
| `--pipeline ID` | Target pipeline (required for batch/job-name) |
| `--auto` | Auto-detect project from git remote |
| `--batch` | Enable batch mode (multiple jobs) |
| `--failed-only` | Only failed jobs |
| `--pattern GLOB` | Match job names (e.g., `test-*`) |
| `--stage STAGE` | Filter by stage name |
| `--all` | All jobs in pipeline |
| `--summary` | Generate summary report |
| `--aggregate` | Combine all logs into one file |
| `--tail N` | Last N lines only |
| `--grep PATTERN` | Filter with regex |
| `-i` | Case-insensitive grep |
| `--output FILE` | Save to specific file |
| `--parallel N` | Parallel downloads (default: 5, max: 10) |

## Finding Pipeline/Job IDs

If you need to find the pipeline or job ID first:

```bash
# List recent pipelines
$SCRIPT_DIR/list_pipelines.py --auto

# Get latest pipeline ID
PIPELINE_ID=$($SCRIPT_DIR/list_pipelines.py --auto --latest)

# Show pipeline jobs
$SCRIPT_DIR/monitor_status.py --pipeline PIPELINE_ID --auto --show-jobs
```

## Authentication

Uses standard GitLab authentication (same as git):
1. `GITLAB_TOKEN` environment variable
2. `~/.netrc` file
3. `~/.git-credentials` file

## Examples by Use Case

**"Get the error from that failed job"**
```bash
$SCRIPT_DIR/get_logs.py --job 12345 --auto --grep "ERROR|Exception" -i --tail 200
```

**"Download all failed logs from pipeline 67890"**
```bash
$SCRIPT_DIR/get_logs.py --pipeline 67890 --batch --failed-only --summary --auto
cat /tmp/gitlab-logs-67890/summary.txt
```

**"Get logs from all ca-cert test jobs"**
```bash
$SCRIPT_DIR/get_logs.py --pipeline 67890 --batch --pattern "ca-cert:*" --summary --auto
```

**"Archive the complete pipeline for investigation"**
```bash
$SCRIPT_DIR/get_logs.py --pipeline 67890 --batch --all --aggregate --summary --auto
tar -czf pipeline-67890.tar.gz /tmp/gitlab-logs-67890/
```
