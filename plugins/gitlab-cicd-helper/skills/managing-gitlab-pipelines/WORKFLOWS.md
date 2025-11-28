# Common Workflows

## Contents
- [Find and Work with Existing Pipelines](#workflow-0-find-and-work-with-existing-pipelines)
- [Trigger and Monitor Pipeline](#workflow-1-trigger-and-monitor-pipeline)
- [Trigger with Variables and Launch Manual Jobs](#workflow-2-trigger-with-variables-and-launch-manual-jobs)
- [Batch Launch Jobs by Pattern](#workflow-3-batch-launch-jobs-by-pattern)
- [Troubleshoot Failed Jobs](#workflow-4-troubleshoot-failed-jobs)
- [Batch Log Collection and Analysis](#workflow-5-batch-log-collection-and-analysis)
- [Best Practices](#best-practices)

## Workflow 0: Find and Work with Existing Pipelines

**When user says:** "Show me recent pipelines", "Find the failed pipeline", "What's the status of the latest pipeline", "List pipelines on main branch", "Debug the pipeline that ran earlier"

### Scenario 1: Find recent pipelines

```bash
cd /path/to/repo

# List recent pipelines (default: 10)
./scripts/list_pipelines.py --auto

# Output:
# ================================================================================
# 📋 Recent Pipelines
# ================================================================================
#
# ✅ Pipeline #12345
#    Branch: main
#    Status: success
#    Created: 2h ago
#    🔗 https://gitlab.com/group/project/-/pipelines/12345
#
# ❌ Pipeline #12344
#    Branch: main
#    Status: failed
#    Created: 5h ago
#
# 💡 Quick actions for latest pipeline #12345:
#    Monitor:  ./scripts/monitor_status.py --pipeline 12345 --auto --watch
#    Jobs:     ./scripts/launch_jobs.py --pipeline 12345 --auto --batch
#    Logs:     ./scripts/get_logs.py --pipeline 12345 --auto --batch --failed-only --summary
```

### Scenario 2: Find and debug a failed pipeline

```bash
cd /path/to/repo

# Find failed pipelines on main branch
./scripts/list_pipelines.py --auto --status failed --ref main

# Pick the pipeline ID from the list and investigate
PIPELINE_ID=12344

# Check status and jobs
./scripts/monitor_status.py --pipeline $PIPELINE_ID --auto --show-jobs

# Get failed job logs
./scripts/get_logs.py --pipeline $PIPELINE_ID --batch --failed-only --summary --auto
```

### Scenario 3: Work with the latest pipeline (scripting)

```bash
cd /path/to/repo

# Get the latest pipeline ID directly
PIPELINE_ID=$(./scripts/list_pipelines.py --auto --latest)

# Now use it with other scripts
./scripts/monitor_status.py --pipeline $PIPELINE_ID --auto --watch
./scripts/launch_jobs.py --pipeline $PIPELINE_ID --batch --pattern "test-*"
```

### Scenario 4: Filter pipelines by multiple criteria

```bash
cd /path/to/repo

# Find running pipelines
./scripts/list_pipelines.py --auto --status running

# Find scheduled pipelines
./scripts/list_pipelines.py --auto --source schedule

# Find pipelines triggered by specific user
./scripts/list_pipelines.py --auto --username john.doe

# Combine filters
./scripts/list_pipelines.py --auto --status failed --ref main --limit 5

# JSON output for scripting
./scripts/list_pipelines.py --auto --status failed --json | jq '.[0].id'
```

## Workflow 1: Trigger and Monitor Pipeline

**When user says:** "Trigger a pipeline", "Start a CI run", "Run the pipeline and monitor it", "Start pipeline on [branch]"

```bash
cd /path/to/repo

# 1. Trigger pipeline
PIPELINE_OUTPUT=$(./scripts/trigger_pipeline.py --auto --ref main)
# Output:
# ✅ Pipeline #24 created successfully
# 🔗 https://gitlab.example.com/your-org/your-project/-/pipelines/12345

PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')
echo "Pipeline ID: $PIPELINE_ID"
# Output: 12345

# 2. Monitor with watch mode (auto-shows progress, running jobs, status changes)
./scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --watch
# Output (refreshes every 5s):
# Pipeline #12345
# Status: running
# Progress: 15/90 jobs (17%)
#    ▶️ 3 running | ✅ 5 success | ❌ 2 failed | ⚙️ 15 manual | ◯ 65 created
#
# 🔄 Currently Running (3):
#    ▶️ build-backend [build] (1m 15s)
#    ▶️ test-integration [test] (45s)
#    ▶️ deploy-staging [deploy] (30s)
#
# ✨ Recently Changed (2):
#    ✅ build-frontend → success (was ▶️ running)
#    ❌ test-unit → failed (was ▶️ running)

# Watch mode automatically provides:
# - Real-time progress tracking (completion %, status breakdown)
# - Currently running jobs with execution durations
# - Recently changed jobs (status transitions between refreshes)
# - Full job visibility (no need for --show-jobs flag)
```

## Workflow 2: Trigger with Variables and Launch Manual Jobs

**When user says:** "Deploy to [environment]", "Run [specific] tests", "Launch manual jobs"

```bash
cd /path/to/repo

# 1. Trigger pipeline with optional variables
PIPELINE_OUTPUT=$(./scripts/trigger_pipeline.py --auto --ref main \
  --var ENVIRONMENT=staging \
  --var DEBUG=true)
PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')

# 2. Wait for pipeline to initialize (5-10 seconds)
sleep 10

# 3. Launch specific manual job by exact name
./scripts/launch_jobs.py \
  --pipeline $PIPELINE_ID --job-name "deploy-staging"

# 4. Monitor jobs
./scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --show-jobs
```

## Workflow 3: Batch Launch Jobs by Pattern

**When user says:** "Run all [category] jobs", "Launch test suite", "Start integration tests"

```bash
cd /path/to/repo

# 1. Trigger pipeline
PIPELINE_OUTPUT=$(./scripts/trigger_pipeline.py --auto --ref main)
PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')

# 2. Wait for pipeline initialization
sleep 10

# 3. Launch jobs matching pattern
# Adapt pattern to your project's job naming convention:
# - All tests: --pattern "test-*"
# - Specific suite: --pattern "integration:*"
# - Environment-specific: --pattern "deploy-staging*"
./scripts/launch_jobs.py \
  --pipeline $PIPELINE_ID --batch --pattern "YOUR-PATTERN-*"

# 4. Monitor progress with pattern-aware watch (stops when YOUR jobs complete!)
./scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --watch --watch-pattern "YOUR-PATTERN-*"

# This stops automatically when all YOUR-PATTERN-* jobs complete,
# even if the pipeline has 80+ other unrelated jobs still running.
# Result: Watch stops in 1-2 minutes instead of waiting indefinitely!
```

### Pattern-Aware Monitoring (Smart Watch)

When launching specific jobs by pattern, use `--watch-pattern` to automatically stop monitoring when those jobs complete.

**Traditional approach (waits for entire pipeline)**:
```bash
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "test-*"
./scripts/monitor_status.py --pipeline 12345 --auto --watch
# Problem: Waits for all 80 pipeline jobs, not just the 10 test jobs!
```

**Smart approach (stops when pattern jobs complete)**:
```bash
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "test-*"
./scripts/monitor_status.py --pipeline 12345 --auto --watch --watch-pattern "test-*"
# Solution: Stops automatically when all test-* jobs complete (1-2 min)
# Ignores other manual/created jobs you didn't launch!
```

**Benefits**:
- ✅ Targeted monitoring - only track jobs you care about
- ✅ Faster feedback - stops when YOUR jobs complete
- ✅ Better agent UX - agent knows when the task is done
- ✅ Works with all pattern types (prefix, suffix, wildcards)

**Use cases**:
- Testing specific suites: `--watch-pattern "integration:*"`
- Environment deployments: `--watch-pattern "deploy-staging*"`
- CA cert validation: `--watch-pattern "ca-cert:*"`
- Any batch launch operation where you used `--pattern`

## Workflow 4: Troubleshoot Failed Jobs

**When user asks:** "Why did this job fail?", "Show me the error logs", "Debug CI failure", "What went wrong with [job name]?"

```bash
# 1. Get pipeline status
./scripts/monitor_status.py \
  --pipeline 12345 --auto --show-jobs

# 2. Identify failed job ID from output
# 3. Get logs for failed job
./scripts/get_logs.py \
  --job 67890 --auto --tail 100
```

## Workflow 5: Batch Log Collection and Analysis

**When user asks:** "Get all failed job logs", "Analyze test failures", "Archive pipeline logs", "Debug multiple jobs"

### Scenario 1: Debug all failed jobs

```bash
cd /path/to/repo
PIPELINE_ID=12345

# 1. Collect logs from all failed jobs with summary
./scripts/get_logs.py \
  --pipeline $PIPELINE_ID --batch --failed-only \
  --grep "ERROR|FAIL|Exception" \
  --summary --auto

# 2. Review summary report
cat /tmp/gitlab-logs-$PIPELINE_ID/summary.txt

# 3. Examine specific failed job
cd /tmp/gitlab-logs-$PIPELINE_ID/by-status/failed
less job-456-test-integration.log

# 4. Search across all failed logs
grep -r "Database connection" /tmp/gitlab-logs-$PIPELINE_ID/all/
```

### Scenario 2: Complete pipeline archive for investigation

```bash
PIPELINE_ID=12345

# 1. Collect ALL logs with aggregate file
./scripts/get_logs.py \
  --pipeline $PIPELINE_ID --batch --all \
  --aggregate --summary \
  --output-dir /tmp/investigation-$PIPELINE_ID \
  --auto

# 2. Create searchable archive
cd /tmp/investigation-$PIPELINE_ID
tar -czf pipeline-$PIPELINE_ID-logs.tar.gz all/

# 3. Share with team or attach to issue
# Archive contains organized logs + summary + manifest
```

### Scenario 3: Analyze specific stage failures

```bash
PIPELINE_ID=12345

# 1. Get logs from test stage only
./scripts/get_logs.py \
  --pipeline $PIPELINE_ID --batch --stage test \
  --summary --auto

# 2. View test stage jobs by status
ls -lh /tmp/gitlab-logs-$PIPELINE_ID/by-stage/test/

# 3. Find common failure patterns
grep -h "FAILED" /tmp/gitlab-logs-$PIPELINE_ID/by-stage/test/*.log | sort | uniq -c
```

### Scenario 4: Pattern-based log collection

```bash
PIPELINE_ID=12345

# 1. Collect logs matching pattern (e.g., CA cert tests)
./scripts/get_logs.py \
  --pipeline $PIPELINE_ID --batch \
  --pattern "ca-cert:*" \
  --summary --auto

# 2. Review summary showing all CA cert test results
cat /tmp/gitlab-logs-$PIPELINE_ID/summary.txt

# 3. Compare failed vs successful tests
diff \
  /tmp/gitlab-logs-$PIPELINE_ID/by-status/failed/job-123-ca-cert-ubuntu.log \
  /tmp/gitlab-logs-$PIPELINE_ID/by-status/success/job-456-ca-cert-alpine.log
```

## Best Practices

### Project Resolution
- **Always use `--auto`** when working in a git repository directory
- Scripts auto-detect project from git remote (no manual ID lookup needed)
- Only use explicit `--project ID` when outside a git repository

### Pipeline Triggering
- Use descriptive variable names: `--var ENVIRONMENT=prod` not `--var E=p`
- Wait 5-10 seconds after triggering before launching manual jobs
- Check pipeline status before launching jobs to ensure initialization

### Batch Operations
- Use patterns for selective launching: `--pattern "deploy-*"`
- Use `--status` filter to target specific job states
- Always verify job list before batch launch (shows count and names)

### Monitoring
- Use `--watch` mode for long-running pipelines/jobs
- `--show-jobs` flag is auto-enabled in watch mode (no need to specify both)
- Set appropriate `--interval` (default: 5s) to avoid API rate limits
- Use Ctrl+C to stop watch mode gracefully
- Watch mode provides real-time progress tracking with completion percentage and status breakdown

### Log Analysis
- Use `--tail N` to limit output for long logs
- Use `--grep` with regex for filtering errors/warnings
- Save large logs to file with `--output` for analysis
- Use `--summary` to get overview before diving into individual logs
- Use `--aggregate` for single-file analysis (easier to search/share)
- Use `--parallel N` to speed up large batch collections (max: 10)
