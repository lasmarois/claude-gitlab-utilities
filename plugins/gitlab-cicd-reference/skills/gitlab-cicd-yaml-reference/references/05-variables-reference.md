# GitLab CI/CD Variables Reference

> Predefined variables, custom variables, and variable handling patterns.

---

## Predefined Variables Categories

### Pipeline Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_PIPELINE_ID` | Unique pipeline ID (instance-wide) | `12345` |
| `CI_PIPELINE_IID` | Pipeline ID (project-scoped) | `42` |
| `CI_PIPELINE_SOURCE` | How pipeline was triggered | `push`, `merge_request_event`, `schedule`, `web`, `trigger`, `api`, `parent_pipeline` |
| `CI_PIPELINE_URL` | URL to pipeline page | `https://gitlab.example.com/project/-/pipelines/12345` |
| `CI_PIPELINE_CREATED_AT` | Pipeline creation timestamp | `2024-01-15T10:30:00Z` |

### Commit Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_COMMIT_SHA` | Full commit SHA | `abc123def456...` |
| `CI_COMMIT_SHORT_SHA` | First 8 characters of SHA | `abc123de` |
| `CI_COMMIT_BRANCH` | Branch name (empty for tags) | `feature/my-branch` |
| `CI_COMMIT_REF_NAME` | Branch or tag name | `main` or `v1.0.0` |
| `CI_COMMIT_REF_SLUG` | URL-safe ref name (max 63 chars) | `feature-my-branch` |
| `CI_COMMIT_TAG` | Tag name (empty if not a tag) | `v1.0.0` |
| `CI_COMMIT_TITLE` | First line of commit message | `Fix bug in login` |
| `CI_COMMIT_MESSAGE` | Full commit message | Multi-line text |
| `CI_COMMIT_AUTHOR` | Commit author | `John Doe <john@example.com>` |
| `CI_COMMIT_BEFORE_SHA` | Previous commit SHA (push events) | `def789...` |

### Job Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_JOB_ID` | Unique job ID | `98765` |
| `CI_JOB_NAME` | Job name from config | `build:linux` |
| `CI_JOB_STAGE` | Stage name | `build` |
| `CI_JOB_STATUS` | Job status | `running`, `success`, `failed` |
| `CI_JOB_TOKEN` | Authentication token | `[masked]` |
| `CI_JOB_URL` | URL to job page | `https://gitlab.example.com/.../jobs/98765` |
| `CI_JOB_STARTED_AT` | Job start timestamp | `2024-01-15T10:31:00Z` |
| `CI_NODE_INDEX` | Parallel job index (1-based) | `1` |
| `CI_NODE_TOTAL` | Total parallel jobs | `5` |

### Project Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_PROJECT_ID` | Project ID | `123` |
| `CI_PROJECT_NAME` | Project name | `my-project` |
| `CI_PROJECT_PATH` | Full project path | `my-group/my-project` |
| `CI_PROJECT_PATH_SLUG` | URL-safe project path | `my-group-my-project` |
| `CI_PROJECT_NAMESPACE` | Project namespace | `my-group` |
| `CI_PROJECT_URL` | Project URL | `https://gitlab.example.com/my-group/my-project` |
| `CI_PROJECT_DIR` | Clone directory | `/builds/my-group/my-project` |
| `CI_PROJECT_ROOT_NAMESPACE` | Top-level namespace | `my-group` |
| `CI_DEFAULT_BRANCH` | Default branch name | `main` |

### Merge Request Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_MERGE_REQUEST_ID` | MR ID (instance-wide) | `456` |
| `CI_MERGE_REQUEST_IID` | MR IID (project-scoped) | `12` |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` | Source branch | `feature/new-login` |
| `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | Target branch | `main` |
| `CI_MERGE_REQUEST_TITLE` | MR title | `Add new login feature` |
| `CI_MERGE_REQUEST_LABELS` | Comma-separated labels | `bug,priority::high` |
| `CI_MERGE_REQUEST_MILESTONE` | Milestone title | `v2.0` |
| `CI_OPEN_MERGE_REQUESTS` | Open MRs for branch | `my-group/my-project!12` |

### Registry Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_REGISTRY` | Container registry URL | `registry.gitlab.example.com` |
| `CI_REGISTRY_IMAGE` | Project registry image | `registry.gitlab.example.com/group/project` |
| `CI_REGISTRY_USER` | Registry username | `gitlab-ci-token` |
| `CI_REGISTRY_PASSWORD` | Registry password | `[masked]` |

### Runner Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_RUNNER_ID` | Runner ID | `789` |
| `CI_RUNNER_DESCRIPTION` | Runner description | `docker-runner-01` |
| `CI_RUNNER_TAGS` | Runner tags | `docker,linux` |
| `CI_RUNNER_EXECUTABLE_ARCH` | Runner architecture | `linux/amd64` |
| `GITLAB_USER_LOGIN` | User who triggered pipeline | `john.doe` |
| `GITLAB_USER_EMAIL` | User email | `john@example.com` |
| `GITLAB_USER_NAME` | User display name | `John Doe` |

### Environment Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_ENVIRONMENT_NAME` | Environment name | `production` |
| `CI_ENVIRONMENT_SLUG` | URL-safe environment name | `production` |
| `CI_ENVIRONMENT_URL` | Environment URL | `https://example.com` |
| `CI_ENVIRONMENT_ACTION` | Environment action | `start`, `stop` |

---

## Defining Custom Variables

### Global variables

```yaml
variables:
  GLOBAL_VAR: "available in all jobs"
  DATABASE_URL: "postgres://localhost/test"
```

### Job variables

```yaml
job:
  variables:
    JOB_VAR: "only in this job"
    GLOBAL_VAR: "overrides global"  # Override
  script: echo $JOB_VAR
```

### Variable expansion

```yaml
variables:
  BASE_PATH: "/app"
  FULL_PATH: "$BASE_PATH/src"  # Expands to /app/src
  DYNAMIC: "${CI_COMMIT_REF_SLUG}-${CI_PIPELINE_ID}"
```

### Prevent expansion

```yaml
variables:
  # Single quotes prevent expansion
  LITERAL: '$NOT_EXPANDED'
  
  # Or use expand: false
  RAW_VALUE:
    value: "$ALSO_NOT_EXPANDED"
    expand: false
```

---

## Variable Scopes and Priority

### Priority order (highest to lowest)

1. Trigger variables
2. Scheduled pipeline variables
3. Manual pipeline variables
4. Project CI/CD variables
5. Group CI/CD variables
6. Instance CI/CD variables
7. `.gitlab-ci.yml` variables
8. Job variables
9. Predefined variables

### Protected variables

Only available in protected branches/tags:

```yaml
# Set in GitLab UI: Settings > CI/CD > Variables
# Mark as "Protected"
```

### Masked variables

Hidden in job logs:

```yaml
# Set in GitLab UI: Settings > CI/CD > Variables
# Mark as "Masked"
# Must be ≥8 characters, Base64-compatible
```

---

## Conditional Variables

### With rules

```yaml
job:
  variables:
    DEPLOY_ENV: "staging"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        DEPLOY_ENV: "production"
    - when: on_success
  script: deploy $DEPLOY_ENV
```

### With workflow

```yaml
variables:
  ENVIRONMENT: "development"

workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        ENVIRONMENT: "production"
    - if: $CI_COMMIT_BRANCH
```

---

## Passing Variables Between Jobs

### Using artifacts (dotenv)

```yaml
build:
  stage: build
  script:
    - echo "VERSION=1.2.3" >> build.env
    - echo "BUILD_DATE=$(date +%Y%m%d)" >> build.env
  artifacts:
    reports:
      dotenv: build.env

test:
  stage: test
  script:
    - echo "Testing version $VERSION from $BUILD_DATE"
  # Automatically receives dotenv from previous stages
```

### To downstream/child pipelines

```yaml
trigger-child:
  trigger:
    include: child.yml
  variables:
    PARENT_VAR: "from parent"
    COMMIT_SHA: $CI_COMMIT_SHA
```

### From upstream pipelines

```yaml
# In child pipeline
job:
  script: echo "Parent passed $PARENT_VAR"
```

---

## Variable Expressions in Rules

### Comparison operators

```yaml
rules:
  # Equality
  - if: $VAR == "value"
  - if: $VAR != "value"
  
  # Null check
  - if: $VAR == null
  - if: $VAR != null
  
  # Empty string check
  - if: $VAR == ""
  - if: $VAR != ""
  
  # Truthiness (variable exists and is not empty)
  - if: $VAR
  - if: $CI_COMMIT_TAG  # True if it's a tag
```

### Regex matching

```yaml
rules:
  - if: $CI_COMMIT_BRANCH =~ /^feature/
  - if: $CI_COMMIT_BRANCH !~ /^release/
  - if: $CI_COMMIT_MESSAGE =~ /\[skip ci\]/
```

### Regex with variables

```yaml
variables:
  PATTERN: '^v\d+\.\d+\.\d+$'

rules:
  - if: $CI_COMMIT_TAG =~ $PATTERN
```

### Logical operators

```yaml
rules:
  # AND
  - if: $VAR1 == "a" && $VAR2 == "b"
  
  # OR
  - if: $VAR1 == "a" || $VAR1 == "b"
  
  # Parentheses for grouping
  - if: ($VAR1 == "a" || $VAR1 == "b") && $VAR2
  
  # Complex expression
  - if: ($CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_COMMIT_BRANCH == "develop") && $DEPLOY_ENABLED
```

---

## Shell-Specific Variable Access

### Bash/sh

```yaml
script:
  - echo "$MY_VAR"
  - echo "${MY_VAR}_suffix"
  - export LOCAL_VAR="value"
```

### PowerShell

```yaml
script:
  - echo $env:MY_VAR
  - echo "$env:MY_VAR"
```

### Windows Batch

```yaml
script:
  - echo %MY_VAR%
```

---

## Common Variable Patterns

### Feature flags

```yaml
variables:
  ENABLE_FEATURE_X: "false"

job:
  script:
    - if [ "$ENABLE_FEATURE_X" == "true" ]; then ./feature-x.sh; fi
```

### Environment-based configuration

```yaml
.deploy-template:
  script:
    - deploy --env=$DEPLOY_ENV --url=$DEPLOY_URL

deploy-staging:
  extends: .deploy-template
  variables:
    DEPLOY_ENV: staging
    DEPLOY_URL: https://staging.example.com

deploy-production:
  extends: .deploy-template
  variables:
    DEPLOY_ENV: production
    DEPLOY_URL: https://example.com
```

### Dynamic versioning

```yaml
variables:
  VERSION: "${CI_COMMIT_TAG:-${CI_COMMIT_SHORT_SHA}}"
  # Uses tag if available, otherwise short SHA

build:
  script:
    - docker build -t myapp:$VERSION .
```

### Conditional image

```yaml
variables:
  DOCKER_IMAGE: "node:18"

job:
  image: $DOCKER_IMAGE
  rules:
    - if: $USE_NODE_20
      variables:
        DOCKER_IMAGE: "node:20"
    - when: always
```

---

## Variable Security Best Practices

1. **Use masked variables** for secrets (API keys, passwords)
2. **Use protected variables** for production credentials
3. **Never echo secrets** in scripts
4. **Use CI_JOB_TOKEN** for GitLab API/registry authentication
5. **Rotate secrets regularly** in CI/CD settings
6. **Audit variable usage** in pipeline logs

### Secure secret handling

```yaml
deploy:
  script:
    # Good: Use variable directly
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    
    # Bad: Don't echo secrets
    # - echo $SECRET_KEY  # Exposes in logs
    
    # Good: Pass via environment
    - MY_SECRET=$SECRET_KEY ./deploy.sh
```

### File-type variables

```yaml
# In GitLab UI, create a "File" type variable
# The variable contains the path to a temporary file with the content

deploy:
  script:
    - cat $KUBECONFIG  # Contains path to kubeconfig file
    - kubectl --kubeconfig=$KUBECONFIG apply -f manifest.yml
```
