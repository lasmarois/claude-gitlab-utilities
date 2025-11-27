# GitLab CI/CD Reference

Claude Code plugin providing expert knowledge for GitLab CI/CD YAML configuration and pipeline architecture.

## Usage

Ask Claude about GitLab CI/CD topics:

- "Help me configure a DAG pipeline for my Node.js project"
- "How do I prevent duplicate pipelines for MRs?"
- "Optimize my cache configuration for faster builds"
- "Set up multi-project pipeline triggers"

Claude will use the **GitLab CI/CD Architect** agent to provide expert guidance.

## Components

| Component | Description |
|-----------|-------------|
| **Agent** (`gitlab-cicd-architect`) | Expert in GitLab CI/CD design and optimization |
| **Skill** (`gitlab-cicd-yaml-reference`) | Comprehensive reference documentation |

## Reference Topics

- YAML syntax and job configuration
- Pipeline architecture (DAG, parallel, multi-project)
- Caching strategies and artifact management
- DRY patterns (extends, includes, !reference)
- Variables (predefined and custom)
- Troubleshooting common issues

## Installation

```bash
/plugin install gitlab-cicd-reference@claude-gitlab-utilities
```
