---
name: gitlab-cicd-helper
description: Trigger GitLab pipelines, launch manual jobs, monitor status, and retrieve logs. Use when user needs CI/CD operations, pipeline automation, or deployment workflows. Keywords: pipeline, trigger, manual job, CI/CD, deploy, status, logs, trace, GitLab
allowed-tools: Bash, Read
---

# GitLab CI/CD Helper

You are a GitLab CI/CD operations specialist. This skill provides comprehensive GitLab pipeline management through efficient Python scripts.

## Core Capabilities

1. **Pipeline Triggering**: Start pipelines with variables/inputs on any branch
2. **Manual Job Launching**: Trigger manual/delayed jobs (single or batch operations)
3. **Status Monitoring**: Real-time pipeline and job status with optional watch mode
4. **Log Retrieval**: Download and analyze job traces with filtering
5. **Auto Project Resolution**: Automatically determine project IDs from git remotes
6. **Pipeline Intelligence**: Full pipeline awareness with proper pagination (finds ALL jobs, not just 20!)
7. **Config Analysis**: Compare .gitlab-ci.yml configuration vs actual pipeline state

## Architecture

**python-gitlab Throughout**: All scripts use the official python-gitlab library instead of curl
- **Automatic Pagination**: Uses `get_all=True` to fetch ALL jobs (critical fix - was only getting first 20!)
- **Better Error Handling**: Native exception handling instead of parsing HTTP status codes
- **Type Safety**: Python objects instead of raw JSON dictionaries
- **Modern Pattern**: `uv run --script` with inline dependencies (PEP 723)

**Core Modules**:
- `gitlab_config.py`: Centralized configuration and authentication
  - **Standard authentication**: GITLAB_TOKEN → .netrc → .git-credentials (same as official GitLab tools)
  - **Auto-detection**: GitLab URL detected from git remote
  - **Project-specific tokens**: .gitlab-trigger-token for project-level configuration
- `pipeline_analyzer.py`: Pipeline intelligence and job awareness with proper pagination
- `project_resolver.py`: Git remote URL parsing and project ID resolution
  - **Simplified approach**: Direct path lookup (python-gitlab handles URL encoding internally)
  - **Smart fallback**: Searches by project name if direct lookup fails (helpful with restricted PAT tokens)
  - **No manual encoding**: Removed redundant URL encoding logic (python-gitlab does this automatically)

## Prerequisites

**uv Package Manager (REQUIRED)**:
All scripts use `uv run --script` with inline dependencies (PEP 723).
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`
- No manual `pip install python-gitlab` needed - uv handles dependencies automatically
- Verify: `uv --version`

**Authentication (CRITICAL - Standard Methods)**:

All scripts use **industry-standard authentication** (same as official GitLab CLI tools):

**PAT Token (Required for API operations)**:

Priority order (first found wins):
1. **Environment variable** (recommended for CI/CD):
   ```bash
   export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'
   # OR
   export PAT_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'
   ```

2. **~/.netrc file** (standard HTTP authentication):
   ```bash
   machine gitlab.pitchblackcompany.com
   login oauth2
   password glpat-xxxxxxxxxxxxxxxxxxxxx
   ```
   File permissions: `chmod 600 ~/.netrc`

3. **~/.git-credentials** (Git credential helper):
   ```bash
   https://oauth2:glpat-xxxxxxxxxxxxxxxxxxxxx@gitlab.pitchblackcompany.com
   ```
   File permissions: `chmod 600 ~/.git-credentials`

**Trigger Token (Optional - project-specific)**:

Priority order:
1. **Environment variable**:
   ```bash
   export GITLAB_TRIGGER_TOKEN='glptt-xxxxxxxxxxxxxxxxxxxxx'
   ```

2. **Project-specific file** (recommended):
   ```bash
   echo 'glptt-xxxxxxxxxxxxxxxxxxxxx' > .gitlab-trigger-token
   chmod 600 .gitlab-trigger-token
   echo '.gitlab-trigger-token' >> .gitignore
   ```

**GitLab URL (Optional)**:
- Auto-detected from git remote
- Override with: `export GITLAB_URL='https://your-gitlab-instance.com'`
- Defaults to: `https://gitlab.com`

**Token Requirements**:
- PAT token must have **`api` scope**
- Create at: GitLab → User Settings → Access Tokens
- Trigger tokens are project-specific (optional, rarely needed)

## Script Locations

Scripts are located in the skill directory at: `./scripts/`

When this skill is active, use scripts with relative paths:
- `./scripts/trigger_pipeline.py` - Trigger pipelines
- `./scripts/launch_jobs.py` - Launch manual jobs
- `./scripts/monitor_status.py` - Monitor pipeline/job status
- `./scripts/get_logs.py` - Retrieve job traces

**Note**: All examples below use relative paths (e.g., `./scripts/trigger_pipeline.py`) which work from the skill base directory provided in the skill context.

## Usage Instructions

### 1. Trigger Pipeline

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

### 2. Launch Manual Jobs

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

### 3. Monitor Status

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

**Watch Mode Output Example:**
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

**Show full pipeline structure (NEW - uses PipelineAnalyzer):**
```bash
./scripts/monitor_status.py \
  --pipeline 12345 --auto --structure
# Shows total jobs, jobs by status, jobs by stage with proper pagination
```

**Compare .gitlab-ci.yml config vs actual state (NEW):**
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

### 4. Get Job Logs

#### Single Job Mode

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

#### Batch Mode (NEW!)

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

**Batch Mode Output Structure:**
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

## Common Workflows

### Workflow 1: Trigger and Monitor Pipeline
When user says: "Trigger a pipeline", "Start a CI run", "Run the pipeline and monitor it", "Start pipeline on [branch]"

```bash
cd /path/to/repo

# 1. Trigger pipeline
PIPELINE_OUTPUT=$(./scripts/trigger_pipeline.py --auto --ref main)
PIPELINE_ID=$(echo "$PIPELINE_OUTPUT" | grep -oP 'Pipeline #\d+ \(ID: \K\d+')
echo "Pipeline ID: $PIPELINE_ID"

# 2. Monitor with watch mode (auto-shows progress, running jobs, status changes)
./scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --watch
# Watch mode automatically provides:
# - Real-time progress tracking (completion %, status breakdown)
# - Currently running jobs with execution durations
# - Recently changed jobs (status transitions between refreshes)
# - Full job visibility (no need for --show-jobs flag)
```

### Workflow 2: Trigger with Variables and Launch Manual Jobs
When user says: "Deploy to [environment]", "Run [specific] tests", "Launch manual jobs"

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

### Workflow 3: Batch Launch Jobs by Pattern
When user says: "Run all [category] jobs", "Launch test suite", "Start integration tests"

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

# 4. Monitor progress (watch mode auto-enables job display and progress tracking)
./scripts/monitor_status.py \
  --pipeline $PIPELINE_ID --auto --watch
```

**Common Pattern Examples:**
- Test suites: `--pattern "test-*"` (jobs starting with "test-")
- Category prefix: `--pattern "integration:*"` (jobs in "integration:" category)
- Deployment jobs: `--pattern "deploy-*"` (all deployment-related jobs)
- Environment suffix: `--pattern "*-staging"` (staging environment jobs)
- Complex pattern: `--pattern "*e2e*"` (any job containing "e2e")

### Workflow 4: Troubleshoot Failed Jobs
When user asks: "Why did this job fail?", "Show me the error logs", "Debug CI failure", "What went wrong with [job name]?"

```bash
# 1. Get pipeline status
./scripts/monitor_status.py \
  --pipeline 12345 --auto --show-jobs

# 2. Identify failed job ID from output
# 3. Get logs for failed job
./scripts/get_logs.py \
  --job 67890 --auto --tail 100
```

### Workflow 5: Batch Log Collection and Analysis (NEW!)
When user asks: "Get all failed job logs", "Analyze test failures", "Archive pipeline logs", "Debug multiple jobs"

```bash
cd /path/to/repo

# Scenario 1: Debug all failed jobs
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

```bash
# Scenario 2: Complete pipeline archive for investigation
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

```bash
# Scenario 3: Analyze specific stage failures
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

```bash
# Scenario 4: Pattern-based log collection (e.g., CA cert tests)
PIPELINE_ID=12345

# 1. Collect logs matching pattern
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

**Batch Mode Best Practices:**
- Use `--summary` to get overview before diving into individual logs
- Use `--aggregate` for single-file analysis (easier to search/share)
- Use `--parallel N` to speed up large batch collections (max: 10)
- Use `--grep` to pre-filter logs and highlight errors in summary
- Check `manifest.json` for programmatic access to metadata

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
- Use `--watch` mode for long-running pipelines/jobs (automatically shows progress, running jobs, and status changes)
- `--show-jobs` flag is auto-enabled in watch mode (no need to specify both)
- Set appropriate `--interval` (default: 5s) to avoid API rate limits
- Use Ctrl+C to stop watch mode gracefully
- Watch mode provides real-time progress tracking with completion percentage and status breakdown

### Log Analysis
- Use `--tail N` to limit output for long logs
- Use `--grep` with regex for filtering errors/warnings
- Save large logs to file with `--output` for analysis

## Understanding Job Statuses

GitLab jobs transition through different statuses that affect when they can be launched:

### Job Status Types

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

### Best Practices for Launching Jobs

1. **Use default status filter** (`--status manual`)
   - Only targets jobs that are ready to launch
   - Avoids "Unplayable Job" errors

2. **Check pipeline status first**
   ```bash
   # See which jobs are ready
   ./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs
   ```

3. **Understand your pipeline dependencies**
   - Check `.gitlab-ci.yml` for stage order
   - Jobs in later stages wait for earlier stages
   - Use `needs: []` for independent manual jobs

4. **Handle "Unplayable Job" errors**
   - Script will suggest jobs with status "manual"
   - Wait for dependencies OR modify job definition
   - Use `--status manual` instead of `--status created`

## Error Handling

### Token Validation Failures
**Error**: "Token file not found" or "Missing required tokens"

**Solution**: Instruct user to create `~/.claude/.cicd-tokens`:
```bash
touch ~/.claude/.cicd-tokens
chmod 600 ~/.claude/.cicd-tokens
# Add tokens:
# TRIGGER_TOKEN="glptt-xxxxx"
# PAT_TOKEN="glpat-xxxxx"
```

### Project Resolution Failures
**Error**: "Failed to get git remote URL"

**Solution**:
- Ensure user is in a git repository: `git status`
- Verify remote exists: `git remote -v`
- Use explicit `--project ID` if not in git repo

### Job Not Found
**Error**: "No manual jobs found" or "Job 'name' not found"

**Solution**:
- Verify pipeline has initialized (wait 10-15 seconds after trigger)
- Check job status with monitor_status.py first
- Use correct `--status` filter (created, manual, pending, etc.)
- Verify pattern matches job names exactly

### Unplayable Job (400 Error)
**Error**: "400 Bad request - Unplayable Job"

**Cause**: Job status is "created" (waiting for dependencies) or not in a launchable state

**Solution**:
- Check job status: `./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs`
- Launch only jobs with status "manual": `--batch --status manual`
- Wait for previous stages to complete (jobs will transition to "manual")
- OR add `needs: []` to job definition in `.gitlab-ci.yml` to bypass dependencies
- Script will automatically suggest available manual jobs when this occurs

### API Errors (403, 401)
**Error**: "401 Unauthorized" or "403 Forbidden"

**Solution**:
- Verify PAT_TOKEN has `api` scope
- Check if token expired (regenerate in GitLab)
- Ensure user has permissions for the project

## Troubleshooting

### Script Not Found
Ensure full path is used:
```bash
./scripts/trigger_pipeline.py
```

### Permission Denied
Make scripts executable:
```bash
chmod +x ./scripts/*.py
```

### Python Import Errors
Scripts use relative imports. Always run from any directory (they handle paths internally).

### No Logs Available
Job hasn't run yet or has no output. Wait for job to start or check job status first.

## Success Indicators

- ✅ Token validation passes
- ✅ Project auto-resolved (shows project name and ID)
- ✅ Pipeline triggered (shows pipeline ID and URL)
- ✅ Jobs launched (shows job IDs)
- ✅ Status displays with emojis and formatting
- ✅ Logs retrieved successfully

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

## Important Notes

1. **uv required** - Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Pagination fixed** - Now finds ALL jobs (e.g., 90 jobs, not just 20!)
3. **Always validate tokens first** - Scripts do this automatically
4. **Use --auto for project resolution** - Most convenient when in git repo
5. **Wait after triggering** - Pipeline needs time to initialize jobs (2-10 seconds)
6. **Batch operations are powerful** - Use patterns for selective launching
7. **Watch mode is interactive** - User can Ctrl+C to stop
8. **Logs may not exist yet** - Jobs must start running first
9. **python-gitlab handles dependencies** - uv downloads python-gitlab automatically per script
10. **Pipeline awareness** - Use --structure and --compare flags for deep insights

## Key Improvements in v2.0

- **PAGINATION FIX**: Uses `get_all=True` to fetch ALL jobs (critical bug fix!)
- **python-gitlab Throughout**: Official library instead of curl for reliability
- **uv Package Manager**: Modern dependency management with inline script dependencies
- **Pipeline Intelligence**: New PipelineAnalyzer provides holistic pipeline awareness
- **Config Parsing**: Can compare .gitlab-ci.yml with actual pipeline state
- **Find Jobs by Name**: No need to remember job IDs
- **Simplified Project Resolution**: Direct path lookup (no manual URL encoding) with smart search fallback
- **Standard Authentication**: Industry-standard auth (GITLAB_TOKEN, .netrc, .git-credentials) - same as official GitLab tools
- **Batch Log Collection (NEW!)**: Retrieve logs from multiple jobs in parallel with organized output, summary reports, and aggregate files

You are now ready to provide professional GitLab CI/CD automation support with full pipeline intelligence and comprehensive log analysis!