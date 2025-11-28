# GitLab CI/CD YAML Optimization and Code Reuse

> DRY (Don't Repeat Yourself) patterns using extends, anchors, includes, and !reference tags.

---

## extends Keyword

Inherit configuration from hidden jobs (jobs starting with `.`):

### Basic extends

```yaml
.test-template:
  stage: test
  image: ruby:3.0
  before_script:
    - bundle install
  cache:
    key: gems
    paths:
      - vendor/bundle

rspec:
  extends: .test-template
  script: bundle exec rspec

rubocop:
  extends: .test-template
  script: bundle exec rubocop
```

**Result:** Both `rspec` and `rubocop` inherit stage, image, before_script, and cache from `.test-template`.

### Multi-level extends

```yaml
.base:
  image: ruby:3.0
  tags:
    - docker

.tests:
  extends: .base
  stage: test
  before_script:
    - bundle install

.rspec:
  extends: .tests
  script: rake rspec

rspec-unit:
  extends: .rspec
  variables:
    RSPEC_SUITE: unit

rspec-integration:
  extends: .rspec
  variables:
    RSPEC_SUITE: integration
```

**Warning:** Avoid more than 3 levels of inheritance—it becomes hard to trace configuration.

### Multiple extends

```yaml
.only-default-branch:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

.docker-build:
  image: docker:24
  services:
    - docker:24-dind

build-production:
  extends:
    - .docker-build
    - .only-default-branch
  script: docker build -t my-app .
```

**Merge order:** Listed first = lowest priority, listed last = highest priority for conflicts.

### Overriding extended configuration

```yaml
.tests:
  image: ruby:3.0
  script: rake test
  variables:
    DEBUG: "false"

unit-tests:
  extends: .tests
  variables:
    DEBUG: "true"  # Overrides parent
    EXTRA_VAR: "value"  # Adds new variable

# Override with empty/null
minimal-test:
  extends: .tests
  before_script: []  # Empty array (clears any inherited before_script)
  
no-vars-test:
  extends: .tests
  variables: null  # Completely removes variables section
```

**Merge behavior:** 
- Scalars (strings, numbers): Child overrides parent
- Arrays: Child replaces entire array (no merge)
- Maps/hashes: Deep merge (child keys override, but unspecified keys inherited)

---

## YAML Anchors

Native YAML feature for content reuse:

### Basic anchors

```yaml
# Define anchor with &
.job_template: &job_configuration
  image: ruby:3.0
  services:
    - postgres
    - redis

# Reference anchor with *
test1:
  <<: *job_configuration  # Merge anchor contents
  script: test1 project

test2:
  <<: *job_configuration
  script: test2 project
```

**Syntax:**
- `&name` - Define anchor
- `*name` - Reference anchor value
- `<<: *name` - Merge anchor map into current map

### Script anchors

```yaml
.before-script: &before-script
  - echo "Setting up..."
  - npm install

.after-script: &after-script
  - echo "Cleaning up..."
  - rm -rf tmp/

.test-script: &test-script
  - npm test
  - npm run coverage

job1:
  before_script:
    - *before-script
  script:
    - *test-script
    - npm run lint  # Additional commands
  after_script:
    - *after-script

job2:
  script:
    - *before-script  # Can inline in script section
    - *test-script
    - *after-script
```

### Service anchors

```yaml
.postgres-service: &postgres-service
  - postgres:15

.redis-service: &redis-service
  - redis:7

.mysql-service: &mysql-service
  - mysql:8.0

test-postgres:
  services: *postgres-service
  script: ./test.sh

test-mysql:
  services: *mysql-service
  script: ./test.sh

test-all:
  services:
    - *postgres-service
    - *redis-service
  script: ./integration-test.sh
```

### Advanced anchor merging

```yaml
.job_template: &job_configuration
  script:
    - test project
  tags:
    - dev

.postgres_services: &postgres_services
  services:
    - postgres
    - ruby

.mysql_services: &mysql_services
  services:
    - mysql
    - ruby

test:postgres:
  <<: *job_configuration
  services: *postgres_services  # Can't use << for arrays
  tags:
    - postgres  # Override tags

test:mysql:
  <<: *job_configuration
  services: *mysql_services
```

### Anchor limitations

1. **File scope:** Anchors only work within the same file (not across `include`d files)
2. **No cross-file:** Use `extends` or `!reference` for multi-file configurations
3. **Arrays don't merge:** `<<:` only works for maps/hashes

---

## include Keyword

Import configuration from other files:

### Local includes

```yaml
include:
  - local: '/templates/build.yml'
  - local: '/templates/test.yml'
```

### Project includes

```yaml
include:
  - project: 'my-group/my-ci-templates'
    ref: main
    file: '/templates/.build.yml'
  
  # Multiple files from same project
  - project: 'my-group/my-ci-templates'
    ref: v1.0.0
    file:
      - '/templates/.build.yml'
      - '/templates/.test.yml'
```

### Remote includes

```yaml
include:
  - remote: 'https://example.com/ci-templates/build.yml'
```

### Template includes

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Code-Quality.gitlab-ci.yml
```

### Conditional includes

```yaml
include:
  - local: build_jobs.yml
    rules:
      - if: $INCLUDE_BUILDS == "true"

  - local: test_jobs.yml
    rules:
      - exists:
          - tests/**/*.py

  - project: my-group/templates
    file: deploy.yml
    rules:
      - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
        changes:
          - deploy/**/*
```

### Combining extends and include

```yaml
# templates/base.yml
.base-job:
  image: ruby:3.0
  cache:
    key: gems
    paths:
      - vendor/bundle

# .gitlab-ci.yml
include:
  - local: templates/base.yml

rspec:
  extends: .base-job
  script: bundle exec rspec
```

---

## !reference Tag

Selectively reuse specific parts of configuration:

### Basic !reference

```yaml
.vars:
  variables:
    VAR1: "value1"
    VAR2: "value2"

.scripts:
  script:
    - echo "Running tests"
    - npm test

job:
  variables: !reference [.vars, variables]
  script: !reference [.scripts, script]
```

### Partial script reuse

```yaml
.setup:
  script:
    - echo "Setting up environment"
    - npm install

.teardown:
  after_script:
    - echo "Cleaning up"
    - rm -rf node_modules

test:
  script:
    - !reference [.setup, script]
    - npm test
    - echo "Additional test commands"
  after_script:
    - !reference [.teardown, after_script]
```

### !reference from included files

```yaml
# templates/configs.yml
.default-cache:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/

.default-rules:
  rules:
    - if: $CI_COMMIT_BRANCH
    - if: $CI_MERGE_REQUEST_ID

# .gitlab-ci.yml
include:
  - local: templates/configs.yml

build:
  cache: !reference [.default-cache, cache]
  rules: !reference [.default-rules, rules]
  script: npm run build
```

### Combining !reference with arrays

```yaml
.strict-rules:
  rules:
    - if: '$CI_PROJECT_NAME !~ /^allowed-project$/'
      when: never

.mr-rules:
  rules:
    - if: '$CI_MERGE_REQUEST_ID'

.combined-rules:
  rules:
    - !reference [.strict-rules, rules]
    - !reference [.mr-rules, rules]
    - when: manual

job:
  rules: !reference [.combined-rules, rules]
  script: echo "Job with combined rules"
```

### !reference with map merging

```yaml
.base-vars:
  variables:
    BASE_VAR: "base"
    SHARED_VAR: "from-base"

.override-vars:
  variables:
    OVERRIDE_VAR: "override"
    SHARED_VAR: "from-override"

# Note: This creates separate arrays, not merged maps
job:
  variables:
    - !reference [.base-vars, variables]
    - !reference [.override-vars, variables]
    - JOB_VAR: "job-specific"
```

---

## Optimization Patterns

### Template library structure

```
ci-templates/
├── .gitlab-ci.yml           # Main entry point
├── jobs/
│   ├── build.yml
│   ├── test.yml
│   └── deploy.yml
├── templates/
│   ├── .base.yml            # Hidden templates
│   ├── .docker.yml
│   └── .security.yml
└── rules/
    ├── branch-rules.yml
    └── mr-rules.yml
```

### Centralized templates project

```yaml
# In any project's .gitlab-ci.yml
include:
  - project: 'devops/ci-templates'
    ref: v2.0.0  # Pin to version
    file:
      - '/jobs/build.yml'
      - '/jobs/test.yml'
      - '/jobs/deploy.yml'

variables:
  PROJECT_TYPE: "nodejs"  # Configure template behavior
```

### Environment-specific configuration

```yaml
.deploy-template:
  script:
    - deploy.sh $ENVIRONMENT
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-staging:
  extends: .deploy-template
  variables:
    ENVIRONMENT: staging
  environment:
    name: staging

deploy-production:
  extends: .deploy-template
  variables:
    ENVIRONMENT: production
  environment:
    name: production
  when: manual
```

### DRY rules

```yaml
.rules:feature-branches:
  rules:
    - if: $CI_COMMIT_BRANCH && $CI_COMMIT_BRANCH != $CI_DEFAULT_BRANCH

.rules:main-only:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

.rules:merge-requests:
  rules:
    - if: $CI_MERGE_REQUEST_ID

test:
  extends: .rules:feature-branches
  script: npm test

deploy-staging:
  extends: .rules:main-only
  script: deploy staging

code-review:
  extends: .rules:merge-requests
  script: npm run lint
```

---

## Validation and Debugging

### VS Code YAML schema

Add to VS Code settings for `!reference` tag support:

```json
{
  "yaml.customTags": [
    "!reference sequence"
  ]
}
```

### CI Lint API

Validate merged configuration:

```bash
# Get merged YAML
curl --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.example.com/api/v4/projects/:id/ci/lint?include_merged_yaml=true"
```

### Debugging extends inheritance

Use the pipeline editor or CI Lint to see the final merged configuration after all `extends` are resolved.

### Common pitfalls

1. **Anchor scope:** Anchors don't work across `include`d files—use `extends` or `!reference` instead

2. **Array merging:** Arrays are replaced, not merged
   ```yaml
   .base:
     script:
       - base-command
   
   job:
     extends: .base
     script:
       - job-command  # Replaces base-command entirely
   ```

3. **Circular extends:** GitLab detects and errors on circular inheritance

4. **Hidden job naming:** Jobs starting with `.` are hidden—ensure your templates use this convention

5. **Include order:** Later includes override earlier ones for duplicate keys
