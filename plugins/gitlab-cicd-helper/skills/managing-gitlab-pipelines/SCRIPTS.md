# Script Reference

## Contents
- [trigger_pipeline.py](#trigger_pipelinepy)
- [launch_jobs.py](#launch_jobspy)
- [monitor_status.py](#monitor_statuspy)
- [get_logs.py](#get_logspy)
- [Job Status Types](#job-status-types)

## trigger_pipeline.py

Trigger pipelines with variables/inputs on any branch.

### Basic Usage

**Auto-resolve project from current directory:**
```bash
cd /path/to/repo
./scripts/trigger_pipeline.py --auto --ref main
```

**With variables:**
```bash
./scripts/trigger_pipeline.py --auto --ref main \
  --var ENVIRONMENT=production \
  --var DEBUG=true
```

**Explicit project:**
```bash
./scripts/trigger_pipeline.py \
  --project 1603 --ref main
```

### Options

- `--auto`: Auto-detect project from git remote (recommended when in git repo)
- `--project ID`: Explicit project ID (numeric)
- `--project-path PATH`: Project path (e.g., 'group/subgroup/project')
- `--ref BRANCH`: Branch, tag, or commit SHA to trigger pipeline on
- `--var KEY=VALUE`: Pipeline variable (can specify multiple times)

### Best Practices

- Use descriptive variable names: `--var ENVIRONMENT=prod` not `--var E=p`
- Wait 5-10 seconds after triggering before launching manual jobs
- Check pipeline status before launching jobs to ensure initialization

## launch_jobs.py

Launch manual/delayed jobs (single or batch operations).

### Basic Usage

**Single job by name:**
```bash
./scripts/launch_jobs.py \
  --pipeline 12345 --job-name "deploy-production"
```

**Batch launch with pattern matching:**
```bash
# Launch jobs matching a specific pattern
./scripts/launch_jobs.py \
  --pipeline 12345 --batch --pattern "test-*"

# Launch all deployment jobs
./scripts/launch_jobs.py \
  --pipeline 12345 --batch --pattern "deploy-*"
```

**Launch all manual jobs (PROPERLY PAGINATED - finds ALL jobs!):**
```bash
./scripts/launch_jobs.py \
  --pipeline 12345 --batch
# CRITICAL FIX: Now finds all 90 jobs, not just first 20!
# Uses python-gitlab with get_all=True for automatic pagination
```

**Launch jobs by status:**
```bash
./scripts/launch_jobs.py \
  --pipeline 12345 --batch --status created
```

### Options

- `--pipeline ID`: Pipeline ID containing the jobs
- `--job-name NAME`: Launch specific job by exact name
- `--batch`: Enable batch mode (launch multiple jobs)
- `--pattern GLOB`: Pattern to match job names (e.g., "test-*", "*-staging")
- `--status STATUS`: Filter by job status (default: manual)

### Common Patterns

Patterns use glob-style wildcards:
- `*` matches any characters (including none)
- `?` matches any single character
- `[abc]` matches any character in the set

**Examples:**
- Test suites: `--pattern "test-*"` (jobs starting with "test-")
- Category prefix: `--pattern "integration:*"` (jobs in "integration:" category)
- Deployment jobs: `--pattern "deploy-*"` (all deployment-related jobs)
- Environment suffix: `--pattern "*-staging"` (staging environment jobs)
- Contains substring: `--pattern "*e2e*"` (any job containing "e2e")
- Multiple wildcards: `--pattern "test-*-integration"` (specific pattern)
- Single character: `--pattern "test-??"` (test-01, test-02, but not test-001)

### Best Practices

- Use patterns for selective launching: `--pattern "deploy-*"`
- Use `--status` filter to target specific job states
- Always verify job list before batch launch (shows count and names)
- Default status filter (`--status manual`) targets jobs ready to launch

## monitor_status.py

Real-time pipeline and job status with optional watch mode.

### Basic Usage

**Pipeline overview with jobs:**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --show-jobs
```

**Watch pipeline until completion (with auto-enabled progress tracking):**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --watch --interval 10
# Watch mode automatically shows:
# - Progress summary (completion %, job counts by status)
# - Currently running jobs with durations
# - Recently changed jobs (status transitions)
# - Full job list (--show-jobs auto-enabled)
```

### Watch Mode Output Example

```
Pipeline #12345
Status: running
Progress: 9/90 jobs (10%)
   ▶️ 2 running | ✅ 3 success | ❌ 6 failed | ⚙️ 13 manual | ◯ 66 created

🔄 Currently Running (2):
   ▶️ ca-cert:integration-test [test-docker] (2m 30s)
   ▶️ ca-cert:volume-propagation [test-docker] (2m 32s)

✨ Recently Changed (6):
   ❌ ca-cert:ubuntu → failed (was ▶️ running)
   ❌ ca-cert:golang → failed (was ▶️ running)
   ...
```

### Advanced Features

**Show full pipeline structure:**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --structure
# Shows total jobs, jobs by status, jobs by stage with proper pagination
```

**Compare .gitlab-ci.yml config vs actual state:**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --compare
# Parses .gitlab-ci.yml and compares with actual pipeline
# Shows which jobs were created vs expected from config
```

**Job details:**
```bash
./scripts/monitor_status.py \
  --job 67890 --auto
```

**Pattern-aware watch (stops when specific jobs complete):**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --watch --watch-pattern "test-*"
# Stops automatically when all test-* jobs complete
# Ignores other manual/created jobs you didn't launch!
```

### Options

- `--pipeline ID`: Pipeline ID to monitor
- `--job ID`: Job ID to monitor (alternative to --pipeline)
- `--auto`: Auto-detect project from git remote
- `--show-jobs`: Display all jobs in pipeline
- `--watch`: Enable watch mode (auto-refresh until completion)
- `--watch-pattern GLOB`: Stop watch when pattern-matching jobs complete
- `--interval SECONDS`: Refresh interval for watch mode (default: 5)
- `--structure`: Show pipeline structure analysis
- `--compare`: Compare .gitlab-ci.yml with actual pipeline

### Best Practices

- Use `--watch` mode for long-running pipelines/jobs (automatically shows progress)
- `--show-jobs` flag is auto-enabled in watch mode (no need to specify both)
- Set appropriate `--interval` (default: 5s) to avoid API rate limits
- Use Ctrl+C to stop watch mode gracefully
- Use `--watch-pattern` when monitoring specific job sets

## get_logs.py

Download and analyze job traces with filtering.

### Single Job Mode

**Full logs by job ID:**
```bash
./scripts/get_logs.py \
  --job 67890 --auto
```

**Get logs by job name (finds job in pipeline):**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --job-name "deploy-production" --auto
# No need to know job ID - finds it by name!
```

**Last N lines:**
```bash
./scripts/get_logs.py \
  --job 67890 --auto --tail 50
```

**Filter for errors:**
```bash
./scripts/get_logs.py \
  --job 67890 --auto --grep "ERROR" --ignore-case
```

**Save to file:**
```bash
./scripts/get_logs.py \
  --job 67890 --auto --output /tmp/job_logs.txt
```

### Batch Mode

**Get logs from all failed jobs:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --failed-only --summary --auto
# Creates organized directory with all failed job logs
# Generates summary report with error analysis
```

**Get logs from specific stage:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --stage test --auto
# Collects logs from all jobs in "test" stage
```

**Get logs matching pattern:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --pattern "ca-cert:*" --auto
# Pattern matching with glob-style wildcards
```

**Complete pipeline archive with aggregate log:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --all --aggregate --summary --auto
# Fetches ALL jobs in pipeline
# Creates aggregate log file with all logs
# Generates comprehensive summary report
```

**Filter batch logs with grep:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --failed-only \
  --grep "ERROR|FAIL|Exception" --summary --auto
# Batch mode with per-job filtering
# Summary includes error match counts
```

**Custom output directory:**
```bash
./scripts/get_logs.py \
  --pipeline 12345 --batch --status failed --status canceled \
  --output-dir /tmp/my-pipeline-logs \
  --parallel 8 --summary --auto
# Multiple status filters
# Custom output location
# 8 parallel fetches for speed
```

### Batch Mode Output Structure

```
/tmp/gitlab-logs-12345/
├── summary.txt                    # Summary report
├── manifest.json                  # Metadata (JSON)
├── aggregate.log                  # All logs (if --aggregate)
├── by-status/
│   ├── failed/                    # Failed job logs
│   ├── success/                   # Successful job logs
│   └── ...
├── by-stage/
│   ├── build/                     # Build stage logs
│   ├── test/                      # Test stage logs
│   └── ...
└── all/                           # All logs in one place
    ├── job-123-build-backend.log
    ├── job-456-test-integration.log
    └── ...
```

### Options

**Single Job Mode:**
- `--job ID`: Job ID to fetch logs from
- `--pipeline ID`: Pipeline ID (with --job-name)
- `--job-name NAME`: Find job by name in pipeline
- `--auto`: Auto-detect project from git remote
- `--tail N`: Show last N lines only
- `--grep PATTERN`: Filter logs with regex pattern
- `--ignore-case, -i`: Case-insensitive grep
- `--context N, -C N`: Show N lines before and after grep matches
- `--line-numbers, -n`: Show line numbers with output
- `--output FILE`: Save logs to file

**Batch Mode:**
- `--batch`: Enable batch mode (multiple jobs)
- `--all`: Fetch all jobs in pipeline
- `--failed-only`: Fetch only failed jobs
- `--status STATUS`: Filter by job status (can specify multiple)
- `--stage STAGE`: Filter by pipeline stage
- `--pattern GLOB`: Pattern to match job names
- `--max-jobs N`: Maximum number of jobs to process (safety limit)
- `--no-empty`: Skip jobs with no logs (default: true)
- `--aggregate`: Create single aggregate log file
- `--summary`: Generate summary report
- `--output-dir DIR`: Custom output directory
- `--parallel N`: Number of parallel downloads (default: 5, max: 10)

### Best Practices

- Use `--summary` to get overview before diving into individual logs
- Use `--aggregate` for single-file analysis (easier to search/share)
- Use `--parallel N` to speed up large batch collections (max: 10)
- Use `--grep` to pre-filter logs and highlight errors in summary
- Check `manifest.json` for programmatic access to metadata
- Use `--tail N` to limit output for long logs
- Save large logs to file with `--output` for analysis

## Job Status Types

GitLab jobs transition through different statuses that affect when they can be launched.

**created** - Job is waiting for dependencies (previous stages) to complete
- Cannot be launched with `/play` endpoint
- Must wait for required jobs/stages to finish
- Or add `needs: []` to job definition to bypass dependencies

**manual** - Job is ready to be launched manually
- Can be launched immediately with `/play` endpoint
- Default status filter for `launch_jobs.py --batch`
- Most common status for manual jobs that are ready

**pending** - Job is queued and waiting for a runner
- Already triggered, waiting for execution
- Cannot be manually launched (already in queue)

**running** - Job is currently executing
- Cannot be launched (already running)

**success/failed** - Job completed
- Cannot be re-launched (use retry or new pipeline)

### When Jobs Become Launchable

Jobs with `when: manual` become launchable when:
1. All dependencies from previous stages complete
2. Job status transitions from "created" → "manual"
3. Or job has `needs: []` (no dependencies)
