# GitLab CI/CD Environments and Deployments Reference

> Environment configuration, deployment tracking, dynamic environments, and deployment safety controls.

---

## Environments Overview

Environments represent deployment targets for your application (development, staging, production). They provide:

- **Deployment tracking**: History of what's deployed where
- **Environment URLs**: Quick access to deployed applications
- **Protected environments**: Access controls for sensitive deployments
- **Auto-stop**: Automatic cleanup of temporary environments
- **Rollback**: Easy revert to previous deployments

---

## Basic Environment Configuration

### Simple Environment

```yaml
deploy-staging:
  script: ./deploy.sh staging
  environment:
    name: staging
```

### Environment with URL

```yaml
deploy-staging:
  script: ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.example.com
```

### Full Environment Configuration

```yaml
deploy-production:
  script: ./deploy.sh production
  environment:
    name: production
    url: https://example.com
    deployment_tier: production
    action: start
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Environment Keywords

### environment:name

Defines the environment name:

```yaml
environment:
  name: production

# Dynamic names with variables
environment:
  name: review/$CI_COMMIT_REF_SLUG

# Folder structure
environment:
  name: aws/us-east-1/production
```

**Naming rules:**
- Letters, digits, spaces, `-`, `_`, `/`, `$`, `{`, `}`
- Cannot start with `$` (except CI/CD variables)
- Max 255 characters

### environment:url

Sets the environment URL (displayed in GitLab UI):

```yaml
environment:
  name: staging
  url: https://staging.example.com

# Dynamic URL
environment:
  name: review/$CI_COMMIT_REF_SLUG
  url: https://$CI_COMMIT_REF_SLUG.example.com
```

### environment:deployment_tier

Classifies the environment for filtering and display:

```yaml
environment:
  name: production
  deployment_tier: production  # Explicit tier

# Available tiers:
# - production
# - staging
# - testing
# - development
# - other
```

**Auto-detection:** GitLab auto-assigns tiers based on environment names containing keywords like "prod", "staging", "test", "dev".

### environment:action

Controls environment behavior:

```yaml
# Start environment (default)
deploy:
  environment:
    name: production
    action: start

# Stop environment
stop-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop

# Prepare environment (no deployment created)
prepare:
  environment:
    name: production
    action: prepare

# Access environment (verification without deployment)
verify:
  environment:
    name: production
    action: access
```

### environment:on_stop

Links to a job that stops the environment:

```yaml
deploy-review:
  script: ./deploy-review.sh
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.example.com
    on_stop: stop-review

stop-review:
  script: ./destroy-review.sh
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: $CI_MERGE_REQUEST_ID
      when: manual
```

### environment:auto_stop_in

Automatically stops environment after duration:

```yaml
deploy-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    auto_stop_in: 1 week
    on_stop: stop-review

# Duration formats:
# 1 day, 3 days, 1 week, 2 weeks
# 1 month, 6 mos
# never (disable auto-stop)
```

### environment:kubernetes

Links to Kubernetes cluster (for GitLab Kubernetes integration):

```yaml
deploy:
  environment:
    name: production
    kubernetes:
      namespace: production
```

---

## Dynamic Environments

Create environments dynamically per branch/MR:

### Review Apps Pattern

```yaml
deploy-review:
  stage: deploy
  script:
    - ./deploy-review.sh $CI_COMMIT_REF_SLUG
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_ENVIRONMENT_SLUG.example.com
    on_stop: stop-review
    auto_stop_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_ID

stop-review:
  stage: deploy
  script:
    - ./destroy-review.sh $CI_COMMIT_REF_SLUG
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: $CI_MERGE_REQUEST_ID
      when: manual
```

### Dynamic URLs with dotenv

```yaml
deploy-review:
  script:
    - DEPLOY_URL=$(./deploy.sh)
    - echo "DYNAMIC_URL=$DEPLOY_URL" >> deploy.env
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: $DYNAMIC_URL
  artifacts:
    reports:
      dotenv: deploy.env
```

---

## Protected Environments

Restrict who can deploy to sensitive environments.

### Configuration

Configure in **Settings > CI/CD > Protected environments**:

- Select environment name
- Add allowed users/groups
- Optionally require approvals

### Required Approvals

```yaml
deploy-production:
  script: ./deploy.sh production
  environment:
    name: production
  # Requires approval from configured reviewers
  # before job can run
```

### Multiple Approval Rules

Configure different approval requirements:
- Development: No approval needed
- Staging: 1 approval from QA team
- Production: 2 approvals from DevOps team

---

## Environment Variables

### Predefined Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CI_ENVIRONMENT_NAME` | Environment name | `production` |
| `CI_ENVIRONMENT_SLUG` | URL-safe name (max 24 chars) | `review-feat-abc` |
| `CI_ENVIRONMENT_URL` | Environment URL | `https://example.com` |
| `CI_ENVIRONMENT_ACTION` | Environment action | `start`, `stop` |
| `CI_ENVIRONMENT_TIER` | Deployment tier | `production` |

### Environment-Scoped Variables

Variables that only apply to specific environments:

```yaml
# Configure in Settings > CI/CD > Variables
# Set "Environment scope" to specific environment or pattern

# Example scopes:
# production
# staging
# review/*
# aws/*
```

```yaml
deploy:
  script:
    # $DATABASE_URL has different values per environment
    - echo "Connecting to $DATABASE_URL"
  environment:
    name: $DEPLOY_ENV
```

### Wildcard Scopes

```yaml
# Variable scope: review/*
# Matches: review/feature-1, review/bugfix-2, etc.

deploy-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
  script:
    # Gets variables scoped to review/*
    - echo $REVIEW_DATABASE_URL
```

---

## Deployment Tiers and Ordering

### Tier Hierarchy

1. **production** - Highest (live systems)
2. **staging** - Pre-production testing
3. **testing** - QA environments
4. **development** - Developer environments
5. **other** - Miscellaneous

### Deployment Safety

Higher tiers get priority in resource conflicts:

```yaml
deploy-production:
  resource_group: deployment
  environment:
    name: production
    deployment_tier: production

deploy-staging:
  resource_group: deployment
  environment:
    name: staging
    deployment_tier: staging
```

---

## Environment Lifecycle

### Starting Environments

```yaml
deploy:
  environment:
    name: production
    action: start  # Default action
  script: ./deploy.sh
```

### Stopping Environments

```yaml
# Manual stop
stop-env:
  environment:
    name: production
    action: stop
  script: ./teardown.sh
  when: manual

# Auto-stop after duration
deploy:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    auto_stop_in: 1 week
```

### Preparing Environments

```yaml
# Setup job that doesn't create deployment
prepare:
  environment:
    name: production
    action: prepare
  script:
    - ./setup-infrastructure.sh
```

### Access Jobs

```yaml
# Verification without creating deployment
verify-access:
  environment:
    name: production
    action: access
  script:
    - ./run-smoke-tests.sh
```

---

## Rollback

### Manual Rollback

From GitLab UI: **Operate > Environments > Select deployment > Rollback**

### Automated Rollback

```yaml
deploy:
  script: ./deploy.sh
  environment:
    name: production
  after_script:
    - |
      if [ "$CI_JOB_STATUS" == "failed" ]; then
        ./rollback.sh
      fi
```

### Rollback on Alert

Configure in **Settings > Monitor > Alerts** to auto-rollback when critical alerts trigger.

---

## Environment Cleanup

### Delete Stopped Environments

From UI: **Operate > Environments > Stopped > Delete**

### Bulk Cleanup

```bash
# API cleanup of stopped environments
curl --request DELETE \
  --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/environments/review%2Ffeature-old"
```

### Cleanup Old Review Apps

```yaml
cleanup-stale:
  script:
    - |
      # Find environments older than 30 days
      curl -s --header "PRIVATE-TOKEN: $TOKEN" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/environments?states=stopped" | \
        jq -r '.[] | select(.updated_at < (now - 2592000 | todate)) | .id' | \
        xargs -I {} curl --request DELETE \
          --header "PRIVATE-TOKEN: $TOKEN" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/environments/{}"
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

---

## Deployment Patterns

### Blue-Green Deployment

```yaml
stages:
  - build
  - deploy-green
  - test-green
  - switch
  - cleanup

deploy-green:
  environment:
    name: production-green
    url: https://green.example.com
  script:
    - ./deploy.sh green

test-green:
  environment:
    name: production-green
    action: access
  script:
    - ./smoke-tests.sh https://green.example.com

switch-to-green:
  environment:
    name: production
    url: https://example.com
  script:
    - ./switch-traffic.sh green
  when: manual

cleanup-blue:
  environment:
    name: production-blue
    action: stop
  script:
    - ./cleanup.sh blue
  when: manual
```

### Canary Deployment

```yaml
deploy-canary:
  environment:
    name: production
    url: https://example.com
  script:
    - ./deploy-canary.sh 10  # 10% traffic
  when: manual

deploy-full:
  environment:
    name: production
  script:
    - ./deploy-full.sh
  needs:
    - deploy-canary
  when: manual
```

### Progressive Delivery

```yaml
stages:
  - deploy
  - verify
  - promote

deploy-10:
  stage: deploy
  environment:
    name: production
  script: ./deploy.sh --percentage 10

verify-10:
  stage: verify
  environment:
    name: production
    action: access
  script: ./verify-metrics.sh
  needs: [deploy-10]

deploy-50:
  stage: promote
  environment:
    name: production
  script: ./deploy.sh --percentage 50
  needs: [verify-10]
  when: manual

deploy-100:
  stage: promote
  environment:
    name: production
  script: ./deploy.sh --percentage 100
  needs: [deploy-50]
  when: manual
```

---

## Environment Folders

Group related environments:

```yaml
# Creates folder structure in UI
deploy-aws-east:
  environment:
    name: aws/us-east-1/production

deploy-aws-west:
  environment:
    name: aws/us-west-2/production

deploy-gcp:
  environment:
    name: gcp/us-central1/production
```

**Result in UI:**
```
├── aws/
│   ├── us-east-1/
│   │   └── production
│   └── us-west-2/
│       └── production
└── gcp/
    └── us-central1/
        └── production
```

---

## Troubleshooting

### Environment Not Stopping

```yaml
# Ensure stop job has correct rules
stop-review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  rules:
    # Must match original deployment rules
    - if: $CI_MERGE_REQUEST_ID
      when: manual
  # Don't use GIT_STRATEGY: none if you need scripts
```

### Auto-stop Not Working

- Check `on_stop` job exists and is valid
- Verify `auto_stop_in` duration
- Ensure stop job rules allow execution

### Environment URL Not Showing

```yaml
# URL must be set at job creation time
# Use artifacts:reports:dotenv for dynamic URLs

deploy:
  script:
    - echo "DYNAMIC_URL=$(./deploy.sh)" >> deploy.env
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: $DYNAMIC_URL
  artifacts:
    reports:
      dotenv: deploy.env
```

### Protected Environment Blocking Deployment

- Verify user has deploy permissions
- Check approval requirements
- Ensure branch protection doesn't conflict
