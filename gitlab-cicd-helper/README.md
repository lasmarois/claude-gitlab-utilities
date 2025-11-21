# GitLab CI/CD Helper Plugin

Claude Code plugin for GitLab CI/CD automation via python-gitlab. Trigger pipelines, launch manual jobs, monitor status with real-time progress tracking, and retrieve logs.

## Features

- **Pipeline Triggering**: Start pipelines on any branch with variables
- **Batch Job Launching**: Trigger manual/delayed jobs by pattern or individually
- **Real-time Monitoring**: Watch pipelines with job progress tracking (%, ETA, runtime)
- **Pattern-aware Watch**: Automatically terminates when pattern-matched jobs complete
- **Log Retrieval**: Download and filter job traces with grep/tail support
- **Auto Project Resolution**: Detects project ID from git remotes
- **Secure Token Management**: Uses standard GitLab authentication (GITLAB_TOKEN, .netrc, .git-credentials)

## Installation

Installed via Claude Code plugin marketplace. See root README for setup details.

**Authentication**: Configure using standard GitLab authentication methods:
- Environment variable: `GITLAB_TOKEN` (required for API operations)
- Git credentials: `~/.netrc` or `~/.git-credentials`
- Optional: `.gitlab-trigger-token` in project root (for pipeline triggering)
- See [Authentication Guide](../README.md#authentication) for details

## How It Works

This plugin provides two components that work together:

### Skill: managing-gitlab-pipelines
Python-based toolkit providing core GitLab API operations:
- Pipeline triggering with variables
- Manual job launching (single or batch)
- Real-time status monitoring with watch mode
- Job log retrieval and filtering

### Agent: gitlab-cicd-specialist
Intelligent orchestrator for complex multi-step workflows:
- Automatically activates for phrases like "trigger and monitor", "debug failed jobs", "analyze test failures"
- Coordinates multi-step operations (trigger → launch → monitor → analyze)
- Provides strategic guidance and root cause analysis
- Leverages batch operations for efficient parallel processing

## Usage with Claude Code

### Simple Operations (Skill)
Ask Claude to perform individual CI/CD operations:
- "Trigger a pipeline on branch develop"
- "Show me the status of pipeline 12345"
- "Get logs for job 67890"

### Complex Workflows (Agent)
Ask for orchestrated multi-step workflows:
- "Trigger the pipeline and monitor until complete"
- "Launch all CA cert tests and watch for failures"
- "Debug why the test stage is failing"
- "Analyze all failed jobs in pipeline 12345"

Claude automatically chooses the right component based on your request.

## Workflow Examples

### Trigger and Monitor Pipeline
```bash
# Trigger pipeline with variable
./scripts/trigger_pipeline.py --auto --ref main --var ENVIRONMENT=staging

# Monitor with real-time updates
./scripts/monitor_status.py --pipeline 12345 --auto --watch --show-jobs
```

### Batch Launch Pattern-Matched Jobs
```bash
# Launch all CA cert test jobs
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "ca-cert:*"

# Monitor will automatically terminate when pattern-matched jobs complete
./scripts/monitor_status.py --pipeline 12345 --auto --watch --pattern "ca-cert:*"
```

### Debug Failed Jobs
```bash
# Check pipeline status
./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs

# Get filtered logs
./scripts/get_logs.py --job 67890 --auto --tail 100 --grep "ERROR"
```

**Note**: Scripts use `uv run --script` with inline dependencies (PEP 723). No manual pip installation required.

## Script Reference

### trigger_pipeline.py
Start a pipeline with optional variables.

Key options: `--auto` (resolve project from git), `--ref BRANCH`, `--var KEY=VALUE`

### launch_jobs.py
Launch manual/delayed jobs individually or by pattern.

Key options: `--pipeline ID`, `--batch`, `--pattern PATTERN`, `--job-name NAME`

### monitor_status.py
Monitor pipeline/job status with real-time progress tracking.

Key options: `--pipeline ID`, `--watch`, `--show-jobs`, `--pattern PATTERN` (auto-terminate when matched jobs complete)

Features: Job progress (%, ETA, runtime), status tracking, pattern-aware termination

### get_logs.py
Retrieve and filter job logs.

Key options: `--job ID`, `--tail N`, `--grep PATTERN`, `-i` (ignore case), `-C N` (context lines)

See `./scripts/<script> --help` for complete options.

## Key Capabilities

### Real-time Progress Tracking
monitor_status.py provides detailed job progress:
- Completion percentage and ETA
- Job runtime and duration
- Status updates (pending, running, success, failed)

### Pattern-aware Watch Mode
Automatically terminates monitoring when all pattern-matched jobs complete:
```bash
# Launches ca-cert jobs and watches only those
./scripts/launch_jobs.py --pipeline 12345 --batch --pattern "ca-cert:*"
./scripts/monitor_status.py --pipeline 12345 --watch --pattern "ca-cert:*"
# Exits when all ca-cert:* jobs finish
```

### Auto Project Resolution
Detects GitLab project ID from git remotes - no manual project ID lookup needed:
```bash
cd /path/to/repo
./scripts/trigger_pipeline.py --auto --ref main
```

## Troubleshooting

**Authentication errors**: Verify GITLAB_TOKEN is set or credentials exist in .netrc/.git-credentials (see root README)

**Project resolution fails**: Ensure you're in a git repo with GitLab remote, or use `--project ID` explicitly

**No manual jobs found**: Wait 10-15 seconds after pipeline trigger for jobs to initialize

**Pattern not matching**: Use `--show-jobs` to list available job names and verify pattern syntax

## Architecture

Built on python-gitlab library with modular components:
- Token management and validation
- GitLab API client wrapper
- Auto project ID resolution from git remotes
- Terminal output formatting with progress tracking
- Pattern-aware monitoring and termination logic

Self-contained design with no external dependencies beyond system Python3 and python-gitlab.

## Requirements

- Python 3.6+
- python-gitlab library
- Git (for auto project resolution)
- GitLab instance with API access

## License

MIT License
