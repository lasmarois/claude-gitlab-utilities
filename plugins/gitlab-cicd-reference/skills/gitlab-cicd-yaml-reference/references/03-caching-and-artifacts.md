# GitLab CI/CD Caching and Artifacts Reference

> Advanced caching strategies and artifact management for optimizing pipeline performance.

---

## Cache vs Artifacts: Key Differences

| Aspect | Cache | Artifacts |
|--------|-------|-----------|
| Purpose | Speed up jobs by reusing files | Pass files between jobs/stages |
| Persistence | Best-effort (may be cleared) | Guaranteed (stored in GitLab) |
| Scope | Per-runner or distributed | Per-pipeline/job |
| Use case | Dependencies, node_modules, vendor | Build outputs, test results, binaries |
| Download | Before job starts | Before job starts (if needed) |
| Upload | After job completes | After job completes |

---

## Cache Configuration

### Basic cache

```yaml
build:
  script: npm install && npm run build
  cache:
    paths:
      - node_modules/
```

### cache:key

Create unique caches to avoid conflicts:

```yaml
# Per-branch cache
cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - node_modules/

# Per-job and branch
cache:
  key: "$CI_JOB_NAME-$CI_COMMIT_REF_SLUG"
  paths:
    - vendor/

# Static key (shared across all branches)
cache:
  key: project-dependencies
  paths:
    - node_modules/
```

### cache:key:files (Hash-based keys)

Generate key from file contents:

```yaml
# Cache invalidates when package.json or yarn.lock changes
cache:
  key:
    files:
      - package.json
      - yarn.lock
  paths:
    - node_modules/

# With prefix
cache:
  key:
    files:
      - Gemfile.lock
    prefix: $CI_JOB_NAME
  paths:
    - vendor/ruby/
```

### cache:key:files_commits

Key based on file commit history (changes when files are updated, even with same content):

```yaml
cache:
  key:
    files_commits:
      - package.json
      - yarn.lock
  paths:
    - node_modules/
```

### cache:fallback_keys

Define fallback keys when primary cache misses:

```yaml
test:
  cache:
    key: cache-$CI_COMMIT_REF_SLUG
    fallback_keys:
      - cache-$CI_DEFAULT_BRANCH
      - cache-default
    paths:
      - vendor/ruby/
  script:
    - bundle install --path vendor/ruby
    - bundle exec rspec
```

**Fallback order:** Primary key → fallback_keys (in order) → `CACHE_FALLBACK_KEY` variable

### Global fallback key

```yaml
variables:
  CACHE_FALLBACK_KEY: default-cache

job:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - binaries/
```

### cache:policy

Control upload/download behavior:

```yaml
# pull-push (default): Download at start, upload at end
# pull: Only download, never upload
# push: Only upload, never download

# Typical pattern: One job builds cache, others consume it
install-deps:
  stage: build
  cache:
    key: deps-$CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
    policy: push  # Only uploads
  script:
    - npm ci

test:
  stage: test
  cache:
    key: deps-$CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
    policy: pull  # Only downloads
  script:
    - npm test
```

### Dynamic cache policy

```yaml
conditional-cache:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        POLICY: pull-push  # Update cache on main branch
    - if: $CI_COMMIT_BRANCH != $CI_DEFAULT_BRANCH
      variables:
        POLICY: pull  # Feature branches only read
  cache:
    key: shared-cache
    policy: $POLICY
    paths:
      - vendor/
  script:
    - bundle install
```

### cache:when

Control when cache is saved:

```yaml
install:
  script: npm install
  cache:
    paths:
      - node_modules/
    when: on_success  # Default: only save on success

# Save cache even on failure
install:
  script: npm install
  cache:
    paths:
      - node_modules/
    when: on_failure  # Save for debugging

# Always save
install:
  script: npm install
  cache:
    paths:
      - node_modules/
    when: always
```

### cache:untracked

Include untracked Git files in cache:

```yaml
cache:
  untracked: true
  paths:
    - node_modules/
```

### cache:unprotect

Allow unprotected branches to access protected branch cache:

```yaml
cache:
  key: shared-cache
  unprotect: true  # Feature branches can use main branch cache
  paths:
    - vendor/
```

### Multiple caches

```yaml
test:
  cache:
    - key: npm-$CI_COMMIT_REF_SLUG
      paths:
        - node_modules/
    - key: pip-$CI_COMMIT_REF_SLUG
      paths:
        - .pip-cache/
  script:
    - npm ci
    - pip install -r requirements.txt
```

---

## Cache Compression

```yaml
variables:
  # Options: fastest, fast, default, slow, slowest
  CACHE_COMPRESSION_LEVEL: "fast"
```

| Level | Speed | Size |
|-------|-------|------|
| fastest | Fastest | Largest |
| fast | Fast | Large |
| default | Balanced | Medium |
| slow | Slow | Small |
| slowest | Slowest | Smallest |

---

## Distributed Cache (S3/GCS)

Configure in runner's `config.toml`:

```toml
[runners.cache]
  Type = "s3"
  Shared = true  # Share cache across runners

  [runners.cache.s3]
    ServerAddress = "s3.amazonaws.com"
    BucketName = "gitlab-runner-cache"
    BucketLocation = "us-east-1"
```

---

## Artifacts Configuration

### artifacts:paths

```yaml
build:
  script: make
  artifacts:
    paths:
      - binaries/
      - dist/*.js
      - "**/*.o"  # Glob patterns supported
```

### artifacts:exclude

```yaml
build:
  script: make
  artifacts:
    paths:
      - build/
    exclude:
      - build/**/*.log
      - build/tmp/
```

### artifacts:expire_in

```yaml
build:
  script: make
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

# Duration formats:
# 42, 42 seconds, 3 mins 4 sec
# 2 hrs 20 min, 2h20min
# 6 mos 1 day, 47 yrs 6 mos and 4d
# never (keeps forever)
```

### artifacts:when

```yaml
test:
  script: npm test
  artifacts:
    paths:
      - test-results/
    when: always  # Upload even on failure

# Options: on_success (default), on_failure, always
```

### artifacts:name

```yaml
build:
  script: make
  artifacts:
    name: "build-$CI_COMMIT_REF_SLUG-$CI_JOB_ID"
    paths:
      - dist/
```

### artifacts:expose_as

Make artifacts downloadable from MR UI:

```yaml
build:
  script: make docs
  artifacts:
    paths:
      - public/
    expose_as: 'Documentation'  # Shows link in MR
```

### artifacts:public

Control artifact visibility:

```yaml
build:
  artifacts:
    public: false  # Only accessible to project members
    paths:
      - dist/
```

---

## Artifact Reports

### JUnit test reports

```yaml
test:
  script: pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml

# Multiple files
test:
  artifacts:
    reports:
      junit:
        - rspec.xml
        - test-results/**/*.xml
```

### Coverage reports

```yaml
test:
  script: pytest --cov --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### dotenv reports (pass variables)

```yaml
build:
  script:
    - echo "VERSION=$(cat VERSION)" >> build.env
  artifacts:
    reports:
      dotenv: build.env

deploy:
  script:
    - echo "Deploying version $VERSION"
```

### Other report types

```yaml
artifacts:
  reports:
    # Security reports
    sast: gl-sast-report.json
    dast: gl-dast-report.json
    dependency_scanning: gl-dependency-scanning-report.json
    container_scanning: gl-container-scanning-report.json
    secret_detection: gl-secret-detection-report.json
    
    # Quality reports
    codequality: gl-code-quality-report.json
    
    # Terraform
    terraform: plan.json
    
    # Performance
    load_performance: load-performance.json
    browser_performance: sitespeed-results.json
```

---

## Controlling Artifact Dependencies

### dependencies

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
    - build  # Download only from build job
  script: ./test.sh

deploy:
  stage: deploy
  dependencies: []  # Download no artifacts
  script: ./deploy.sh
```

### needs:artifacts

```yaml
test:
  needs:
    - job: build
      artifacts: true  # Download artifacts (default)
    - job: lint
      artifacts: false  # No artifacts needed
  script: ./test.sh
```

### Cross-project artifacts

```yaml
deploy:
  needs:
    - project: namespace/other-project
      job: build
      ref: main
      artifacts: true
  script: ./deploy.sh
```

### Parent-child pipeline artifacts

```yaml
# In child pipeline
test:
  needs:
    - pipeline: $PARENT_PIPELINE_ID
      job: build
      artifacts: true
  script: ./test.sh
```

---

## Caching Strategies by Language

### Node.js / npm

```yaml
variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

cache:
  key:
    files:
      - package-lock.json
  paths:
    - .npm/
    - node_modules/

install:
  script: npm ci --cache .npm
```

### Python / pip

```yaml
variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"

cache:
  key:
    files:
      - requirements.txt
  paths:
    - .pip-cache/
    - venv/

install:
  script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
```

### Ruby / Bundler

```yaml
variables:
  BUNDLE_PATH: vendor/bundle

cache:
  key:
    files:
      - Gemfile.lock
  paths:
    - vendor/bundle/

install:
  script:
    - bundle config set --local path 'vendor/bundle'
    - bundle install
```

### Go

```yaml
variables:
  GOPATH: "$CI_PROJECT_DIR/.go"

cache:
  key: go-modules
  paths:
    - .go/pkg/mod/

build:
  script: go build ./...
```

### Maven / Java

```yaml
variables:
  MAVEN_OPTS: "-Dmaven.repo.local=$CI_PROJECT_DIR/.m2/repository"

cache:
  key:
    files:
      - pom.xml
  paths:
    - .m2/repository/

build:
  script: mvn package
```

### Gradle / Java

```yaml
variables:
  GRADLE_USER_HOME: "$CI_PROJECT_DIR/.gradle"

cache:
  key:
    files:
      - build.gradle
      - gradle/wrapper/gradle-wrapper.properties
  paths:
    - .gradle/caches/
    - .gradle/wrapper/

build:
  script: ./gradlew build
```

---

## Docker Image Caching

### Registry-based caching

```yaml
build:
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker context create builder
    - docker buildx create builder --driver docker-container --use
    - |
      docker buildx build \
        --push \
        -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA \
        --cache-to type=registry,ref=$CI_REGISTRY_IMAGE/cache,mode=max \
        --cache-from type=registry,ref=$CI_REGISTRY_IMAGE/cache \
        .
```

### Multi-stage build caching

```yaml
build:
  script:
    - |
      docker build \
        --cache-from $CI_REGISTRY_IMAGE:cache \
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA \
        --tag $CI_REGISTRY_IMAGE:cache \
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:cache
```

---

## Best Practices

### Cache Optimization

1. **Use hash-based keys** for lockfiles to invalidate on dependency changes
2. **Implement fallback keys** to get partial cache hits on feature branches
3. **Separate caches** by language/tool when using multiple ecosystems
4. **Use pull-only policy** for jobs that don't modify dependencies
5. **Set appropriate compression** based on upload speed vs. archive size

### Artifact Optimization

1. **Set expire_in** to avoid storage bloat (default is 30 days)
2. **Use exclude** to filter out logs and temporary files
3. **Minimize artifact size** by only including what's needed
4. **Use reports** for structured data (JUnit, coverage) that integrates with GitLab UI
5. **Empty dependencies** for jobs that don't need upstream artifacts

### Performance Tips

```yaml
variables:
  # Increase artifact transfer frequency feedback
  TRANSFER_METER_FREQUENCY: "2s"
  
  # Fast compression for faster uploads
  ARTIFACT_COMPRESSION_LEVEL: "fast"
  
  # No compression for caches (smaller impact, faster transfer)
  CACHE_COMPRESSION_LEVEL: "fastest"
  
  # Cache request timeout
  CACHE_REQUEST_TIMEOUT: 10
```

### Common Issues and Solutions

**Cache not being used:**
- Check key matches between jobs
- Verify paths are correct (relative to project root)
- Protected/unprotected branch cache separation

**Artifacts missing:**
- Check `expire_in` hasn't passed
- Verify `dependencies` or `needs` includes the producing job
- Check job actually succeeded (artifacts:when setting)

**Slow cache/artifact operations:**
- Reduce artifact/cache size
- Use distributed cache (S3/GCS) for geographically distributed runners
- Adjust compression settings
