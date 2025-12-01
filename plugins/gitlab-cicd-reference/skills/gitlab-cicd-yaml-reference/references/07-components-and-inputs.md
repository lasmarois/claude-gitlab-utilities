# GitLab CI/CD Components and Inputs Reference

> Reusable CI/CD configuration units with typed parameters for building modular, maintainable pipelines.

---

## CI/CD Components Overview

CI/CD components are reusable, versioned units of pipeline configuration that can be shared across projects. They represent GitLab's modern approach to pipeline reusability, replacing older patterns like include templates.

### Key Benefits

- **Versioned**: Pin to specific versions for stability
- **Discoverable**: Published to CI/CD Catalog
- **Typed inputs**: Strong validation at pipeline creation time
- **Self-documenting**: Built-in documentation standards

---

## Using Components

### Basic Component Inclusion

```yaml
include:
  - component: gitlab.com/my-group/my-component@1.0.0
```

### Component with Inputs

```yaml
include:
  - component: gitlab.com/components/docker-build@2.1.0
    inputs:
      image_name: my-app
      dockerfile: ./docker/Dockerfile
      registry: $CI_REGISTRY
```

### Version Formats

```yaml
include:
  # Exact version (recommended for production)
  - component: gitlab.com/group/component@1.2.3

  # Major version (gets latest 1.x.x)
  - component: gitlab.com/group/component@1

  # Major.minor (gets latest 1.2.x)
  - component: gitlab.com/group/component@1.2

  # Latest from catalog
  - component: gitlab.com/group/component@~latest

  # Specific commit SHA
  - component: gitlab.com/group/component@abc123def

  # Branch name (not recommended for production)
  - component: gitlab.com/group/component@main
```

### Multiple Components

```yaml
include:
  - component: gitlab.com/components/docker-build@1.0.0
    inputs:
      image_name: backend
  - component: gitlab.com/components/sast@2.0.0
  - component: gitlab.com/components/deploy-aws@1.5.0
    inputs:
      environment: production
```

---

## spec:inputs - Defining Input Parameters

The `spec:inputs` section defines typed parameters for reusable configurations.

### Basic Input Definition

```yaml
spec:
  inputs:
    environment:
      description: "Target deployment environment"
      default: "staging"
    version:
      description: "Application version to deploy"
---
# Job definitions below the separator
deploy:
  script: deploy.sh $[[ inputs.environment ]] $[[ inputs.version ]]
```

### Input Configuration Options

#### description

Provides context for users:

```yaml
spec:
  inputs:
    database_url:
      description: "PostgreSQL connection string for the application database"
```

#### default

Makes inputs optional:

```yaml
spec:
  inputs:
    # Required input (no default)
    api_key:
      description: "API key for external service"

    # Optional input (has default)
    timeout:
      description: "Request timeout in seconds"
      default: 30
```

#### type

Specifies input data type:

```yaml
spec:
  inputs:
    # String (default type)
    name:
      type: string
      default: "my-app"

    # Number
    replicas:
      type: number
      default: 3

    # Boolean
    enable_cache:
      type: boolean
      default: true

    # Array (GitLab 16.11+)
    tags:
      type: array
      default: ["docker", "linux"]
```

#### options

Restricts to predefined values:

```yaml
spec:
  inputs:
    environment:
      description: "Deployment environment"
      options:
        - development
        - staging
        - production
      default: staging

    log_level:
      options:
        - debug
        - info
        - warn
        - error
      default: info
```

#### regex

Validates input against a pattern:

```yaml
spec:
  inputs:
    version:
      description: "Semantic version (e.g., 1.2.3)"
      regex: '^\d+\.\d+\.\d+$'

    branch_name:
      description: "Feature branch name"
      regex: '^feature/[a-z0-9-]+$'

    email:
      description: "Notification email"
      regex: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

### Complete Input Example

```yaml
spec:
  inputs:
    image_name:
      description: "Docker image name without registry prefix"
      type: string

    registry:
      description: "Container registry URL"
      type: string
      default: $CI_REGISTRY

    dockerfile:
      description: "Path to Dockerfile"
      type: string
      default: "Dockerfile"

    build_args:
      description: "Docker build arguments"
      type: array
      default: []

    push:
      description: "Push image after build"
      type: boolean
      default: true

    platform:
      description: "Target platform"
      options:
        - linux/amd64
        - linux/arm64
        - linux/amd64,linux/arm64
      default: linux/amd64
---
docker-build:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker build
        --platform $[[ inputs.platform ]]
        -f $[[ inputs.dockerfile ]]
        -t $[[ inputs.registry ]]/$[[ inputs.image_name ]]:$CI_COMMIT_SHA
        .
    - |
      if [ "$[[ inputs.push ]]" = "true" ]; then
        docker push $[[ inputs.registry ]]/$[[ inputs.image_name ]]:$CI_COMMIT_SHA
      fi
```

---

## Input Types Deep Dive

### String Type

```yaml
spec:
  inputs:
    message:
      type: string
      default: "Hello World"
---
job:
  script: echo "$[[ inputs.message ]]"
```

### Number Type

```yaml
spec:
  inputs:
    parallelism:
      type: number
      default: 4
    timeout_minutes:
      type: number
      default: 30
---
test:
  parallel: $[[ inputs.parallelism ]]
  timeout: $[[ inputs.timeout_minutes ]] minutes
  script: ./run-tests.sh
```

### Boolean Type

```yaml
spec:
  inputs:
    skip_tests:
      type: boolean
      default: false
    verbose:
      type: boolean
      default: true
---
build:
  script:
    - ./build.sh
    - |
      if [ "$[[ inputs.skip_tests ]]" != "true" ]; then
        ./test.sh
      fi
  variables:
    VERBOSE: $[[ inputs.verbose ]]
```

### Array Type

```yaml
spec:
  inputs:
    services:
      type: array
      default: ["postgres:15", "redis:7"]
    test_suites:
      type: array
      default: ["unit", "integration"]
---
test:
  services: $[[ inputs.services ]]
  parallel:
    matrix:
      - SUITE: $[[ inputs.test_suites ]]
  script: ./run-tests.sh $SUITE
```

**Passing arrays manually:**

```yaml
include:
  - local: templates/test.yml
    inputs:
      # JSON format required for arrays
      services: '["mysql:8", "redis:7", "elasticsearch:8"]'
```

---

## Input Interpolation

### Basic Interpolation

```yaml
spec:
  inputs:
    app_name:
---
job:
  # Use $[[ inputs.name ]] syntax
  script: echo "Deploying $[[ inputs.app_name ]]"
  environment:
    name: $[[ inputs.app_name ]]-env
```

### Interpolation with Manipulation Functions

#### expand_vars - Expand CI/CD Variables

```yaml
spec:
  inputs:
    path:
      default: "$CI_PROJECT_DIR/output"
---
job:
  script: ls $[[ inputs.path | expand_vars ]]
```

#### truncate - Shorten Values

```yaml
spec:
  inputs:
    commit_sha:
      default: $CI_COMMIT_SHA
---
job:
  # truncate(offset, length)
  variables:
    SHORT_SHA: $[[ inputs.commit_sha | truncate(0, 8) ]]
```

#### posix_escape - Escape Shell Characters

```yaml
spec:
  inputs:
    user_input:
---
job:
  # Safely use user input in shell commands
  script: echo '$[[ inputs.user_input | posix_escape ]]'
```

#### Chaining Functions

```yaml
spec:
  inputs:
    path:
---
job:
  # Maximum 3 functions per interpolation
  script: echo "$[[ inputs.path | expand_vars | posix_escape ]]"
```

---

## Creating Component Projects

### Directory Structure

```
my-component/
├── templates/
│   └── build.yml          # Component template (required)
├── README.md              # Documentation (required)
├── .gitlab-ci.yml         # Component's own CI (for testing)
└── LICENSE                # License file (recommended)
```

### Component Template Example

```yaml
# templates/build.yml
spec:
  inputs:
    stage:
      default: build
    image:
      default: node:18
    script:
      type: array
      default: ["npm ci", "npm run build"]
    artifacts_paths:
      type: array
      default: ["dist/"]
---
build:
  stage: $[[ inputs.stage ]]
  image: $[[ inputs.image ]]
  script: $[[ inputs.script ]]
  artifacts:
    paths: $[[ inputs.artifacts_paths ]]
```

### Testing Components

```yaml
# .gitlab-ci.yml in component project
stages:
  - test

# Test with default inputs
test-defaults:
  trigger:
    include:
      - local: templates/build.yml
    strategy: depend

# Test with custom inputs
test-custom:
  trigger:
    include:
      - local: templates/build.yml
        inputs:
          image: node:20
          script: '["yarn install", "yarn build"]'
    strategy: depend
```

### Publishing to CI/CD Catalog

1. **Create a release tag:**

```bash
git tag -a 1.0.0 -m "Initial release"
git push origin 1.0.0
```

2. **Configure catalog publishing:**

```yaml
# .gitlab-ci.yml
include:
  - component: gitlab.com/components/release@1.0.0

release:
  stage: release
  rules:
    - if: $CI_COMMIT_TAG
```

---

## Component Context

Access component metadata within templates:

```yaml
spec:
  inputs:
    image_tag:
      default: $[[ component.version ]]
---
job:
  variables:
    # Component's version (from tag)
    COMPONENT_VERSION: $[[ component.version ]]
    # Component's commit SHA
    COMPONENT_SHA: $[[ component.sha ]]
    # Component's ref (branch/tag)
    COMPONENT_REF: $[[ component.ref ]]
  script:
    - echo "Using component version $COMPONENT_VERSION"
```

---

## Passing Inputs to Downstream Pipelines

### To Child Pipelines

```yaml
trigger-child:
  trigger:
    include:
      - local: child-pipeline.yml
        inputs:
          environment: production
          version: $CI_COMMIT_TAG
```

### To Multi-Project Pipelines

```yaml
trigger-downstream:
  trigger:
    project: my-group/downstream-project
    inputs:
      upstream_sha: $CI_COMMIT_SHA
      upstream_project: $CI_PROJECT_PATH
```

---

## include:inputs for Local Files

Pass inputs to included local files:

```yaml
# Main .gitlab-ci.yml
include:
  - local: templates/deploy.yml
    inputs:
      environment: staging
      replicas: 3

# templates/deploy.yml
spec:
  inputs:
    environment:
    replicas:
      type: number
      default: 1
---
deploy:
  script: kubectl scale deployment/app --replicas=$[[ inputs.replicas ]]
  environment:
    name: $[[ inputs.environment ]]
```

---

## Conditional Includes with Inputs

```yaml
include:
  - local: templates/security-scan.yml
    inputs:
      scan_type: sast
    rules:
      - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

  - local: templates/deploy.yml
    inputs:
      environment: staging
    rules:
      - if: $CI_PIPELINE_SOURCE == "merge_request_event"
        changes:
          - src/**/*
```

---

## Best Practices

### Component Design

1. **Use descriptive input names** with clear descriptions
2. **Provide sensible defaults** for optional inputs
3. **Validate inputs** with regex or options where appropriate
4. **Document all inputs** in README.md
5. **Version semantically** (major.minor.patch)

### Security

1. **Pin component versions** in production pipelines
2. **Review component source** before using third-party components
3. **Use protected variables** for sensitive inputs
4. **Minimize job token permissions** in components

### Maintenance

1. **Test components** in the component project's CI
2. **Use component context** for dynamic versioning
3. **Publish releases** to make components discoverable
4. **Deprecate gracefully** with clear migration paths

---

## Troubleshooting

### "Input validation failed"

```yaml
# Problem: Input doesn't match type or validation
inputs:
  replicas: "three"  # Should be number

# Solution: Use correct type
inputs:
  replicas: 3
```

### "Component not found"

```yaml
# Problem: Wrong path or version
include:
  - component: gitlab.com/group/component@v1.0.0  # Wrong: 'v' prefix

# Solution: Use correct version format
include:
  - component: gitlab.com/group/component@1.0.0
```

### "Maximum inputs exceeded"

- Pipelines support maximum **20 inputs**
- Consolidate related inputs or use array types

### Input Not Expanding

```yaml
# Problem: Using wrong syntax
script: echo "inputs.name"

# Solution: Use interpolation syntax
script: echo "$[[ inputs.name ]]"
```
