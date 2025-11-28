# GitLab CI/CD Troubleshooting and Common Issues

> Diagnostic patterns, common problems, and solutions for CI/CD pipeline issues.

---

## Pipeline Not Created

### Symptom: No pipeline appears after push

**Check workflow:rules:**
```yaml
# Problem: Rules block all pipelines
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
      when: never

# Solution: Ensure at least one rule evaluates to true
workflow:
  rules:
    - if: $CI_COMMIT_TITLE =~ /-draft$/
      when: never
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - when: always  # Fallback
```

**Check for empty pipeline:**
```yaml
# Problem: All jobs excluded by rules
job1:
  rules:
    - if: $NEVER_TRUE_VARIABLE
      
# Solution: Ensure at least one job can run
```

**Check .gitlab-ci.yml location:**
- Must be in repository root (or custom path configured in settings)
- Filename is case-sensitive

---

## Duplicate Pipelines

### Symptom: Two pipelines for same commit

**Problem: Branch and MR pipelines both run**

```yaml
# Solution: Prevent duplicate with workflow rules
workflow:
  rules:
    # Skip branch pipeline if MR exists
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS && $CI_PIPELINE_SOURCE == "push"
      when: never
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH
```

**Problem: Jobs without rules run on both sources**

```yaml
# Problem
job:
  script: test  # Runs on all pipeline sources

# Solution: Add explicit rules
job:
  script: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
```

---

## Job Not Running

### Symptom: Job shows as "skipped" or doesn't appear

**Check rules evaluation:**
```yaml
# Debug: Add a rule that always matches to test
job:
  rules:
    - if: $DEBUG_RULES == "true"
      when: always  # For debugging
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

**Check stage exists:**
```yaml
# Problem: Job references undefined stage
stages:
  - build
  - test

deploy:
  stage: deploy  # Stage not defined!

# Solution: Add stage to stages list
stages:
  - build
  - test
  - deploy
```

**Check needs dependencies:**
```yaml
# Problem: needed job doesn't exist or was skipped
job2:
  needs: [job1]  # If job1 is skipped, job2 won't run

# Solution: Use optional
job2:
  needs:
    - job: job1
      optional: true
```

---

## YAML Syntax Errors

### Colons in scripts

```yaml
# Problem: YAML interprets colon as key:value
script:
  - curl --header "Authorization: Bearer $TOKEN"  # Error!

# Solution: Quote the entire command
script:
  - 'curl --header "Authorization: Bearer $TOKEN"'
```

### Special characters

```yaml
# Problem: Unquoted special characters
variables:
  MY_VAR: value with: colon  # Error!
  
# Solution: Quote values with special characters
variables:
  MY_VAR: "value with: colon"
```

### Multiline scripts

```yaml
# Option 1: Literal block scalar (preserves newlines)
script:
  - |
    echo "Line 1"
    echo "Line 2"
    if [ "$VAR" == "true" ]; then
      echo "Conditional"
    fi

# Option 2: Folded block scalar (joins lines)
script:
  - >
    long command
    continued here
    becomes single line
```

---

## Cache Issues

### Cache not being used

**Check key matches:**
```yaml
# Problem: Different keys between jobs
job1:
  cache:
    key: cache-v1
    
job2:
  cache:
    key: cache-v2  # Different key!
```

**Check protected branch settings:**
```yaml
# Problem: Protected branches don't share cache with unprotected
# Solution: Use unprotect option or separate keys
cache:
  key: $CI_COMMIT_REF_SLUG
  unprotect: true  # Allow unprotected branches to access
```

**Check runner configuration:**
- Distributed cache requires S3/GCS configuration
- Different runners may have separate local caches

### Stale cache

```yaml
# Solution: Use file-based keys that change with dependencies
cache:
  key:
    files:
      - package-lock.json  # Key changes when file changes
  paths:
    - node_modules/
```

---

## Artifact Issues

### Artifact not found

**Check job succeeded:**
```yaml
# Artifacts only upload on success by default
# Solution: Use when: always for debugging artifacts
artifacts:
  paths:
    - logs/
  when: always  # Upload even on failure
```

**Check dependencies:**
```yaml
# Problem: Job doesn't download artifacts
job2:
  dependencies: []  # Empty means no artifacts downloaded
  
# Solution: Specify or remove dependencies
job2:
  dependencies:
    - job1
```

**Check expire_in:**
```yaml
# Problem: Artifacts expired
artifacts:
  expire_in: 1 hour  # Too short!
  
# Solution: Increase expiration
artifacts:
  expire_in: 1 week
```

### Artifacts reports not showing

```yaml
# Problem: Report file not in artifacts:paths
artifacts:
  reports:
    junit: report.xml
  # Missing paths!
  
# Solution: Include report files in paths
artifacts:
  reports:
    junit: report.xml
  paths:
    - report.xml  # Or gl-*-report.json
```

---

## Docker Issues

### Docker daemon not available

```yaml
# Problem: Can't connect to Docker daemon
# Solution: Use docker-in-docker service properly
build:
  image: docker:24
  services:
    - name: docker:24-dind
      alias: docker
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
```

### Service not found

```yaml
# Problem: Service hostname not resolving
services:
  - name: postgres:15
    # Default hostname is 'postgres' or 'postgres-15'
    
# Solution: Use explicit alias
services:
  - name: postgres:15
    alias: db
# Now accessible at 'db:5432'
```

---

## Variable Issues

### Variable not expanding

```yaml
# Problem: Variable appears as literal text
script:
  - echo '$MY_VAR'  # Single quotes prevent expansion

# Solution: Use double quotes or no quotes
script:
  - echo "$MY_VAR"
  - echo $MY_VAR
```

### Variable not available

**Check variable scope:**
- Protected variables only in protected branches
- File variables contain path, not content
- Masked variables must meet format requirements

**Check variable origin:**
```yaml
# Problem: Variable from dotenv not available
build:
  artifacts:
    reports:
      dotenv: vars.env  # Must be in artifacts

test:
  # Only available if artifacts downloaded
  dependencies:
    - build  # Ensure this is set
```

### Variable in rules not working

```yaml
# Problem: Variables set in same job not available in rules
job:
  variables:
    MY_VAR: "value"
  rules:
    - if: $MY_VAR == "value"  # May not work as expected
    
# Solution: Use workflow or global variables for rules
variables:
  MY_VAR: "value"

job:
  rules:
    - if: $MY_VAR == "value"
```

---

## Timeout Issues

### Job times out

```yaml
# Solution 1: Increase job timeout
job:
  timeout: 2 hours
  script: long_running_task

# Solution 2: Use script timeout for early termination
job:
  timeout: 2h
  variables:
    RUNNER_SCRIPT_TIMEOUT: 1h30m  # Script stops, leaving time for artifacts
```

### after_script times out

```yaml
# Problem: after_script has 5 minute default timeout
# Solution: Increase timeout
variables:
  RUNNER_AFTER_SCRIPT_TIMEOUT: 15m
```

---

## Debugging Techniques

### View merged configuration

```yaml
# Use CI Lint in GitLab UI: CI/CD > Editor > Validate
# Or API:
# GET /projects/:id/ci/lint?include_merged_yaml=true
```

### Debug variables

```yaml
debug-vars:
  script:
    - env | sort  # List all variables
    - echo "CI_PIPELINE_SOURCE=$CI_PIPELINE_SOURCE"
    - echo "CI_MERGE_REQUEST_ID=$CI_MERGE_REQUEST_ID"
```

### Debug rules

```yaml
# Add debug job that always runs
debug-rules:
  script:
    - echo "Pipeline source: $CI_PIPELINE_SOURCE"
    - echo "Commit branch: $CI_COMMIT_BRANCH"
    - echo "MR ID: $CI_MERGE_REQUEST_ID"
  rules:
    - when: always
```

### Trace job execution

```yaml
job:
  variables:
    CI_DEBUG_TRACE: "true"  # Enables verbose logging
  script: ./test.sh
```

**Warning:** Debug trace exposes all variables including secrets!

### Check file changes

```yaml
debug-changes:
  script:
    - git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA
  rules:
    - when: always
```

---

## Performance Troubleshooting

### Slow cache operations

```yaml
# Reduce cache size
cache:
  paths:
    - node_modules/
  # Don't cache:
  # - Large generated files
  # - Build artifacts (use artifacts instead)

# Adjust compression
variables:
  CACHE_COMPRESSION_LEVEL: "fastest"
```

### Slow artifact uploads

```yaml
# Minimize artifact size
artifacts:
  paths:
    - dist/
  exclude:
    - dist/**/*.map  # Exclude source maps
    - dist/**/*.log
    
# Use fast compression
variables:
  ARTIFACT_COMPRESSION_LEVEL: "fast"
```

### Pipeline too slow

```yaml
# 1. Use needs for parallelism
test:
  needs: [build]  # Don't wait for all stage jobs

# 2. Use parallel for large test suites
test:
  parallel: 5
  script: ./run-tests.sh --partition=$CI_NODE_INDEX --total=$CI_NODE_TOTAL

# 3. Fail fast
lint:
  stage: validate
  needs: []  # Start immediately
```

---

## Error Messages

### "Job failed: execution took longer than X"

- Increase timeout in job or project settings
- Runner timeout may limit maximum

### "This job is stuck because no runners match"

- Check job tags match runner tags
- Ensure runners are active and available
- Check protected branch settings if using protected runners

### "yaml invalid"

- Validate syntax in CI Lint
- Check for tabs (YAML uses spaces)
- Verify special characters are quoted

### "needs dependency not found"

- Check spelling of needed job name
- Ensure needed job exists in pipeline
- Use `optional: true` for jobs that may not run

### "cache not found"

- Cache is best-effort; job should work without it
- Check key generation matches between jobs
- Verify runner has cache access
