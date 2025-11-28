# Setup and Configuration

## Contents
- [Prerequisites](#prerequisites)
- [Authentication](#authentication)
- [Architecture Overview](#architecture-overview)
- [Script Locations](#script-locations)

## Prerequisites

**uv Package Manager (REQUIRED)**:
All scripts use `uv run --script` with inline dependencies (PEP 723).
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`
- No manual `pip install python-gitlab` needed - uv handles dependencies automatically
- Verify: `uv --version`

**Python**: 3.9 or higher (typically pre-installed)

**Compatibility:**
- python-gitlab: >=4.0.0 (automatically installed by uv)
- PyYAML: >=6.0 (automatically installed by uv)
- GitLab API: Tested with GitLab 15.x and 16.x
- Works with gitlab.com and self-hosted GitLab instances
- Supports Community Edition (CE) and Enterprise Edition (EE)

## Authentication

All scripts use **industry-standard authentication** (same as official GitLab CLI tools).

### PAT Token (Required for API operations)

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

### Trigger Token (Optional - project-specific)

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

### GitLab URL (Optional)

- Auto-detected from git remote
- Override with: `export GITLAB_URL='https://your-gitlab-instance.com'`
- Defaults to: `https://gitlab.com`

### Token Requirements

- PAT token must have **`api` scope**
- Create at: GitLab → User Settings → Access Tokens
- Trigger tokens are project-specific (optional, rarely needed)

## Architecture Overview

**python-gitlab Throughout**: All scripts use the official python-gitlab library instead of curl

- **Automatic Pagination**: Uses `get_all=True` to fetch ALL jobs (critical fix - was only getting first 20!)
- **Better Error Handling**: Native exception handling instead of parsing HTTP status codes
- **Type Safety**: Python objects instead of raw JSON dictionaries
- **Modern Pattern**: `uv run --script` with inline dependencies (PEP 723)

### Core Modules

**gitlab_config.py**: Centralized configuration and authentication
- **Standard authentication**: GITLAB_TOKEN → .netrc → .git-credentials (same as official GitLab tools)
- **Auto-detection**: GitLab URL detected from git remote
- **Project-specific tokens**: .gitlab-trigger-token for project-level configuration

**pipeline_analyzer.py**: Pipeline intelligence and job awareness with proper pagination

**project_resolver.py**: Git remote URL parsing and project ID resolution
- **Simplified approach**: Direct path lookup (python-gitlab handles URL encoding internally)
- **Smart fallback**: Searches by project name if direct lookup fails (helpful with restricted PAT tokens)
- **No manual encoding**: Removed redundant URL encoding logic (python-gitlab does this automatically)

## Script Locations

Scripts are located in the skill directory at: `./scripts/`

When this skill is active, all commands use relative paths from the skill base directory:
- `./scripts/trigger_pipeline.py` - Trigger pipelines
- `./scripts/launch_jobs.py` - Launch manual jobs
- `./scripts/monitor_status.py` - Monitor pipeline/job status
- `./scripts/get_logs.py` - Retrieve job traces
