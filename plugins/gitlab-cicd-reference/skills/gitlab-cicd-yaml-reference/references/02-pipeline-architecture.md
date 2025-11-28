# GitLab CI/CD Pipeline Architecture Reference

> Advanced patterns for pipeline design, DAG (Directed Acyclic Graph) execution, parallel jobs, and multi-pipeline architectures.

---

## Pipeline Execution Models

### Basic (Stage-based) Pipelines

Default execution model where jobs wait for all jobs in previous stages:

```yaml
stages:
  - build
  - test
  - deploy

build-a:
  stage: build
  script: echo "Building A"

build-b:
  stage: build
  script: echo "Building B"

test:
  stage: test
  # Waits for BOTH build-a AND build-b to complete
  script: echo "Testing"

deploy:
  stage: deploy
  script: echo "Deploying"
```

**Characteristics:**
- Simple to understand
- All jobs in stage run in parallel
- Next stage waits for ALL previous stage jobs
- Slowest job in each stage becomes bottleneck

### DAG Pipelines (needs keyword)

Break stage barriers with explicit job dependencies:

```yaml
stages:
  - build
  - test
  - deploy

build_a:
  stage: build
  script: echo "Building A (fast)"

build_b:
  stage: build
  script: 
    - echo "Building B (slow)"
    - sleep 300

test_a:
  stage: test
  needs: [build_a]  # Starts immediately when build_a completes
  script: echo "Testing A"

test_b:
  stage: test
  needs: [build_b]  # Waits only for build_b
  script: echo "Testing B"

deploy_a:
  stage: deploy
  needs: [test_a]  # Can deploy A while B is still building/testing
  script: echo "Deploying A"

deploy_b:
  stage: deploy
  needs: [test_b]
  script: echo "Deploying B"
```

**Benefits:**
- Faster pipelines (critical path optimization)
- Independent workflows can run concurrently
- Deploy fast components without waiting for slow ones

### needs Syntax Variations

```yaml
job:
  needs:
    # Simple job name
    - build-job
    
    # Explicit job specification
    - job: build-job
      artifacts: true  # Download artifacts (default)
    
    # From different project
    - project: namespace/project-name
      job: build-job
      ref: main
      artifacts: true
    
    # No artifacts needed
    - job: lint-job
      artifacts: false
    
    # Optional dependency (job may not exist)
    - job: optional-job
      optional: true
```

### needs: [] (Start Immediately)

Jobs with empty `needs` start immediately, ignoring stages:

```yaml
stages:
  - build
  - test

lint:
  stage: test
  needs: []  # Starts immediately, doesn't wait for build stage
  script: npm run lint

build:
  stage: build
  script: npm run build

test:
  stage: test
  needs: [build]
  script: npm test
```

---

## Parallel Job Execution

### parallel keyword

Run multiple instances of a job:

```yaml
test:
  parallel: 5
  script: ./run-tests.sh --partition=$CI_NODE_INDEX --total=$CI_NODE_TOTAL
```

**Variables available:**
- `CI_NODE_INDEX` - Current instance (1 to N)
- `CI_NODE_TOTAL` - Total instances

### parallel:matrix

Generate jobs from variable combinations:

```yaml
# Simple matrix - 4 jobs total
test:
  parallel:
    matrix:
      - RUBY_VERSION: ["2.7", "3.0", "3.1", "3.2"]
  image: ruby:$RUBY_VERSION
  script: bundle exec rspec

# Multi-dimensional matrix - 8 jobs total (2×4)
test:
  parallel:
    matrix:
      - RUBY_VERSION: ["3.0", "3.1"]
        DATABASE: [postgres, mysql, sqlite, mongo]
  script: ./test.sh

# Multiple matrix groups - 6 jobs total (2 + 4)
deploy:
  parallel:
    matrix:
      - PROVIDER: aws
        STACK: [monitoring, app]
      - PROVIDER: [gcp, azure]
        STACK: [web, api]
  script: ./deploy.sh $PROVIDER $STACK
```

### Matrix job names

Generated jobs are named: `job_name: [var1_value, var2_value]`

```yaml
# Creates jobs:
# - "test: [3.0, postgres]"
# - "test: [3.0, mysql]"
# - "test: [3.1, postgres]"
# - "test: [3.1, mysql]"
```

### needs with parallel:matrix

Reference specific matrix instances:

```yaml
build:
  stage: build
  parallel:
    matrix:
      - PROVIDER: aws
        STACK: [monitoring, app1, app2]

test:
  stage: test
  needs:
    - job: build
      parallel:
        matrix:
          - PROVIDER: aws
            STACK: app1  # Only depend on this specific matrix job
  script: ./test.sh

# Depend on multiple matrix instances
integration-test:
  stage: test
  needs:
    - job: build
      parallel:
        matrix:
          - PROVIDER: aws
            STACK: [monitoring, app1]  # Depends on both
  script: ./integration-test.sh
```

**Important:** Variable order in `needs:parallel:matrix` must match the order in the parallel job definition.

### Dynamic tags with matrix

```yaml
deploy:
  parallel:
    matrix:
      - PROVIDER: [aws, gcp, azure]
        REGION: [us-east, eu-west]
  tags:
    - ${PROVIDER}-${REGION}  # Selects region-specific runners
  environment: $PROVIDER/$REGION
  script: ./deploy.sh
```

### Fetching artifacts from matrix jobs

```yaml
ruby:
  parallel:
    matrix:
      - RUBY_VERSION: ["2.7", "3.0", "3.1"]
        PROVIDER: [aws, gcp]
  script: bundle install
  artifacts:
    paths:
      - vendor/

deploy:
  dependencies:
    - "ruby: [3.0, aws]"  # Quotes required
  script: ./deploy.sh
```

---

## Parent-Child Pipelines

Split complex pipelines into manageable components:

### Triggering a child pipeline

```yaml
# Parent pipeline
stages:
  - triggers
  - deploy

trigger-child:
  stage: triggers
  trigger:
    include:
      - local: path/to/child-pipeline.yml
    strategy: depend  # Parent job status mirrors child pipeline status
```

### Child pipeline configuration

```yaml
# child-pipeline.yml
stages:
  - build
  - test

build:
  stage: build
  script: make build

test:
  stage: test
  script: make test
```

### Passing variables to child pipelines

```yaml
trigger-child:
  trigger:
    include: child.yml
  variables:
    ENVIRONMENT: production
    PARENT_BRANCH: $CI_COMMIT_REF_NAME
```

### Dynamic child pipelines (generated config)

```yaml
generate-config:
  stage: build
  script:
    - ./generate-pipeline.sh > generated-config.yml
  artifacts:
    paths:
      - generated-config.yml

trigger-child:
  stage: deploy
  trigger:
    include:
      - artifact: generated-config.yml
        job: generate-config
```

### Child pipeline from different project

```yaml
trigger-child:
  trigger:
    include:
      - project: 'my-group/my-pipeline-library'
        ref: 'main'
        file: '/templates/child-pipeline.yml'
```

### Child pipelines with merge request context

```yaml
# Parent .gitlab-ci.yml
trigger-child:
  trigger:
    include: child.yml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# child.yml
job1:
  script: echo "Runs when parent triggers"
  rules:
    - if: $CI_PIPELINE_SOURCE == "parent_pipeline"

job2:
  script: echo "Runs only for MR pipelines"
  rules:
    - if: $CI_MERGE_REQUEST_ID
```

### Passing artifacts between parent and child

```yaml
# Parent pipeline
build:
  stage: build
  script: make build
  artifacts:
    paths:
      - build/

trigger-child:
  stage: test
  trigger:
    include: child.yml
  variables:
    PARENT_PIPELINE_ID: $CI_PIPELINE_ID

# Child pipeline (child.yml)
test:
  stage: test
  script: ./test.sh
  needs:
    - pipeline: $PARENT_PIPELINE_ID
      job: build
      artifacts: true
```

---

## Multi-Project Pipelines

Trigger pipelines in different projects:

### Basic multi-project trigger

```yaml
trigger-downstream:
  trigger:
    project: my-group/my-downstream-project
    branch: main  # Optional: specify branch
```

### With variables

```yaml
trigger-downstream:
  trigger:
    project: my-group/my-downstream-project
  variables:
    UPSTREAM_COMMIT: $CI_COMMIT_SHA
    UPSTREAM_PROJECT: $CI_PROJECT_PATH
```

### Mirror downstream status

```yaml
trigger-downstream:
  trigger:
    project: my-group/my-downstream-project
    strategy: mirror  # Parent job status mirrors downstream pipeline
```

### API-based trigger (advanced)

```yaml
trigger-api:
  script:
    - |
      curl --request POST \
        --form "token=$CI_JOB_TOKEN" \
        --form "ref=main" \
        --form "variables[UPSTREAM_SHA]=$CI_COMMIT_SHA" \
        "https://gitlab.example.com/api/v4/projects/9/trigger/pipeline"
  rules:
    - if: $CI_COMMIT_TAG
```

---

## Pipeline Architectures

### Mono-repo with parent-child

```yaml
# Root .gitlab-ci.yml
stages:
  - triggers

trigger-frontend:
  stage: triggers
  trigger:
    include: frontend/.gitlab-ci.yml
  rules:
    - changes:
        - frontend/**/*

trigger-backend:
  stage: triggers
  trigger:
    include: backend/.gitlab-ci.yml
  rules:
    - changes:
        - backend/**/*

trigger-shared:
  stage: triggers
  trigger:
    include: shared/.gitlab-ci.yml
  rules:
    - changes:
        - shared/**/*
```

### Fan-out/Fan-in pattern

```yaml
stages:
  - build
  - test
  - merge
  - deploy

build:
  stage: build
  script: make build
  artifacts:
    paths:
      - build/

unit-test:
  stage: test
  needs: [build]
  script: make unit-test

integration-test:
  stage: test
  needs: [build]
  script: make integration-test

security-scan:
  stage: test
  needs: [build]
  script: make security-scan

merge-results:
  stage: merge
  needs: [unit-test, integration-test, security-scan]
  script: ./merge-results.sh

deploy:
  stage: deploy
  needs: [merge-results]
  script: make deploy
```

### Environment promotion pipeline

```yaml
stages:
  - build
  - deploy-dev
  - deploy-staging
  - deploy-production

build:
  stage: build
  script: make build
  artifacts:
    paths:
      - dist/

deploy-dev:
  stage: deploy-dev
  needs: [build]
  environment: development
  script: ./deploy.sh dev
  rules:
    - if: $CI_COMMIT_BRANCH

deploy-staging:
  stage: deploy-staging
  needs: [deploy-dev]
  environment: staging
  script: ./deploy.sh staging
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  stage: deploy-production
  needs: [deploy-staging]
  environment: production
  script: ./deploy.sh production
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Best Practices for Pipeline Architecture

### Critical Path Optimization

Identify and optimize the longest path through your pipeline:

```yaml
# Slow: Sequential stages
# build (5m) → test (10m) → deploy (2m) = 17 minutes

# Fast: Parallel with needs
# lint (2m) ──────────────────────────────┐
# build (5m) → unit-test (3m) ────────────┤
# build (5m) → integration-test (10m) → deploy (2m)
# = 17 minutes critical path, but lint finishes in 2m
```

### Fail Fast

Put quick validation jobs early:

```yaml
stages:
  - validate
  - build
  - test

lint:
  stage: validate
  needs: []
  script: npm run lint

type-check:
  stage: validate
  needs: []
  script: npm run type-check

# Only build if validation passes
build:
  stage: build
  needs: [lint, type-check]
  script: npm run build
```

### Resource Groups for Deployments

Prevent concurrent deployments:

```yaml
deploy-staging:
  resource_group: staging
  script: ./deploy.sh staging

deploy-production:
  resource_group: production
  script: ./deploy.sh production
```

### Pipeline Complexity Limits

Be aware of GitLab limits:
- `needs` can reference up to 50 jobs
- Maximum pipeline depth: determined by instance configuration
- Avoid more than 3 levels of `extends` inheritance
- Child pipelines have their own job limits
