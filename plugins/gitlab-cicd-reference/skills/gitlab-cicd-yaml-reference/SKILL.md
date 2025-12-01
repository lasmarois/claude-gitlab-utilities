---
name: gitlab-cicd-yaml-reference
description: "REQUIRED reference for validating GitLab CI/CD YAML syntax and providing accurate recommendations. Contains authoritative documentation on keywords, rules, workflow, DAG pipelines, caching strategies, and troubleshooting patterns. MUST be loaded before analyzing .gitlab-ci.yml files or reviewing pipeline configurations to ensure recommendations follow current GitLab best practices. Invoked by gitlab-cicd-architect agent."
---

# GitLab CI/CD YAML Reference

> **Note:** This skill is invoked by the `gitlab-cicd-architect` agent to provide comprehensive reference documentation.

This skill provides comprehensive reference documentation for advanced GitLab CI/CD configuration, pipeline architecture, and optimization patterns.

## Contents

This skill contains comprehensive reference material for:

### Core Configuration
- Core YAML keywords and job configuration
- DAG pipelines and parallel execution
- Caching strategies and artifact management
- DRY patterns with extends, anchors, and includes
- Predefined and custom variables
- Troubleshooting common issues

### Advanced Topics
- CI/CD components and inputs (spec:inputs)
- Secrets management and OIDC authentication
- Runner types, executors, and configuration
- Environments, deployments, and protected environments
- Testing, reports, and security scanning
- Advanced keywords (release, pages, merge trains)

## Quick Reference

### Essential Keywords

| Keyword | Purpose |
|---------|---------|
| `script` | Commands to execute (required) |
| `rules` | Conditional job execution |
| `needs` | DAG dependencies |
| `cache` | Dependency caching |
| `artifacts` | Job output storage |
| `extends` | Configuration inheritance |
| `include` | External configuration |
| `environment` | Deployment target |
| `secrets` | External secrets (Vault, Azure, GCP, AWS) |
| `id_tokens` | OIDC authentication tokens |
| `release` | Create GitLab releases |
| `spec:inputs` | Typed parameters for components |

### Critical Patterns

**Prevent Duplicate Pipelines:**
```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS && $CI_PIPELINE_SOURCE == "push"
      when: never
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH
```

**DAG Pipeline:**
```yaml
test:
  needs: [build]  # Start immediately when build completes
```

**Optimized Caching:**
```yaml
cache:
  key:
    files: [package-lock.json]
  paths: [node_modules/]
  policy: pull-push
```

## Reference Documentation

For detailed information, consult these reference files in this skill:

### Core Configuration
- **`references/01-yaml-syntax-reference.md`** - Core YAML keywords, job configuration, rules, workflow, and script handling
- **`references/02-pipeline-architecture.md`** - DAG pipelines, parallel execution, parent-child/multi-project pipelines
- **`references/03-caching-and-artifacts.md`** - Cache strategies, artifact management, and optimization patterns
- **`references/04-yaml-optimization.md`** - DRY patterns with extends, anchors, includes, and !reference tags
- **`references/05-variables-reference.md`** - Predefined variables, custom variables, and variable handling
- **`references/06-troubleshooting.md`** - Common issues, debugging techniques, and error resolution

### Advanced Topics
- **`references/07-components-and-inputs.md`** - CI/CD components, spec:inputs, component catalog, typed parameters
- **`references/08-secrets-and-security.md`** - Secrets keyword, Vault/Azure/GCP/AWS integration, id_tokens, OIDC
- **`references/09-runners-reference.md`** - Runner types, executors, tags, GitLab-hosted vs self-managed
- **`references/10-environments-and-deployments.md`** - Environment configuration, dynamic environments, protected environments
- **`references/11-testing-and-reports.md`** - JUnit reports, code coverage, security scanning, test visualization
- **`references/12-advanced-keywords.md`** - release, pages, inherit, identity, merge trains, and more

## Common Variables

| Variable | Purpose |
|----------|---------|
| `CI_PIPELINE_SOURCE` | Trigger type (push, merge_request_event, schedule) |
| `CI_COMMIT_BRANCH` | Branch name (empty for tags) |
| `CI_DEFAULT_BRANCH` | Repository default branch |
| `CI_MERGE_REQUEST_ID` | MR ID (if merge request pipeline) |
| `CI_JOB_TOKEN` | Auth token for API/registry |
| `CI_ENVIRONMENT_NAME` | Current environment name |
| `CI_ENVIRONMENT_URL` | Environment URL |
| `CI_RUNNER_TAGS` | Runner tags (comma-separated) |

## Best Practices Summary

### Pipeline Design
1. **Fail fast** - Put quick validation jobs early
2. **Use DAG** - `needs` keyword for parallel execution
3. **Cache aggressively** - Use file-based keys
4. **Use components** - Modular, reusable configurations

### Configuration Quality
1. **DRY configuration** - Use extends, includes, and !reference
2. **Explicit rules** - Avoid relying on defaults
3. **Pin versions** - Include refs, image tags, component versions
4. **Use typed inputs** - Validate parameters at pipeline creation

### Security
1. **Mask secrets** - All sensitive values
2. **Protect production credentials** - Protected variables and environments
3. **Minimize variable scope** - Job-level when possible
4. **Use OIDC** - id_tokens for cloud provider authentication
5. **External secrets** - HashiCorp Vault, Azure Key Vault, GCP/AWS Secrets Manager

### Deployments
1. **Use environments** - Track deployments per environment
2. **Protect production** - Required approvals, protected environments
3. **Auto-stop review apps** - Prevent resource waste
4. **Use deployment tiers** - Proper classification

## Common Pitfalls

1. **Duplicate pipelines** - Missing workflow rules for MR + push scenarios
2. **Cache key collisions** - Using branch name alone without file-based invalidation
3. **Stage bottlenecks** - Not using `needs` for independent job chains
4. **Artifact bloat** - Not setting expire_in or being too broad with paths
5. **Secrets in variables** - Use external secrets (Vault, etc.) for sensitive data
6. **Floating versions** - Pin component versions in production
7. **Missing test reports** - Always upload JUnit reports even on failure

## Version Requirements

Some features require specific GitLab versions:

### Core Features
- `cache:fallback_keys` - GitLab 15.8+
- `needs:parallel:matrix` - GitLab 14.10+
- `rules:exists:project` - GitLab 16.9+

### Components & Inputs
- `spec:inputs` - GitLab 15.11+
- `spec:inputs:type: array` - GitLab 16.11+
- `include:component` - GitLab 16.0+
- CI/CD Catalog - GitLab 16.0+

### Security & Authentication
- `secrets` keyword - GitLab Premium 13.4+
- `id_tokens` (OIDC) - GitLab 15.7+
- AWS Secrets Manager - GitLab 16.3+

### Advanced Features
- `pages:publish` - GitLab 16.1+
- `manual_confirmation` - GitLab 15.11+
- `workflow:auto_cancel:on_job_failure` - GitLab 16.1+

Always verify feature availability for your GitLab version.
