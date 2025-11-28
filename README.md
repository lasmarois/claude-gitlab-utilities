# Claude GitLab Utilities

GitLab automation plugin marketplace for Claude Code. Manage pipelines, merge requests, and CI/CD configuration using natural language.

## Available Plugins

### gitlab-cicd-helper

Comprehensive GitLab CI/CD automation with intelligent workflow orchestration.

**Components:**
- **Agent** (`gitlab-cicd-specialist`): Orchestrates complex multi-step workflows with strategic guidance and failure analysis
- **Skill** (`managing-gitlab-pipelines`): Python scripts for pipeline operations, job launching, monitoring, and log retrieval

**Key Features:**
- Pipeline triggering with variables on any branch
- Batch job launching with pattern matching
- Real-time monitoring with progress tracking and pattern-aware termination
- Parallel log collection with organized output and summary reports

**Documentation**: [plugins/gitlab-cicd-helper/README.md](plugins/gitlab-cicd-helper/README.md)

---

### gitlab-cicd-reference

Expert knowledge for GitLab CI/CD YAML configuration and pipeline architecture.

**Components:**
- **Agent** (`gitlab-cicd-architect`): Expert in YAML configuration, DAG optimization, caching strategies, and troubleshooting
- **Skill** (`gitlab-cicd-yaml-reference`): Comprehensive reference documentation for .gitlab-ci.yml

**Key Features:**
- YAML syntax and job configuration reference
- DAG pipelines and parallel execution patterns
- Caching strategies and artifact management
- DRY patterns with extends, anchors, includes, !reference
- Variables reference and troubleshooting guides

**Documentation**: [plugins/gitlab-cicd-reference/README.md](plugins/gitlab-cicd-reference/README.md)

---

### gitlab-mr-helper

GitLab Merge Request management with full API integration.

**Components:**
- **Agent** (`gitlab-mr-specialist`): Expert in MR workflows, descriptions, labels, and reviewers
- **Skill** (`managing-gitlab-mrs`): Go scripts for MR creation, listing, and updates

**Key Features:**
- Create MRs with automatic branch detection and title generation
- List MRs with status icons, labels, and age formatting
- Update MR title, description, labels, or close/reopen
- Auto project resolution from git remotes

**Documentation**: [plugins/gitlab-mr-helper/README.md](plugins/gitlab-mr-helper/README.md)

---

## Installation

### From GitHub

```bash
/plugin marketplace add lasmarois/claude-gitlab-utilities
/plugin install gitlab-cicd-helper@claude-gitlab-utilities
/plugin install gitlab-cicd-reference@claude-gitlab-utilities
/plugin install gitlab-mr-helper@claude-gitlab-utilities
```

### Local Development

```bash
git clone https://github.com/lasmarois/claude-gitlab-utilities.git ~/dev/claude-gitlab-utilities
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

## Usage

Use natural language commands in Claude Code:

```
"Trigger a pipeline on the main branch"
"Launch all manual jobs matching pattern deploy-*"
"Monitor the pipeline until it completes"
"Get the logs for failed jobs"
"Help me configure a DAG pipeline"
"Create a merge request for my current branch"
"List my open merge requests"
```

## Contributing

Want to add a new plugin or improve existing ones? See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE)

## Support

[GitHub Issues](https://github.com/lasmarois/claude-gitlab-utilities/issues)
