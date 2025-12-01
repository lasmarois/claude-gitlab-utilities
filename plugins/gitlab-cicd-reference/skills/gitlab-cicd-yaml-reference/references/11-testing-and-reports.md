# GitLab CI/CD Testing and Reports Reference

> Test reports, code coverage, code quality, security scanning, and test result visualization.

---

## Test Reports Overview

GitLab can display test results directly in:
- Merge request widgets
- Pipeline pages
- Job pages

This enables quick identification of test failures without reading job logs.

---

## Unit Test Reports (JUnit)

### Basic JUnit Report

```yaml
test:
  script: pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
```

### Multiple Report Files

```yaml
test:
  script:
    - npm test
    - pytest
  artifacts:
    reports:
      junit:
        - jest-results.xml
        - pytest-results.xml
        - "test-results/**/*.xml"  # Glob pattern
```

### Language-Specific Examples

#### Python (pytest)

```yaml
test-python:
  image: python:3.11
  script:
    - pip install pytest pytest-cov
    - pytest --junitxml=report.xml --cov=myapp --cov-report=xml
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

#### JavaScript (Jest)

```yaml
test-js:
  image: node:18
  script:
    - npm ci
    - npm test -- --ci --reporters=default --reporters=jest-junit
  artifacts:
    reports:
      junit: junit.xml
```

#### Java (Maven)

```yaml
test-java:
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn test
  artifacts:
    reports:
      junit:
        - target/surefire-reports/TEST-*.xml
```

#### Go

```yaml
test-go:
  image: golang:1.21
  script:
    - go install gotest.tools/gotestsum@latest
    - gotestsum --junitfile report.xml ./...
  artifacts:
    reports:
      junit: report.xml
```

#### Ruby (RSpec)

```yaml
test-ruby:
  image: ruby:3.2
  script:
    - bundle install
    - bundle exec rspec --format RspecJunitFormatter --out rspec.xml
  artifacts:
    reports:
      junit: rspec.xml
```

#### C# (.NET)

```yaml
test-dotnet:
  image: mcr.microsoft.com/dotnet/sdk:7.0
  script:
    - dotnet test --logger "junit;LogFilePath=TestResults/results.xml"
  artifacts:
    reports:
      junit: TestResults/results.xml
```

---

## Code Coverage

### coverage Keyword

Extract coverage percentage from job output:

```yaml
test:
  script:
    - pytest --cov=myapp
  coverage: '/TOTAL.*\s+(\d+%)$/'  # Regex to extract percentage
```

### Coverage Report Formats

```yaml
test:
  script: pytest --cov --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

**Supported formats:**
- `cobertura` - XML format (most common)
- `jacoco` - Java coverage format

### Coverage Visualization in MR

```yaml
test:
  script:
    - pytest --cov=src --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

Displays:
- Line-by-line coverage diff in MR
- Overall coverage percentage
- Coverage trend badge

### Multiple Coverage Reports

```yaml
test:
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      # Note: Only one coverage_report per job
      # Merge reports before uploading
```

### Coverage Badge

Add to README.md:

```markdown
![coverage](https://gitlab.com/namespace/project/badges/main/coverage.svg)
```

---

## Code Quality

### Using Code Climate

```yaml
include:
  - template: Code-Quality.gitlab-ci.yml

code_quality:
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

### Custom Code Quality Report

```yaml
lint:
  script:
    - eslint --format gitlab src/
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

### Code Quality Report Format

```json
[
  {
    "description": "Avoid using var",
    "check_name": "no-var",
    "fingerprint": "abc123",
    "severity": "minor",
    "location": {
      "path": "src/index.js",
      "lines": {
        "begin": 10
      }
    }
  }
]
```

**Severity levels:** `info`, `minor`, `major`, `critical`, `blocker`

---

## Security Scanning Reports

### SAST (Static Application Security Testing)

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

# Or custom job
sast:
  script:
    - ./run-sast.sh
  artifacts:
    reports:
      sast: gl-sast-report.json
```

### DAST (Dynamic Application Security Testing)

```yaml
include:
  - template: Security/DAST.gitlab-ci.yml

dast:
  variables:
    DAST_WEBSITE: https://staging.example.com
```

### Dependency Scanning

```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

dependency_scanning:
  artifacts:
    reports:
      dependency_scanning: gl-dependency-scanning-report.json
```

### Container Scanning

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

container_scanning:
  variables:
    CI_APPLICATION_REPOSITORY: $CI_REGISTRY_IMAGE
    CI_APPLICATION_TAG: $CI_COMMIT_SHA
```

### Secret Detection

```yaml
include:
  - template: Security/Secret-Detection.gitlab-ci.yml

secret_detection:
  artifacts:
    reports:
      secret_detection: gl-secret-detection-report.json
```

### License Scanning

```yaml
include:
  - template: Security/License-Scanning.gitlab-ci.yml

license_scanning:
  artifacts:
    reports:
      license_scanning: gl-license-scanning-report.json
```

---

## Performance Testing

### Browser Performance

```yaml
include:
  - template: Verify/Browser-Performance.gitlab-ci.yml

browser_performance:
  variables:
    URL: https://staging.example.com
  artifacts:
    reports:
      browser_performance: sitespeed-results/data/browsertime.pageSummary.json
```

### Load Performance

```yaml
include:
  - template: Verify/Load-Performance.gitlab-ci.yml

load_performance:
  variables:
    K6_TEST_FILE: loadtest.js
  artifacts:
    reports:
      load_performance: load-performance.json
```

---

## Accessibility Testing

```yaml
include:
  - template: Verify/Accessibility.gitlab-ci.yml

a11y:
  variables:
    a11y_urls: https://staging.example.com
  artifacts:
    reports:
      accessibility: gl-accessibility.json
```

---

## Metrics Reports

Track custom metrics over time:

```yaml
metrics:
  script:
    - ./collect-metrics.sh > metrics.txt
  artifacts:
    reports:
      metrics: metrics.txt
```

**Format:**

```
memory_usage 245.5
response_time 0.123
error_rate 0.01
```

---

## dotenv Reports

Pass variables between jobs:

```yaml
build:
  script:
    - echo "VERSION=$(cat VERSION)" >> build.env
    - echo "BUILD_DATE=$(date +%Y%m%d)" >> build.env
  artifacts:
    reports:
      dotenv: build.env

deploy:
  script:
    - echo "Deploying version $VERSION built on $BUILD_DATE"
  # Variables from dotenv are automatically available
```

---

## Terraform Reports

```yaml
plan:
  script:
    - terraform plan -out=plan.cache
    - terraform show -json plan.cache > plan.json
  artifacts:
    reports:
      terraform: plan.json
```

Displays Terraform plan changes in MR widget.

---

## All Report Types Summary

```yaml
artifacts:
  reports:
    # Test results
    junit: report.xml

    # Coverage
    coverage_report:
      coverage_format: cobertura
      path: coverage.xml

    # Code quality
    codequality: gl-code-quality-report.json

    # Security scanning
    sast: gl-sast-report.json
    dast: gl-dast-report.json
    dependency_scanning: gl-dependency-scanning-report.json
    container_scanning: gl-container-scanning-report.json
    secret_detection: gl-secret-detection-report.json
    license_scanning: gl-license-scanning-report.json

    # Performance
    browser_performance: performance.json
    load_performance: load.json

    # Accessibility
    accessibility: accessibility.json

    # Metrics
    metrics: metrics.txt

    # Variables
    dotenv: variables.env

    # Terraform
    terraform: plan.json

    # Requirements (for Requirements Management)
    requirements: requirements.json

    # Cyclone DX (SBOM)
    cyclonedx: sbom.json
```

---

## Fail Fast Testing

Stop pipeline early when critical tests fail:

```yaml
stages:
  - test
  - integration

# Critical tests run first
smoke-tests:
  stage: test
  script: ./smoke-tests.sh
  artifacts:
    reports:
      junit: smoke-results.xml

# Full tests only if smoke passes
full-tests:
  stage: integration
  needs: [smoke-tests]
  script: ./full-tests.sh
```

### With RSpec Fail Fast

```yaml
rspec:
  script:
    - bundle exec rspec --fail-fast
  artifacts:
    reports:
      junit: rspec.xml
```

---

## Parallel Testing

### Test Splitting

```yaml
test:
  parallel: 5
  script:
    - ./split-tests.sh --total=$CI_NODE_TOTAL --index=$CI_NODE_INDEX
  artifacts:
    reports:
      junit: results-$CI_NODE_INDEX.xml
```

### With pytest-split

```yaml
test:
  parallel: 4
  script:
    - pytest --splits $CI_NODE_TOTAL --group $CI_NODE_INDEX --junitxml=report-$CI_NODE_INDEX.xml
  artifacts:
    reports:
      junit: report-*.xml
```

### With Jest

```yaml
test:
  parallel: 3
  script:
    - npm test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  artifacts:
    reports:
      junit: junit.xml
```

---

## Test Result Widgets

### Merge Request Widget

Displays:
- Test summary (passed/failed/total)
- Failed test details
- New failures vs existing failures
- Coverage percentage

### Pipeline Test Tab

Shows:
- All test suites
- Test duration
- Test history
- Flaky test detection

---

## Flaky Test Detection

GitLab automatically detects flaky tests:

```yaml
test:
  retry: 2  # Enables flaky detection
  script: pytest
  artifacts:
    reports:
      junit: report.xml
```

Tests that:
- Fail then pass on retry, or
- Have inconsistent results across pipelines

Are marked as "flaky" in the UI.

---

## Test Case Management

Link test results to requirements:

```yaml
test:
  script: ./run-tests.sh
  artifacts:
    reports:
      junit: report.xml
      requirements: requirements.json
```

**Requirements format:**

```json
[
  {
    "requirement_iid": 1,
    "test_report": "Test Case 1 passed"
  }
]
```

---

## Troubleshooting

### JUnit Report Not Showing

```yaml
# Ensure artifact is uploaded
artifacts:
  reports:
    junit: report.xml
  paths:
    - report.xml  # Keep file accessible
```

### Coverage Not Displaying

```yaml
# Check regex matches your output format
coverage: '/Coverage: (\d+\.?\d*)%/'  # Adjust pattern

# Test regex against actual output
script:
  - pytest --cov | tee coverage.log
  - grep -E 'Coverage: \d+\.?\d*%' coverage.log
```

### Report File Not Found

```yaml
# Use when: always to upload on failure
artifacts:
  reports:
    junit: report.xml
  when: always
```

### Large Report Files

```yaml
# Exclude unnecessary data
artifacts:
  reports:
    junit: report.xml
  expire_in: 1 week  # Don't keep forever
```

---

## Best Practices

### Test Organization

1. **Run fast tests first** to fail fast
2. **Use parallel execution** for large test suites
3. **Separate unit and integration tests** into different jobs

### Report Quality

1. **Always upload reports** even on failure (`when: always`)
2. **Set appropriate expiration** to manage storage
3. **Use meaningful test names** for easy identification

### Coverage

1. **Track coverage trends** over time
2. **Set coverage thresholds** in project settings
3. **Review uncovered lines** in MR diffs

### Security

1. **Run security scans** on every MR
2. **Block merges** on critical vulnerabilities
3. **Review dependency updates** for security issues
