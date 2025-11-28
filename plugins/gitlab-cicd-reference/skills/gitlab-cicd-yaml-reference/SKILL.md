---
name: gitlab-cicd-yaml-reference
description: "Reference documentation for the gitlab-cicd-architect agent. Contains YAML syntax, pipeline architecture, caching strategies, optimization patterns, variables reference, and troubleshooting guides. NOT for direct use - always use the gitlab-cicd-architect agent instead."
---

# GitLab CI/CD YAML Reference

> **Note:** This skill is a reference library for the `gitlab-cicd-architect` agent. Do not invoke directly - use the agent for GitLab CI/CD tasks.

This skill provides comprehensive reference documentation for advanced GitLab CI/CD configuration, pipeline architecture, and optimization patterns.

## Contents

This skill contains reference material for:
- Core YAML keywords and job configuration
- DAG pipelines and parallel execution
- Caching strategies and artifact management
- DRY patterns with extends, anchors, and includes
- Predefined and custom variables
- Troubleshooting common issues

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

- **`references/01-yaml-syntax-reference.md`** - Core YAML keywords, job configuration, rules, workflow, and script handling
- **`references/02-pipeline-architecture.md`** - DAG pipelines, parallel execution, parent-child/multi-project pipelines
- **`references/03-caching-and-artifacts.md`** - Cache strategies, artifact management, and optimization patterns
- **`references/04-yaml-optimization.md`** - DRY patterns with extends, anchors, includes, and !reference tags
- **`references/05-variables-reference.md`** - Predefined variables, custom variables, and variable handling
- **`references/06-troubleshooting.md`** - Common issues, debugging techniques, and error resolution

## Common Variables

| Variable | Purpose |
|----------|---------|
| `CI_PIPELINE_SOURCE` | Trigger type (push, merge_request_event, schedule) |
| `CI_COMMIT_BRANCH` | Branch name (empty for tags) |
| `CI_DEFAULT_BRANCH` | Repository default branch |
| `CI_MERGE_REQUEST_ID` | MR ID (if merge request pipeline) |
| `CI_JOB_TOKEN` | Auth token for API/registry |

## Best Practices Summary

### Pipeline Design
1. **Fail fast** - Put quick validation jobs early
2. **Use DAG** - `needs` keyword for parallel execution
3. **Cache aggressively** - Use file-based keys

### Configuration Quality
1. **DRY configuration** - Use extends, includes, and !reference
2. **Explicit rules** - Avoid relying on defaults
3. **Pin versions** - Include refs, image tags

### Security
1. **Mask secrets** - All sensitive values
2. **Protect production credentials** - Protected variables
3. **Minimize variable scope** - Job-level when possible

## Common Pitfalls

1. **Duplicate pipelines** - Missing workflow rules for MR + push scenarios
2. **Cache key collisions** - Using branch name alone without file-based invalidation
3. **Stage bottlenecks** - Not using `needs` for independent job chains
4. **Artifact bloat** - Not setting expire_in or being too broad with paths

## Version Requirements

Some features require specific GitLab versions:
- `cache:fallback_keys` - GitLab 15.8+
- `needs:parallel:matrix` - GitLab 14.10+
- `rules:exists:project` - GitLab 16.9+

Always verify feature availability for your GitLab version.
