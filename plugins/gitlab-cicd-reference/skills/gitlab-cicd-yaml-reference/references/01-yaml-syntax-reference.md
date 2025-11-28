# GitLab CI/CD YAML Syntax Reference

> Advanced reference for `.gitlab-ci.yml` configuration. This document covers core keywords, syntax patterns, and advanced configurations for users familiar with GitLab CI basics.

---

## Job Definition Fundamentals

### script (Required)

The `script` keyword specifies commands the GitLab Runner executes. This is the only required keyword for most job types.

```yaml
job1:
  script: "bundle exec rspec"

job2:
  script:
    - uname -a
    - bundle exec rspec
```

**Key behaviors:**
- Scripts are concatenated with `before_script` and executed in a single shell
- CI/CD variables are expanded within scripts
- Non-zero exit codes fail the job by default

### before_script / after_script

```yaml
job:
  before_script:
    - echo "Execute before main script, after artifacts restored"
  script:
    - echo "Main script"
  after_script:
    - echo "Runs even on failure or cancellation"
```

**Critical `after_script` behaviors:**
- Runs in a **separate shell context** (environment variables from script don't persist)
- Default timeout: **5 minutes** (configurable via `RUNNER_AFTER_SCRIPT_TIMEOUT`)
- Does **not** affect job exit code (job succeeds if script succeeds)
- Runs when job is canceled or script fails with `script_failure`

**Timeout configuration (GitLab Runner 16.4+):**

```yaml
job-with-timeouts:
  timeout: 5m
  variables:
    RUNNER_SCRIPT_TIMEOUT: 3m
    RUNNER_AFTER_SCRIPT_TIMEOUT: 1m
  script:
    - long_running_command
  after_script:
    - cleanup_command
```

### default

Set global defaults that apply to all jobs unless overridden:

```yaml
default:
  image: ruby:3.0
  retry: 2
  timeout: 30m
  before_script:
    - echo "Global before_script"

rspec:
  script: bundle exec rspec  # Inherits defaults

custom-job:
  image: python:3.11  # Overrides default image
  script: pytest
```

**Merge behavior:** Job configuration **replaces** default configuration entirely (no deep merge).

---

## Stages and Pipeline Structure

### stages

Define pipeline stages and execution order:

```yaml
stages:
  - build
  - test
  - security
  - deploy
```

**Execution rules:**
- Jobs in the same stage run **in parallel**
- Subsequent stages run only if all previous stage jobs succeed
- Jobs without `stage:` default to `test`
- If `stages:` is not defined, defaults are: `.pre`, `build`, `test`, `deploy`, `.post`

### stage

Assign jobs to stages:

```yaml
build-job:
  stage: build
  script: make

test-job:
  stage: test
  script: make test
```

**Special stages:**
- `.pre` - Always runs first
- `.post` - Always runs last

---

## Conditional Execution with rules

### rules:if

Evaluate CI/CD variable expressions:

```yaml
job:
  script: echo "Conditional job"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: on_success
    - if: $CI_COMMIT_BRANCH =~ /^feature/
      when: manual
      allow_failure: true
    - if: $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME
      when: delayed
      start_in: 5 minutes
```

**Operators:**
- `==`, `!=` - Equality
- `=~`, `!~` - Regex matching
- `&&`, `||` - Logical AND/OR
- Parentheses for grouping

**Complex expression example:**

```yaml
job:
  rules:
    - if: ($CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_COMMIT_BRANCH == "develop") && $MY_VARIABLE
```

### rules:changes

Run jobs based on file changes:

```yaml
docker-build:
  script: docker build -t my-image .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        paths:
          - Dockerfile
          - docker/**/*
          - "*.dockerfile"
        compare_to: 'refs/heads/main'  # Compare against specific ref
```

**Path patterns:**
- Glob patterns supported (`**/*.py`, `src/**/*`)
- `compare_to` requires `paths` to be specified

### rules:exists

Run jobs based on file/directory presence:

```yaml
job:
  script: docker build -t my-image .
  rules:
    - exists:
        - Dockerfile

# With variables and globs
job2:
  variables:
    DOCKERPATH: "**/Dockerfile"
  rules:
    - exists:
        - $DOCKERPATH

# Check files in another project
job3:
  rules:
    - exists:
        paths:
          - Dockerfile
        project: my-group/my-project
        ref: v1.0.0
```

**Limits:** Maximum 50,000 file checks per rule.

### rules:when

Control job execution behavior:

| Value | Behavior |
|-------|----------|
| `on_success` | Run if all previous jobs succeeded (default) |
| `on_failure` | Run only if a previous job failed |
| `always` | Run regardless of previous job status |
| `manual` | Wait for manual trigger |
| `delayed` | Run after specified delay |
| `never` | Never add job to pipeline |

### rules:variables

Define variables conditionally:

```yaml
job:
  variables:
    DEPLOY_ENV: "staging"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        DEPLOY_ENV: "production"
    - when: on_success
  script:
    - deploy --env=$DEPLOY_ENV
```

### rules:interruptible

Override job interruptibility per rule:

```yaml
job:
  interruptible: true
  rules:
    - if: $CI_COMMIT_REF_NAME == $CI_DEFAULT_BRANCH
      interruptible: false  # Never cancel on main branch
    - when: on_success
```

---

## workflow

Control entire pipeline creation:

```yaml
workflow:
  name: '$PIPELINE_NAME'
  rules:
    - if: $CI_COMMIT_TITLE =~ /-draft$/
      when: never
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      variables:
        PIPELINE_NAME: "MR: $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        PIPELINE_NAME: "Production Pipeline"
    - when: always

variables:
  PIPELINE_NAME: "Default Pipeline"
```

**Common patterns to prevent duplicate pipelines:**

```yaml
workflow:
  rules:
    # Skip if branch pipeline and MR exists
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS && $CI_PIPELINE_SOURCE == "push"
      when: never
    # Run for merge requests
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    # Run for default branch
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### workflow:auto_cancel

Control automatic pipeline cancellation:

```yaml
workflow:
  auto_cancel:
    on_new_commit: interruptible  # Cancel only interruptible jobs
    # Options: conservative, interruptible, none
```

---

## Variables

### Defining variables

```yaml
variables:
  GLOBAL_VAR: "available everywhere"

job:
  variables:
    JOB_VAR: "job-specific"
    INHERITED: $GLOBAL_VAR  # Reference other variables
  script:
    - echo "$GLOBAL_VAR $JOB_VAR"
```

### Variable expansion

```yaml
variables:
  PROJECT_PATH: "$CI_PROJECT_DIR/build"
  DYNAMIC_PATH: '${CI_COMMIT_REF_SLUG}-${CI_PIPELINE_ID}'
```

### Passing variables between jobs (dotenv)

```yaml
build-job:
  stage: build
  script:
    - echo "BUILD_VERSION=1.2.3" >> build.env
    - echo "BUILD_DATE=$(date +%Y%m%d)" >> build.env
  artifacts:
    reports:
      dotenv: build.env

test-job:
  stage: test
  script:
    - echo "Testing version $BUILD_VERSION built on $BUILD_DATE"
```

---

## Image and Services

### image

```yaml
job:
  image: ruby:3.2-alpine

# With entrypoint override
job:
  image:
    name: super/sql:experimental
    entrypoint: [""]
```

### services

```yaml
test:
  image: ruby:3.2
  services:
    - postgres:15
    - redis:7

# Multiple instances of same image
test:
  services:
    - name: mysql:8.0
      alias: mysql-primary
    - name: mysql:8.0
      alias: mysql-replica

# With configuration
test:
  services:
    - name: postgres:15
      alias: db
      entrypoint: ["docker-entrypoint.sh"]
      command: ["postgres", "-c", "max_connections=200"]
      variables:
        POSTGRES_DB: test_db
        POSTGRES_USER: test_user
```

### Docker-in-Docker setup

```yaml
build:
  image: docker:24.0.5
  services:
    - name: docker:24.0.5-dind
      alias: docker
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

---

## Job Control Keywords

### timeout

```yaml
build:
  script: build.sh
  timeout: 3 hours 30 minutes

test:
  script: rspec
  timeout: 3h 30m
```

**Hierarchy:** Job timeout ≤ Runner timeout ≤ Project timeout

### retry

```yaml
test:
  script: rspec
  retry: 2  # Simple retry on any failure

# Targeted retry
test:
  script: rspec
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
      - script_failure
    exit_codes: [137, 255]  # Retry only on specific exit codes
```

**Failure types:** `unknown_failure`, `script_failure`, `api_failure`, `stuck_or_timeout_failure`, `runner_system_failure`, `runner_unsupported`, `stale_schedule`, `job_execution_timeout`, `archived_failure`, `scheduler_failure`, `data_integrity_failure`

### interruptible

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  interruptible: true  # Can be canceled by newer pipeline
  script: make build

deploy:
  stage: deploy
  interruptible: false  # Must complete even if newer pipeline starts
  script: make deploy
```

### resource_group

Ensure only one job runs at a time for a resource:

```yaml
deploy-staging:
  stage: deploy
  resource_group: staging
  script: deploy.sh staging

deploy-production:
  stage: deploy
  resource_group: production
  script: deploy.sh production
```

**Process modes:**
- `unordered` (default) - First available job runs
- `oldest_first` - Strict FIFO ordering
- `newest_first` - Latest job runs first

### allow_failure

```yaml
test:
  script: experimental_test.sh
  allow_failure: true

# With exit codes
test:
  script: test.sh
  allow_failure:
    exit_codes:
      - 42
      - 137
```

### when

```yaml
cleanup:
  script: cleanup.sh
  when: always  # Run regardless of previous job status

manual-deploy:
  script: deploy.sh
  when: manual
  allow_failure: false  # Block pipeline until manually triggered
```

### dependencies

Control artifact downloading:

```yaml
build:
  stage: build
  script: make
  artifacts:
    paths:
      - build/

test:
  stage: test
  dependencies:
    - build  # Only download artifacts from 'build' job
  script: test.sh

deploy:
  stage: deploy
  dependencies: []  # Download no artifacts
  script: deploy.sh
```

---

## Tags and Runner Selection

### tags

```yaml
job:
  tags:
    - docker
    - linux

# Dynamic tags with variables
deploy:
  tags:
    - ${DEPLOY_ENV}-runner
```

---

## Environment

### Basic environment

```yaml
deploy-staging:
  script: deploy.sh
  environment:
    name: staging
    url: https://staging.example.com

deploy-production:
  script: deploy.sh
  environment:
    name: production
    url: https://example.com
  when: manual
```

### Dynamic environments

```yaml
deploy-review:
  script: deploy-review.sh
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_ENVIRONMENT_SLUG.example.com
    on_stop: stop-review
    auto_stop_in: 1 week

stop-review:
  script: destroy-review.sh
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
```

---

## Coverage and Reports

### coverage

Extract coverage from job output:

```yaml
test:
  script: pytest --cov
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

### artifacts:reports

```yaml
test:
  script: pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      dotenv: variables.env
```

---

## YAML Troubleshooting

### Colons in scripts

```yaml
# Wrong - YAML interprets colon as key
job:
  script:
    - curl --header "TOKEN: secret"  # Error!

# Correct - Quote the entire command
job:
  script:
    - 'curl --header "TOKEN: secret"'
```

### Special characters

```yaml
job:
  script:
    # Use quotes for special YAML characters
    - echo 'Value with: colon'
    - echo "Value with $VARIABLE"
    - 'echo "Complex: $VAR with spaces"'
```
