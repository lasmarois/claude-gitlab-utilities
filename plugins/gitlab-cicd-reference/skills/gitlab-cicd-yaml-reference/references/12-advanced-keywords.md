# GitLab CI/CD Advanced Keywords Reference

> Less common but powerful keywords: release, pages, inherit, identity, merge trains, and more.

---

## release Keyword

Create GitLab releases automatically from pipelines.

### Basic Release

```yaml
release_job:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  rules:
    - if: $CI_COMMIT_TAG
  release:
    tag_name: $CI_COMMIT_TAG
    description: "Release $CI_COMMIT_TAG"
```

### Full Release Configuration

```yaml
release_job:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  rules:
    - if: $CI_COMMIT_TAG
  release:
    tag_name: $CI_COMMIT_TAG
    name: "Release $CI_COMMIT_TAG"
    description: "Automatic release for $CI_COMMIT_TAG"
    ref: $CI_COMMIT_SHA
    milestones:
      - "v1.0"
    released_at: "2024-01-15T12:00:00Z"  # Optional, defaults to now
    assets:
      links:
        - name: "Binary (Linux)"
          url: "https://example.com/releases/$CI_COMMIT_TAG/binary-linux"
          filepath: "/binaries/linux/app"
          link_type: "package"
        - name: "Documentation"
          url: "https://docs.example.com/$CI_COMMIT_TAG"
          link_type: "other"
```

### Release with Changelog

```yaml
release_job:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  script:
    - echo "Generating changelog..."
  release:
    tag_name: $CI_COMMIT_TAG
    description: "./CHANGELOG.md"  # Read from file
```

### Dynamic Release Description

```yaml
release_job:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  script:
    - |
      cat > release_notes.md << EOF
      ## What's Changed
      $(git log --oneline $(git describe --tags --abbrev=0 HEAD^)..HEAD)

      ## Contributors
      $(git log --format='- %an' $(git describe --tags --abbrev=0 HEAD^)..HEAD | sort -u)
      EOF
  release:
    tag_name: $CI_COMMIT_TAG
    description: release_notes.md

### Release Asset Types

```yaml
release:
  assets:
    links:
      - name: "Asset Name"
        url: "https://example.com/asset"
        link_type: "package"     # Downloadable package
        # link_type: "runbook"   # Documentation
        # link_type: "image"     # Container image
        # link_type: "other"     # Anything else
```

---

## pages Keyword

Deploy static content to GitLab Pages.

### Basic Pages Deployment

```yaml
pages:
  stage: deploy
  script:
    - npm run build
  artifacts:
    paths:
      - public  # Must be named "public"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Pages with Custom Build

```yaml
pages:
  image: node:18
  script:
    - npm ci
    - npm run build
    - mv dist public  # Rename to public
  artifacts:
    paths:
      - public
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Pages with Hugo

```yaml
pages:
  image: registry.gitlab.com/pages/hugo:latest
  script:
    - hugo
  artifacts:
    paths:
      - public
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### pages:publish (GitLab 16.1+)

Specify output directory without renaming:

```yaml
pages:
  script:
    - npm run build  # Outputs to dist/
  artifacts:
    paths:
      - dist
  publish: dist  # Use dist instead of public
```

### pages:pages (Disable Auto-Deploy)

```yaml
pages:
  script:
    - npm run build
  artifacts:
    paths:
      - public
  pages:
    path_prefix: "$CI_COMMIT_REF_SLUG"  # Deploy to subdirectory
```

---

## inherit Keyword

Control which global/default settings jobs inherit.

### Disable All Inheritance

```yaml
default:
  image: ruby:3.0
  before_script:
    - bundle install

job:
  inherit:
    default: false  # Inherit nothing from default
  script: echo "No image or before_script"
```

### Selective Default Inheritance

```yaml
default:
  image: ruby:3.0
  before_script:
    - bundle install
  after_script:
    - cleanup.sh

job:
  inherit:
    default:
      - image  # Only inherit image
      # before_script and after_script not inherited
  script: echo "Only has image"
```

### Variable Inheritance

```yaml
variables:
  GLOBAL_VAR: "value"
  ANOTHER_VAR: "another"

job:
  inherit:
    variables: false  # Inherit no global variables
  script: echo "No GLOBAL_VAR"

job2:
  inherit:
    variables:
      - GLOBAL_VAR  # Only inherit GLOBAL_VAR
  script: echo "$GLOBAL_VAR"
```

### Combined Inheritance Control

```yaml
default:
  image: ruby:3.0
  before_script:
    - setup.sh

variables:
  DATABASE_URL: "postgres://..."

minimal-job:
  inherit:
    default: false
    variables: false
  image: alpine:latest
  script: echo "Truly minimal job"

partial-job:
  inherit:
    default:
      - image
    variables:
      - DATABASE_URL
  script: echo "Selective inheritance"
```

---

## identity Keyword

Authenticate with external services using OIDC federation.

### Basic Identity

```yaml
job:
  identity: google_cloud
  script:
    - gcloud storage ls
```

### With Provider Configuration

```yaml
deploy:
  identity:
    provider: google_cloud
  variables:
    GOOGLE_CLOUD_PROJECT: my-project
  script:
    - gcloud run deploy my-service
```

### Multiple Identities

```yaml
multi-cloud:
  id_tokens:
    AWS_TOKEN:
      aud: sts.amazonaws.com
    GCP_TOKEN:
      aud: https://iam.googleapis.com/...
  script:
    - # Use both cloud providers
```

---

## manual_confirmation Keyword

Custom confirmation message for manual jobs.

```yaml
deploy-production:
  stage: deploy
  script: ./deploy.sh production
  when: manual
  manual_confirmation: "Are you sure you want to deploy to production? This will affect all users."
```

### With Environment Context

```yaml
deploy-production:
  script: ./deploy.sh
  environment:
    name: production
  when: manual
  manual_confirmation: |
    You are about to deploy to PRODUCTION.

    Current version: $CURRENT_VERSION
    New version: $CI_COMMIT_TAG

    Type 'deploy' to confirm.
```

---

## Merge Trains

Queue merges to ensure they all work together.

### Enable Merge Trains

Configure in **Settings > Merge requests**:
1. Enable "Merge trains"
2. Optionally enable "Pipelines must succeed"

### Pipeline Configuration

```yaml
workflow:
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

test:
  script: ./test.sh
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

### Merge Train Behavior

- MRs queue when "Merge" clicked
- Each MR's pipeline runs against merged result of all preceding MRs
- Failed MR is removed, pipelines restart for remaining MRs

### Skip Merge Train (Emergency)

Use "Merge immediately" for critical patches (restarts all queued pipelines).

---

## dast_configuration Keyword

Specify DAST profiles for security scanning.

```yaml
dast:
  dast_configuration:
    site_profile: "My Site Profile"
    scanner_profile: "My Scanner Profile"
```

---

## run Keyword (Experimental)

Runtime execution configuration.

```yaml
job:
  run:
    # Experimental features
```

---

## Hook Scripts

### hooks:pre_get_sources_script

Run before source checkout:

```yaml
job:
  hooks:
    pre_get_sources_script:
      - echo "Preparing environment"
      - setup-credentials.sh
  script:
    - build.sh
```

---

## Job Scheduling

### start_in with delayed

```yaml
delayed-job:
  script: ./notify.sh
  when: delayed
  start_in: 30 minutes
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Dynamic Delay

```yaml
notify:
  when: delayed
  start_in: $DELAY_DURATION  # From variable
  script: ./send-notification.sh
```

---

## Interruptible Pipelines

### workflow:auto_cancel

```yaml
workflow:
  auto_cancel:
    on_new_commit: interruptible
    on_job_failure: all
```

**on_new_commit options:**
- `conservative` - Cancel only if all jobs are interruptible
- `interruptible` - Cancel interruptible jobs only
- `none` - Never auto-cancel

**on_job_failure options:**
- `none` - Don't cancel on failure
- `all` - Cancel all jobs when any fails

### Per-Rule Auto-Cancel

```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      auto_cancel:
        on_new_commit: none  # Never cancel main branch
    - if: $CI_MERGE_REQUEST_IID
      auto_cancel:
        on_new_commit: interruptible
```

---

## Pipeline Naming

### workflow:name

```yaml
workflow:
  name: "Pipeline for $CI_COMMIT_REF_NAME"
  rules:
    - if: $CI_MERGE_REQUEST_IID
      variables:
        PIPELINE_NAME: "MR: $CI_MERGE_REQUEST_TITLE"
    - when: always

# Dynamic name
workflow:
  name: "$PIPELINE_NAME"
```

---

## trigger:forward

Control variable forwarding to downstream pipelines.

```yaml
trigger-downstream:
  trigger:
    project: group/downstream
    forward:
      yaml_variables: true      # Forward YAML-defined variables
      pipeline_variables: false  # Don't forward trigger variables
```

### Forward Options

```yaml
trigger:
  forward:
    yaml_variables: true|false       # Variables from .gitlab-ci.yml
    pipeline_variables: true|false   # Variables from trigger/API
```

---

## Image Pull Policies

### pull_policy

```yaml
job:
  image:
    name: my-registry/image:latest
    pull_policy: if-not-present
```

**Options:**
- `always` - Always pull (default)
- `if-not-present` - Pull only if not cached
- `never` - Never pull (must exist locally)

### Multiple Policies

```yaml
job:
  image:
    name: my-image:latest
    pull_policy:
      - if-not-present
      - always  # Fallback
```

---

## Service Pull Policy

```yaml
job:
  services:
    - name: postgres:15
      pull_policy: if-not-present
```

---

## Job Log Sections

### Collapsible Sections

```yaml
job:
  script:
    - echo -e "\e[0Ksection_start:$(date +%s):build_section\r\e[0KBuild Section"
    - ./build.sh
    - echo -e "\e[0Ksection_end:$(date +%s):build_section\r\e[0K"
    - echo -e "\e[0Ksection_start:$(date +%s):test_section[collapsed=true]\r\e[0KTest Section"
    - ./test.sh
    - echo -e "\e[0Ksection_end:$(date +%s):test_section\r\e[0K"
```

### Helper Function

```yaml
.log-sections:
  before_script:
    - |
      section_start() {
        echo -e "\e[0Ksection_start:$(date +%s):$1\r\e[0K$2"
      }
      section_end() {
        echo -e "\e[0Ksection_end:$(date +%s):$1\r\e[0K"
      }

job:
  extends: .log-sections
  script:
    - section_start "setup" "Setting up environment"
    - npm install
    - section_end "setup"
```

---

## Exit Codes

### allow_failure:exit_codes

```yaml
test:
  script: ./test.sh
  allow_failure:
    exit_codes:
      - 42  # Known non-critical failure
      - 137 # OOM killed
```

### retry:exit_codes

```yaml
test:
  script: ./flaky-test.sh
  retry:
    max: 2
    when: script_failure
    exit_codes:
      - 1   # General failure
      - 137 # OOM
```

---

## Debugging Features

### CI_DEBUG_TRACE

```yaml
debug-job:
  variables:
    CI_DEBUG_TRACE: "true"  # Verbose output (exposes secrets!)
  script: ./debug.sh
```

### CI_DEBUG_SERVICES

```yaml
debug-services:
  variables:
    CI_DEBUG_SERVICES: "true"  # Show service container logs
  services:
    - postgres:15
  script: ./test.sh
```

---

## Deprecated Keywords

### only/except (Use rules instead)

```yaml
# Deprecated
job:
  only:
    - main
  except:
    - tags

# Modern equivalent
job:
  rules:
    - if: $CI_COMMIT_BRANCH == "main" && $CI_COMMIT_TAG == null
```

### type (Use stage instead)

```yaml
# Deprecated
job:
  type: build

# Modern equivalent
job:
  stage: build
```

---

## Experimental Features

Check GitLab release notes for experimental features:

- `run` keyword
- New auto_cancel options
- Pipeline composition features

Enable via feature flags in self-managed instances.
