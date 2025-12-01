# GitLab CI/CD Runners Reference

> Runner types, configuration, executors, and job scheduling for CI/CD pipeline execution.

---

## Runner Overview

GitLab Runners are lightweight agents that execute CI/CD jobs. They:
- Register with GitLab to receive jobs
- Execute jobs in isolated environments
- Report results back to GitLab

---

## Runner Types

### By Management

| Type | Description | Use Case |
|------|-------------|----------|
| **GitLab-hosted** | Fully managed by GitLab | Zero maintenance, GitLab.com/Dedicated |
| **Self-managed** | User-installed and maintained | Custom requirements, private networks |

### By Scope

| Scope | Availability | Configuration |
|-------|--------------|---------------|
| **Instance runners** | All projects on instance | Admin only |
| **Group runners** | All projects in group | Group owners |
| **Project runners** | Single project only | Project maintainers |

---

## GitLab-Hosted Runners

Available on GitLab.com and GitLab Dedicated with zero configuration.

### Linux Runners

```yaml
job:
  # Uses GitLab-hosted Linux runner
  tags:
    - saas-linux-small-amd64
  script:
    - echo "Running on GitLab-hosted runner"
```

### Available Machine Types (GitLab.com)

| Tag | vCPUs | Memory | Use Case |
|-----|-------|--------|----------|
| `saas-linux-small-amd64` | 2 | 8 GB | Default, light workloads |
| `saas-linux-medium-amd64` | 4 | 16 GB | Build/test jobs |
| `saas-linux-large-amd64` | 8 | 32 GB | Heavy compilation |
| `saas-linux-xlarge-amd64` | 16 | 64 GB | Large builds |
| `saas-linux-2xlarge-amd64` | 32 | 128 GB | Very large builds |

### macOS Runners

```yaml
build-ios:
  tags:
    - saas-macos-medium-m1
  script:
    - xcodebuild -project MyApp.xcodeproj -scheme MyApp
```

### Windows Runners

```yaml
build-windows:
  tags:
    - saas-windows-medium-amd64
  script:
    - echo "Building on Windows"
```

---

## Self-Managed Runners

### Installation

```bash
# Linux (Debian/Ubuntu)
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Linux (RHEL/CentOS)
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | sudo bash
sudo yum install gitlab-runner

# macOS
brew install gitlab-runner

# Docker
docker run -d --name gitlab-runner --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:latest
```

### Registration

```bash
# Interactive registration
gitlab-runner register

# Non-interactive registration
gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --token "$RUNNER_TOKEN" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "docker-runner"
```

---

## Runner Executors

Executors define how jobs run:

### Shell Executor

Runs jobs directly on the runner's host machine.

```toml
# config.toml
[[runners]]
  executor = "shell"
```

**Use cases:** Simple scripts, accessing host resources

### Docker Executor

Runs jobs in Docker containers (most common).

```toml
[[runners]]
  executor = "docker"
  [runners.docker]
    image = "alpine:latest"
    privileged = false
    volumes = ["/cache"]
```

**Use cases:** Isolated builds, consistent environments

### Kubernetes Executor

Runs jobs in Kubernetes pods.

```toml
[[runners]]
  executor = "kubernetes"
  [runners.kubernetes]
    namespace = "gitlab-runner"
    image = "alpine:latest"
```

**Use cases:** Scalable builds, cloud-native environments

### Docker Machine Executor

Auto-scales runners using Docker Machine.

```toml
[[runners]]
  executor = "docker+machine"
  [runners.machine]
    MaxBuilds = 10
    IdleCount = 5
```

**Use cases:** Auto-scaling, cost optimization

### Other Executors

- **VirtualBox**: Runs jobs in VirtualBox VMs
- **Parallels**: Runs jobs in Parallels VMs
- **SSH**: Runs jobs on remote machines via SSH
- **Instance**: Cloud instance per job (AWS, GCP, Azure)

---

## tags Keyword

### Selecting Runners by Tags

```yaml
build:
  tags:
    - docker
    - linux
  script:
    - make build
```

### Multiple Tag Requirements

```yaml
# Job requires ALL specified tags
job:
  tags:
    - docker
    - linux
    - gpu
  # Only runners with ALL three tags can pick this job
```

### Dynamic Tags

```yaml
deploy:
  tags:
    - $DEPLOY_RUNNER  # Variable expansion
  script:
    - deploy.sh
```

### No Tags (Any Runner)

```yaml
job:
  # Without tags, any available runner can pick the job
  script:
    - echo "Running on any runner"
```

---

## Runner Selection Process

GitLab matches jobs to runners based on:

1. **Tags** - Runner must have all required tags
2. **Runner type** - Protected runners for protected branches
3. **Runner status** - Must be online and active
4. **Capacity** - Runner must have available slots
5. **Scope** - Project/group/instance runner availability

### Selection Priority

1. Project runners (most specific)
2. Group runners
3. Instance runners (least specific)

---

## Runner Configuration (config.toml)

### Basic Configuration

```toml
concurrent = 4  # Maximum concurrent jobs
check_interval = 0  # Job check interval (0 = default)

[[runners]]
  name = "docker-runner"
  url = "https://gitlab.com/"
  token = "RUNNER_TOKEN"
  executor = "docker"

  [runners.docker]
    image = "alpine:latest"
    privileged = false
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = ["/cache"]
    shm_size = 0
```

### Docker Executor Options

```toml
[runners.docker]
  image = "ruby:3.0"
  privileged = true  # Required for Docker-in-Docker
  volumes = [
    "/var/run/docker.sock:/var/run/docker.sock",
    "/cache"
  ]
  allowed_images = ["ruby:*", "python:*", "node:*"]
  allowed_services = ["postgres:*", "redis:*"]
  pull_policy = ["if-not-present"]
  memory = "2g"
  cpus = "2"
```

### Cache Configuration

```toml
[runners.cache]
  Type = "s3"
  Shared = true

  [runners.cache.s3]
    ServerAddress = "s3.amazonaws.com"
    BucketName = "runner-cache"
    BucketLocation = "us-east-1"
    AccessKey = "ACCESS_KEY"
    SecretKey = "SECRET_KEY"
```

### Kubernetes Executor Options

```toml
[runners.kubernetes]
  namespace = "gitlab-runner"
  image = "alpine:latest"

  [runners.kubernetes.pod_labels]
    "app" = "gitlab-runner"

  [runners.kubernetes.pod_annotations]
    "prometheus.io/scrape" = "true"

  [[runners.kubernetes.volumes.host_path]]
    name = "docker"
    mount_path = "/var/run/docker.sock"
    host_path = "/var/run/docker.sock"
```

---

## Runner Variables

### Predefined Runner Variables

| Variable | Description |
|----------|-------------|
| `CI_RUNNER_ID` | Runner's unique ID |
| `CI_RUNNER_DESCRIPTION` | Runner's description |
| `CI_RUNNER_TAGS` | Comma-separated runner tags |
| `CI_RUNNER_EXECUTABLE_ARCH` | Runner's architecture |
| `CI_RUNNER_VERSION` | Runner version |
| `CI_RUNNER_REVISION` | Runner revision |
| `CI_RUNNER_SHORT_TOKEN` | First 8 chars of runner token |

### Custom Environment Variables

```toml
[[runners]]
  environment = [
    "DOCKER_DRIVER=overlay2",
    "DOCKER_TLS_CERTDIR=/certs"
  ]
```

---

## Protected Runners

Protected runners only execute jobs on protected branches/tags.

### Configuration

```yaml
# In GitLab UI: Settings > CI/CD > Runners
# Edit runner > Check "Protected"
```

### Behavior

```yaml
# Protected branch job
deploy-production:
  tags:
    - protected-runner  # Only protected runners
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  environment: production
  script:
    - deploy.sh
```

---

## Runner Autoscaling

### Docker Machine Autoscaling

```toml
[[runners]]
  executor = "docker+machine"
  limit = 20

  [runners.machine]
    IdleCount = 2
    IdleTime = 1800
    MaxBuilds = 100
    MachineDriver = "amazonec2"
    MachineName = "runner-%s"

    MachineOptions = [
      "amazonec2-access-key=ACCESS_KEY",
      "amazonec2-secret-key=SECRET_KEY",
      "amazonec2-region=us-east-1",
      "amazonec2-instance-type=t3.medium",
      "amazonec2-vpc-id=vpc-12345"
    ]

    [[runners.machine.autoscaling]]
      Periods = ["* * 9-17 * * mon-fri *"]
      IdleCount = 10
      IdleTime = 600
      Timezone = "America/New_York"

    [[runners.machine.autoscaling]]
      Periods = ["* * * * * sat,sun *"]
      IdleCount = 0
      IdleTime = 60
```

### Kubernetes Autoscaling

Use Kubernetes Horizontal Pod Autoscaler or cluster autoscaler.

---

## Concurrent Job Execution

### Global Concurrency

```toml
# config.toml
concurrent = 10  # Max jobs across all runners
```

### Per-Runner Concurrency

```toml
[[runners]]
  limit = 5  # Max jobs for this runner
```

### Request Concurrency

```toml
[[runners]]
  request_concurrency = 1  # Concurrent job requests
```

---

## Job Timeouts

### Runner-Level Timeout

```toml
[[runners]]
  [runners.custom_build_dir]

  # Maximum job duration (overrides project settings)
  timeout = 7200  # 2 hours in seconds
```

### Job-Level Timeout

```yaml
job:
  timeout: 30 minutes
  script:
    - long-running-task.sh
```

**Hierarchy:** Job timeout ≤ Project timeout ≤ Runner timeout

---

## Troubleshooting

### "This job is stuck because no runners match"

```yaml
# Check job tags match runner tags
job:
  tags:
    - docker  # Ensure runner has this tag
    - linux   # AND this tag
```

**Solutions:**
- Verify runner is online (Admin > Runners)
- Check runner tags include all job tags
- Ensure runner accepts untagged jobs (if no tags)
- Verify protected runner status matches branch protection

### "Runner system failure"

Common causes:
- Docker daemon unavailable
- Out of disk space
- Network connectivity issues

```yaml
# Add retry for transient failures
job:
  retry:
    max: 2
    when:
      - runner_system_failure
```

### "Job timeout"

```yaml
# Increase timeout
job:
  timeout: 2 hours
  script:
    - slow-build.sh
```

### Runner Not Picking Jobs

1. Check runner is online: `gitlab-runner verify`
2. Check runner tags match job requirements
3. Check runner isn't paused
4. Check concurrent job limit not reached
5. Check protected runner/branch settings

### Debug Runner

```bash
# Run in debug mode
gitlab-runner --debug run

# Verify runner
gitlab-runner verify

# Check configuration
gitlab-runner verify --config /etc/gitlab-runner/config.toml
```

---

## Best Practices

### Resource Management

1. **Set appropriate limits** for CPU/memory per job
2. **Use autoscaling** for variable workloads
3. **Monitor runner metrics** for capacity planning

### Security

1. **Use protected runners** for production deployments
2. **Restrict privileged mode** to required jobs only
3. **Limit allowed images** on shared runners
4. **Rotate runner tokens** regularly

### Performance

1. **Use distributed cache** (S3/GCS) for shared runners
2. **Pre-pull common images** on runners
3. **Set appropriate concurrent limits**
4. **Use tags** to route jobs to appropriate runners

### Maintenance

1. **Keep runners updated** to latest version
2. **Monitor disk space** especially for Docker executor
3. **Clean up old containers/images** regularly
4. **Document runner configurations**
