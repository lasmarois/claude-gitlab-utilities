# Claude GitLab Utilities

GitLab CI/CD automation plugin marketplace for Claude Code. Trigger pipelines, launch jobs, monitor status, and retrieve logs using natural language.

## Available Plugins

### gitlab-cicd-helper

Comprehensive GitLab CI/CD automation with intelligent workflow orchestration.

**Components:**
- **Skill** (`managing-gitlab-pipelines`): Python scripts for pipeline operations, job launching, monitoring, and log retrieval
- **Agent** (`gitlab-cicd-specialist`): Orchestrates complex multi-step workflows with strategic guidance and failure analysis

**Key Features:**
- Pipeline triggering with variables on any branch
- Batch job launching with pattern matching
- Real-time monitoring with progress tracking and pattern-aware termination
- Parallel log collection with organized output and summary reports
- Auto project resolution from git remotes
- Standard GitLab authentication (GITLAB_TOKEN, .netrc, .git-credentials)

**Documentation**: [plugins/gitlab-cicd-helper/README.md](plugins/gitlab-cicd-helper/README.md)

## Installation

### From GitHub

```bash
/plugin marketplace add lasmarois/claude-gitlab-utilities
/plugin install gitlab-cicd-helper@claude-gitlab-utilities
```

### Local Development

```bash
git clone https://github.com/nmarois/claude-gitlab-utilities.git ~/dev/claude-gitlab-utilities
/plugin marketplace add ~/dev/claude-gitlab-utilities
/plugin install gitlab-cicd-helper@claude-gitlab-utilities
```

## Authentication

Plugins use standard GitLab authentication methods (same as official GitLab CLI tools):

**Option 1: Environment Variable (recommended)**
```bash
export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'
```

**Option 2: ~/.netrc file**
```bash
machine gitlab.example.com
login oauth2
password glpat-xxxxxxxxxxxxxxxxxxxxx
```
Set permissions: `chmod 600 ~/.netrc`

**Option 3: ~/.git-credentials**
```bash
https://oauth2:glpat-xxxxxxxxxxxxxxxxxxxxx@gitlab.example.com
```
Set permissions: `chmod 600 ~/.git-credentials`

**Token Requirements:**
- Create at: GitLab → User Settings → Access Tokens
- Required scope: `api`
- Optional: Set `GITLAB_URL` environment variable to override default GitLab instance

**Optional: Project-Specific Trigger Token**

For project-specific pipeline triggering, create `.gitlab-trigger-token`:

```bash
echo 'glptt-xxxxxxxxxxxxxxxxxxxxx' > .gitlab-trigger-token
chmod 600 .gitlab-trigger-token
echo '.gitlab-trigger-token' >> .gitignore
```

Create trigger tokens at: Project Settings → CI/CD → Pipeline triggers

## Usage

Use natural language commands in Claude Code:

```
"Trigger a pipeline on the main branch for this project"
"Launch all manual jobs matching pattern deploy-*"
"Monitor the latest pipeline until it completes"
"Get the logs for job 67890 and filter for ERROR"
```

## Contributing

Want to add a new plugin or improve existing ones? See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE)

## Support

[GitHub Issues](https://github.com/lasmarois/claude-gitlab-utilities/issues)
