# Contributing to Claude GitLab Utilities

## Adding New Plugins

To add a new plugin to this marketplace:

### 1. Create Plugin Structure

```bash
mkdir -p your-plugin/.claude-plugin
mkdir -p your-plugin/skills/your-skill
```

### 2. Create Plugin Metadata

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "Brief description of your plugin",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "keywords": ["gitlab", "ci-cd", "your-keywords"],
  "license": "MIT"
}
```

### 3. Create Skill Definition

Create `skills/your-skill/SKILL.md` with YAML frontmatter:

```markdown
---
name: your-skill
description: Concise skill description with key capabilities and keywords
allowed-tools: Bash, Read, Write
---

# Your Skill Name

You are a specialist in [domain]. This skill provides [capabilities].

## Core Capabilities

1. **Feature 1**: Description
2. **Feature 2**: Description

## Usage Instructions

[Detailed instructions for using the skill]
```

### 4. Add Scripts (if applicable)

If your skill uses scripts, organize them under `skills/your-skill/scripts/`:

```bash
mkdir -p your-plugin/skills/your-skill/scripts
```

Use `uv run --script` with inline dependencies (PEP 723) for self-contained scripts:

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "python-gitlab"]
# ///

import sys
# Your script code
```

### 5. Update Marketplace Configuration

Edit `.claude-plugin/marketplace.json` and add your plugin:

```json
{
  "name": "claude-gitlab-utilities",
  "plugins": [
    {
      "name": "your-plugin",
      "description": "Brief plugin description",
      "source": "./your-plugin",
      "strict": false
    }
  ]
}
```

### 6. Test Locally

```bash
# Reload marketplace
/plugin marketplace update claude-gitlab-utilities

# Install your plugin
/plugin install your-plugin@claude-gitlab-utilities

# Test functionality
# Ask Claude to use your new skill
```

## Plugin Best Practices

### Skills vs Agents

**Skills** provide low-level tools and capabilities:
- Execute specific operations (API calls, script execution)
- Provide technical foundation (scripts, libraries, utilities)
- Focus on "how" to do something
- Example: `managing-gitlab-pipelines` skill provides Python scripts for GitLab API operations

**Agents** orchestrate complex workflows:
- Coordinate multi-step operations using skills
- Provide strategic guidance and decision-making
- Focus on "what" to accomplish and "when" to use different approaches
- Example: `gitlab-cicd-specialist` agent orchestrates trigger → launch → monitor → analyze workflows

**When to provide both:**
- Complex domains requiring multi-step workflows
- Operations needing strategic decision-making
- Scenarios with multiple valid approaches requiring judgment

**When skills alone are sufficient:**
- Simple, single-purpose operations
- Direct tool wrappers without orchestration needs
- Well-defined workflows with no branching logic

### Skill Descriptions
- Use concise, keyword-rich descriptions
- Include primary capabilities and use cases
- Follow format: "Tool/library providing X, Y, and Z capabilities"

### Authentication
- Use standard authentication methods (environment variables, config files)
- Document token requirements clearly
- Support multiple auth methods with fallback priority

### Script Design
- Use `uv run --script` with inline dependencies
- Follow PEP 723 for dependency declarations
- Include `--help` flag with comprehensive usage info
- Use `--auto` flag for automatic resolution when possible

### Documentation
- Keep README focused on plugin capabilities and usage
- Reference marketplace README for installation/setup
- Include workflow examples for common use cases
- Provide troubleshooting section with common issues

**For plugins with both skills and agents:**
- Add "How It Works" section explaining both components
- Show when the agent activates vs when the skill is used directly
- Provide examples of simple operations (skill) vs complex workflows (agent)
- Document the agent's decision-making and orchestration capabilities

### Testing
- Test all scripts individually before integration
- Verify skill activation with natural language queries
- Test authentication with all supported methods
- Validate pattern matching and filtering features

## Code Style

- Use clear, descriptive variable names
- Add comments for complex logic
- Include error handling with helpful messages
- Format code consistently (use `black` or similar)

## Submitting Changes

1. Fork the repository at https://github.com/lasmarois/claude-gitlab-utilities
2. Create a feature branch: `git checkout -b feature/your-plugin`
3. Add your plugin following the structure above
4. Test thoroughly with local installation
5. Commit with clear message: `git commit -m "Add your-plugin with X capabilities"`
6. Push to your fork: `git push origin feature/your-plugin`
7. Open a Pull Request with:
   - Clear description of plugin capabilities
   - Testing performed
   - Any special requirements or dependencies

## Getting Help

- Review existing plugins (e.g., `gitlab-cicd-helper`) as examples
- Check Claude Code documentation for plugin development
- Open an issue for questions or clarifications
- Join discussions in GitHub Issues

## License

All contributions are subject to the MIT License. By contributing, you agree to license your work under the same terms.
