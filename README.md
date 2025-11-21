# Claude GitLab Utilities

A comprehensive marketplace of GitLab automation plugins for Claude Code, providing powerful CI/CD operations, pipeline management, and DevOps workflows.

## Overview

This marketplace provides Claude Code plugins that enhance GitLab integration, enabling seamless automation of CI/CD pipelines, job management, monitoring, and logging directly from Claude Code.

## Available Plugins

### 🚀 gitlab-cicd-helper

Comprehensive GitLab CI/CD automation plugin for professional pipeline management.

**Capabilities:**
- **Pipeline Triggering**: Start pipelines with variables/inputs on any branch
- **Manual Job Launching**: Trigger manual/delayed jobs (single or batch operations)
- **Status Monitoring**: Real-time pipeline and job status with optional watch mode
- **Log Retrieval**: Download and analyze job traces with filtering
- **Auto Project Resolution**: Automatically determine project IDs from git remotes

**Use Cases:**
- Trigger deployment pipelines from within your development workflow
- Launch batch testing jobs (e.g., CA certificate tests across distributions)
- Monitor long-running pipelines with auto-refresh
- Debug failed jobs by retrieving filtered logs
- Automate multi-stage deployment workflows

**Documentation**: See [gitlab-cicd-helper/README.md](gitlab-cicd-helper/README.md)

## Installation

### Prerequisites

- Claude Code installed and configured
- GitLab tokens configured (see [Token Setup](#token-setup))

### Install from GitHub

```bash
# In Claude Code, run:
/plugin marketplace add nmarois/claude-gitlab-utilities
```

### Install from Local Development

```bash
# Clone the repository
git clone https://github.com/nmarois/claude-gitlab-utilities.git ~/dev/claude-gitlab-utilities

# In Claude Code, run:
/plugin marketplace add ~/dev/claude-gitlab-utilities
```

### Install Plugins

Once the marketplace is added, install individual plugins:

```bash
# Install the GitLab CI/CD helper
/plugin install gitlab-cicd-helper@claude-gitlab-utilities

# Verify installation
/plugin
```

## Token Setup

All plugins in this marketplace require GitLab authentication tokens.

### Create Token File

```bash
# Create token file
touch ~/.claude/.cicd-tokens
chmod 600 ~/.claude/.cicd-tokens
```

### Add Tokens

Edit `~/.claude/.cicd-tokens` and add:

```bash
TRIGGER_TOKEN="glptt-xxxxxxxxxxxxxxxxxxxxx"
PAT_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxxx"
GITLAB_URL="https://gitlab.example.com"  # Optional, defaults to gitlab.com
```

### Generate Tokens in GitLab

**Pipeline Trigger Token:**
1. Navigate to your GitLab project
2. Go to Settings → CI/CD → Pipeline triggers
3. Create a new trigger token
4. Copy the token to `TRIGGER_TOKEN`

**Personal Access Token (PAT):**
1. Go to GitLab → Preferences → Access Tokens
2. Create a new token with `api` scope
3. Copy the token to `PAT_TOKEN`

## Usage Examples

Once plugins are installed, you can use natural language commands:

### Trigger a Pipeline

```
"Trigger a pipeline on the main branch for this project"
"Start a deployment pipeline with ENVIRONMENT=staging"
```

### Launch Manual Jobs

```
"Launch all CA certificate test jobs"
"Start the deploy-production job"
"Launch all manual jobs matching pattern deploy-*"
```

### Monitor Status

```
"What's the status of pipeline 12345?"
"Monitor the latest pipeline until it completes"
"Show me all jobs in pipeline 12345"
```

### Retrieve Logs

```
"Get the logs for job 67890"
"Show me the last 50 lines of the build job"
"Filter logs for ERROR in job 67890"
```

## Plugin Development

### Directory Structure

```
claude-gitlab-utilities/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace definition
├── README.md                     # This file
└── gitlab-cicd-helper/            # Example plugin
    ├── .claude-plugin/
    │   └── plugin.json           # Plugin metadata
    ├── README.md                 # Plugin documentation
    └── skills/
        └── gitlab-cicd-helper/
            ├── SKILL.md          # Claude skill instructions
            └── scripts/          # Python utilities
                ├── trigger_pipeline.py
                ├── launch_jobs.py
                ├── monitor_status.py
                ├── get_logs.py
                └── lib/
                    ├── token_manager.py
                    ├── gitlab_client.py
                    ├── project_resolver.py
                    └── output_formatter.py
```

### Adding New Plugins

To add a new plugin to this marketplace:

1. **Create Plugin Directory**
   ```bash
   mkdir -p claude-gitlab-utilities/your-plugin/.claude-plugin
   mkdir -p claude-gitlab-utilities/your-plugin/skills/your-skill
   ```

2. **Create Plugin Metadata**
   ```bash
   # Create .claude-plugin/plugin.json
   {
     "name": "your-plugin",
     "version": "1.0.0",
     "description": "Your plugin description",
     "author": "Your Name"
   }
   ```

3. **Create Skill**
   ```bash
   # Create skills/your-skill/SKILL.md with YAML frontmatter
   ---
   name: your-skill
   description: Skill description with keywords
   allowed-tools: Bash, Read
   ---

   # Your Skill Instructions
   ```

4. **Update Marketplace**

   Edit `.claude-plugin/marketplace.json` and add to the `plugins` array:
   ```json
   {
     "name": "your-plugin",
     "description": "Your plugin description",
     "source": "./your-plugin",
     "strict": false,
     "skills": [
       "./your-plugin/skills/your-skill"
     ]
   }
   ```

5. **Test Locally**
   ```bash
   # Uninstall and reinstall marketplace
   /plugin marketplace update claude-gitlab-utilities
   /plugin install your-plugin@claude-gitlab-utilities
   ```

## Roadmap

Future plugins planned for this marketplace:

- **gitlab-mr-helper**: Merge request creation, review, and management
- **gitlab-issue-tracker**: Issue creation, labeling, and milestone tracking
- **gitlab-security-scanner**: Security scanning integration and vulnerability management
- **gitlab-deployment-manager**: Advanced deployment workflows with rollback capabilities
- **gitlab-repository-manager**: Repository settings, branch protection, and access control

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-plugin`)
3. Add your plugin following the structure above
4. Test thoroughly with local installation
5. Submit a pull request

### Contribution Guidelines

- Follow the existing plugin structure pattern
- Include comprehensive README.md for each plugin
- Ensure SKILL.md has clear, specific descriptions
- Test all scripts with realistic GitLab projects
- Document all required tokens and permissions
- Include usage examples in plugin documentation

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/nmarois/claude-gitlab-utilities/issues)
- **Documentation**: See individual plugin README files for detailed usage
- **Examples**: Check plugin directories for working examples

## Acknowledgments

- Built for [Claude Code](https://claude.com/code)
- Inspired by [claude-gitlab-tools](https://github.com/mprpic/claude-gitlab-tools)
- Community contributions welcome

## Version History

### 1.0.0 (2025-01-XX)
- Initial release
- gitlab-cicd-helper plugin with comprehensive pipeline automation
- Token-based authentication system
- Auto project resolution from git remotes
- Batch job operations with pattern matching
- Real-time monitoring with watch mode

---

**Made with ❤️ for the Claude Code community**
