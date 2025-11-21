# Troubleshooting Guide

## Contents
- [Authentication Issues](#authentication-issues)
- [Project Resolution Failures](#project-resolution-failures)
- [Job Launch Errors](#job-launch-errors)
- [API Errors](#api-errors)
- [General Issues](#general-issues)
- [Success Indicators](#success-indicators)

## Authentication Issues

### Token Validation Failures

**Error**: "Token file not found" or "Missing required tokens"

**Solution**: Instruct user to create proper authentication:
```bash
# Option 1: Environment variable (recommended)
export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'

# Option 2: ~/.netrc file
cat >> ~/.netrc << EOF
machine gitlab.pitchblackcompany.com
login oauth2
password glpat-xxxxxxxxxxxxxxxxxxxxx
EOF
chmod 600 ~/.netrc

# Option 3: ~/.git-credentials
echo 'https://oauth2:glpat-xxxxxxxxxxxxxxxxxxxxx@gitlab.pitchblackcompany.com' >> ~/.git-credentials
chmod 600 ~/.git-credentials
```

### Token Scope Issues

**Error**: "401 Unauthorized" or "403 Forbidden"

**Solution**:
- Verify PAT_TOKEN has `api` scope
- Check if token expired (regenerate in GitLab)
- Ensure user has permissions for the project
- Create new token at: GitLab → User Settings → Access Tokens

## Project Resolution Failures

### Git Remote Not Found

**Error**: "Failed to get git remote URL"

**Solution**:
- Ensure user is in a git repository: `git status`
- Verify remote exists: `git remote -v`
- Use explicit `--project ID` if not in git repo
- Check that git remote URL is valid

### Project ID Not Found

**Error**: "Project not found" or "404 Not Found"

**Solution**:
- Verify project ID is correct
- Check user has access to the project
- Use `--auto` flag when in git repository
- Try searching by project name if direct lookup fails

## Job Launch Errors

### Job Not Found

**Error**: "No manual jobs found" or "Job 'name' not found"

**Solution**:
- Verify pipeline has initialized (wait 10-15 seconds after trigger)
- Check job status with monitor_status.py first:
  ```bash
  ./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs
  ```
- Use correct `--status` filter (created, manual, pending, etc.)
- Verify pattern matches job names exactly

### Unplayable Job (400 Error)

**Error**: "400 Bad request - Unplayable Job"

**Cause**: Job status is "created" (waiting for dependencies) or not in a launchable state

**Solution**:
1. Check job status:
   ```bash
   ./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs
   ```

2. Launch only jobs with status "manual":
   ```bash
   ./scripts/launch_jobs.py --pipeline 12345 --batch --status manual
   ```

3. Wait for previous stages to complete (jobs will transition to "manual")

4. OR add `needs: []` to job definition in `.gitlab-ci.yml` to bypass dependencies

5. Script will automatically suggest available manual jobs when this occurs

### Job Status Confusion

**Understanding when jobs can be launched:**

- **created**: Job is waiting for dependencies (previous stages) to complete
  - Cannot be launched yet
  - Wait for dependencies OR add `needs: []` to job definition

- **manual**: Job is ready to be launched manually
  - Can be launched immediately
  - Default status filter for launch_jobs.py

- **pending**: Job is queued and waiting for a runner
  - Already triggered, cannot launch again

- **running**: Job is currently executing
  - Cannot launch (already running)

- **success/failed**: Job completed
  - Cannot re-launch (use retry or new pipeline)

**Best practice**: Use default status filter (`--status manual`) to only target jobs ready to launch

## API Errors

### Rate Limiting

**Error**: "429 Too Many Requests"

**Solution**:
- Increase `--interval` value in watch mode (default: 5s, try: 10s)
- Reduce number of parallel requests in batch mode
- Wait a few minutes before retrying

### Network Timeouts

**Error**: "Connection timeout" or "Request timeout"

**Solution**:
- Check network connectivity
- Verify GitLab instance is accessible
- Check firewall/proxy settings
- Try again after a moment

### Invalid Pipeline/Job ID

**Error**: "Pipeline not found" or "Job not found"

**Solution**:
- Verify ID is correct (check GitLab UI)
- Ensure pipeline/job exists and user has access
- Check that ID is a number, not a URL or other format

## General Issues

### Script Not Found

**Error**: "No such file or directory"

**Solution**: Ensure full path is used:
```bash
./scripts/trigger_pipeline.py
```

### Permission Denied

**Error**: "Permission denied" when executing script

**Solution**: Make scripts executable:
```bash
chmod +x ./scripts/*.py
```

### uv Not Installed

**Error**: "uv: command not found"

**Solution**: Install uv package manager:
```bash
# Option 1: Official installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Option 2: pip
pip install uv

# Verify installation
uv --version
```

### Python Import Errors

**Error**: "ModuleNotFoundError" or import failures

**Solution**:
- Scripts use inline dependencies (PEP 723) with uv
- Ensure uv is installed: `uv --version`
- No manual `pip install` needed - uv handles dependencies automatically
- Run scripts with `uv run --script` (scripts do this automatically)

### No Logs Available

**Error**: "No logs available" or empty log output

**Cause**: Job hasn't run yet or has no output

**Solution**:
- Wait for job to start running
- Check job status first:
  ```bash
  ./scripts/monitor_status.py --job 67890 --auto
  ```
- Verify job has actually executed (not just created/manual)
- Some jobs may legitimately have no output

### Pipeline Initialization Delay

**Issue**: Manual jobs not appearing immediately after trigger

**Explanation**: GitLab pipelines need time to initialize (create jobs, parse config, etc.)

**Solution**:
- Wait 5-10 seconds after triggering before launching jobs
- Check pipeline status to confirm initialization:
  ```bash
  ./scripts/monitor_status.py --pipeline 12345 --auto --show-jobs
  ```
- Longer delay (15-30 seconds) for complex pipelines with many jobs

### Watch Mode Interruption

**Question**: "What happens if I Ctrl+C during watch mode?"

**Answer**:
Watch mode can be safely interrupted with Ctrl+C at any time:
- **Pipelines continue running**: Watch is read-only, no impact on GitLab
- **Jobs continue running**: Stopping the monitor doesn't stop the jobs
- **No data loss**: You're just stopping the monitoring display
- **Can resume anytime**: Start a new watch command to see current state

**To resume monitoring:**
```bash
./scripts/monitor_status.py --pipeline 12345 --auto --watch
# Picks up where you left off, showing current state
```

**Use case**: Interrupt watch to check logs, then resume monitoring
```bash
# Start watching
./scripts/monitor_status.py --pipeline 12345 --auto --watch

# Ctrl+C to stop when you see a failure

# Check the failed job
./scripts/get_logs.py --job 67890 --auto --tail 50

# Resume watching if needed
./scripts/monitor_status.py --pipeline 12345 --auto --watch
```

## Success Indicators

Successful operations show these indicators:

- ✅ Token validation passes
- ✅ Project auto-resolved (shows project name and ID)
- ✅ Pipeline triggered (shows pipeline ID and URL)
- ✅ Jobs launched (shows job IDs)
- ✅ Status displays with emojis and formatting
- ✅ Logs retrieved successfully
- ✅ Watch mode shows progress tracking
- ✅ Batch operations complete without errors

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
