# GitLab CI/CD Secrets and Security Reference

> Secure secrets management, OIDC authentication, and pipeline security best practices.

---

## Secrets Overview

CI/CD jobs often need sensitive information (secrets) to complete work:
- API tokens and keys
- Database credentials
- Private keys and certificates
- Cloud provider credentials

GitLab provides multiple approaches to handle secrets securely.

---

## secrets Keyword

The `secrets` keyword retrieves secrets from external providers and exposes them as CI/CD variables.

### Basic Syntax

```yaml
job:
  secrets:
    DATABASE_PASSWORD:
      vault: production/db/password@secrets
```

### Supported Providers

| Provider | Keyword | GitLab Tier |
|----------|---------|-------------|
| HashiCorp Vault | `vault` | Premium+ |
| Azure Key Vault | `azure_key_vault` | Premium+ |
| GCP Secret Manager | `gcp_secret_manager` | Premium+ |
| AWS Secrets Manager | `aws_secrets_manager` | Premium+ |

---

## HashiCorp Vault Integration

### Configuration

First, configure Vault in GitLab settings (Settings > CI/CD > Secrets).

### Basic Secret Retrieval

```yaml
job:
  secrets:
    DATABASE_PASSWORD:
      vault: secret/data/production/db/password@secrets
      # Format: <path>/<to>/<secret>/<key>@<vault-name>
```

### Multiple Secrets

```yaml
deploy:
  secrets:
    DB_PASSWORD:
      vault: production/database/password@secrets
    API_KEY:
      vault: production/api/key@secrets
    TLS_CERT:
      vault: production/tls/certificate@secrets
  script:
    - deploy.sh
```

### Vault KV v2 Engine

```yaml
job:
  secrets:
    SECRET_VALUE:
      vault:
        engine:
          name: kv-v2
          path: secret
        path: production/credentials
        field: password
```

### Using JWT Authentication

```yaml
job:
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.example.com
  secrets:
    DB_PASS:
      vault:
        path: database/creds/readonly
        field: password
      token: $VAULT_ID_TOKEN
```

---

## Azure Key Vault Integration

### Basic Usage

```yaml
job:
  secrets:
    MY_SECRET:
      azure_key_vault:
        name: my-secret-name
        version: latest  # Optional
```

### Full Configuration

```yaml
deploy:
  id_tokens:
    AZURE_TOKEN:
      aud: api://AzureADTokenExchange
  secrets:
    DATABASE_URL:
      azure_key_vault:
        name: database-connection-string
        version: abc123def456
      token: $AZURE_TOKEN
    API_KEY:
      azure_key_vault:
        name: external-api-key
```

---

## GCP Secret Manager Integration

### Basic Usage

```yaml
job:
  secrets:
    MY_SECRET:
      gcp_secret_manager:
        name: projects/my-project/secrets/my-secret/versions/latest
```

### With Workload Identity

```yaml
deploy:
  id_tokens:
    GCP_TOKEN:
      aud: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
  secrets:
    DB_PASSWORD:
      gcp_secret_manager:
        name: projects/123456/secrets/db-password/versions/latest
      token: $GCP_TOKEN
```

---

## AWS Secrets Manager Integration

### Basic Usage

```yaml
job:
  secrets:
    MY_SECRET:
      aws_secrets_manager:
        name: production/database/password
        version_id: AWSCURRENT  # Optional
        version_stage: AWSCURRENT  # Optional
        region: us-east-1
```

### With OIDC Authentication

```yaml
deploy:
  id_tokens:
    AWS_TOKEN:
      aud: sts.amazonaws.com
  secrets:
    DATABASE_URL:
      aws_secrets_manager:
        name: prod/db/connection-string
        region: us-west-2
      token: $AWS_TOKEN
```

---

## id_tokens - OIDC Authentication

The `id_tokens` keyword generates JSON Web Tokens (JWT) for authenticating with external services using OpenID Connect (OIDC).

### Basic id_token

```yaml
job:
  id_tokens:
    MY_TOKEN:
      aud: https://my-service.example.com
  script:
    - echo "Token available as $MY_TOKEN"
```

### Multiple Tokens

```yaml
deploy:
  id_tokens:
    AWS_TOKEN:
      aud: sts.amazonaws.com
    VAULT_TOKEN:
      aud: https://vault.example.com
    AZURE_TOKEN:
      aud: api://AzureADTokenExchange
```

### Token Claims

GitLab ID tokens include these claims:

| Claim | Description | Example |
|-------|-------------|---------|
| `iss` | Issuer (GitLab URL) | `https://gitlab.com` |
| `sub` | Subject (project path + ref) | `project_path:mygroup/myproject:ref_type:branch:ref:main` |
| `aud` | Audience (configured) | `https://vault.example.com` |
| `exp` | Expiration time | Unix timestamp |
| `iat` | Issued at | Unix timestamp |
| `nbf` | Not before | Unix timestamp |
| `project_id` | GitLab project ID | `12345` |
| `project_path` | Project path | `mygroup/myproject` |
| `pipeline_id` | Pipeline ID | `98765` |
| `job_id` | Job ID | `54321` |
| `ref` | Git reference | `main` |
| `ref_type` | Reference type | `branch` or `tag` |
| `environment` | Environment name | `production` |

---

## Cloud Provider Authentication with OIDC

### AWS with OIDC

```yaml
variables:
  AWS_ROLE_ARN: arn:aws:iam::123456789:role/GitLabRunner

deploy-aws:
  image: amazon/aws-cli:latest
  id_tokens:
    AWS_TOKEN:
      aud: sts.amazonaws.com
  before_script:
    - |
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
        $(aws sts assume-role-with-web-identity \
          --role-arn $AWS_ROLE_ARN \
          --role-session-name "GitLabRunner-${CI_PROJECT_ID}-${CI_PIPELINE_ID}" \
          --web-identity-token $AWS_TOKEN \
          --duration-seconds 3600 \
          --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
          --output text))
  script:
    - aws s3 sync ./dist s3://my-bucket/
```

### GCP with Workload Identity

```yaml
variables:
  GCP_PROJECT_NUMBER: "123456789"
  GCP_WORKLOAD_POOL: "gitlab-pool"
  GCP_PROVIDER: "gitlab-provider"
  GCP_SERVICE_ACCOUNT: "gitlab-sa@my-project.iam.gserviceaccount.com"

deploy-gcp:
  image: google/cloud-sdk:latest
  id_tokens:
    GCP_TOKEN:
      aud: https://iam.googleapis.com/projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GCP_WORKLOAD_POOL}/providers/${GCP_PROVIDER}
  before_script:
    - echo "$GCP_TOKEN" > /tmp/gitlab_token.txt
    - gcloud iam workload-identity-pools create-cred-config
        projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GCP_WORKLOAD_POOL}/providers/${GCP_PROVIDER}
        --service-account=${GCP_SERVICE_ACCOUNT}
        --output-file=/tmp/credentials.json
        --credential-source-file=/tmp/gitlab_token.txt
    - gcloud auth login --cred-file=/tmp/credentials.json
  script:
    - gcloud storage cp ./dist/* gs://my-bucket/
```

### Azure with Federated Credentials

```yaml
variables:
  AZURE_CLIENT_ID: "12345678-1234-1234-1234-123456789abc"
  AZURE_TENANT_ID: "87654321-4321-4321-4321-cba987654321"
  AZURE_SUBSCRIPTION_ID: "abcd1234-abcd-1234-abcd-1234abcd5678"

deploy-azure:
  image: mcr.microsoft.com/azure-cli:latest
  id_tokens:
    AZURE_TOKEN:
      aud: api://AzureADTokenExchange
  before_script:
    - az login --service-principal
        -u $AZURE_CLIENT_ID
        -t $AZURE_TENANT_ID
        --federated-token $AZURE_TOKEN
    - az account set --subscription $AZURE_SUBSCRIPTION_ID
  script:
    - az storage blob upload-batch -d mycontainer -s ./dist
```

---

## Signing with Sigstore/Cosign

### Container Image Signing

```yaml
include:
  - template: Cosign.gitlab-ci.yml

variables:
  COSIGN_YES: "true"

build-and-sign:
  image: docker:24
  services:
    - docker:24-dind
  id_tokens:
    SIGSTORE_ID_TOKEN:
      aud: sigstore
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    # Sign the image digest (not tag)
    - |
      DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA)
      cosign sign $DIGEST
```

### Artifact Signing

```yaml
sign-artifact:
  image: gcr.io/projectsigstore/cosign:latest
  id_tokens:
    SIGSTORE_ID_TOKEN:
      aud: sigstore
  script:
    - cosign sign-blob ./my-binary --bundle cosign.bundle
  artifacts:
    paths:
      - my-binary
      - cosign.bundle
```

---

## CI/CD Variables Security

### Protected Variables

Only available on protected branches/tags:

```yaml
# Configure in GitLab UI: Settings > CI/CD > Variables
# Check "Protect variable"
```

### Masked Variables

Hidden in job logs (must be Base64-compatible, ≥8 chars):

```yaml
# Configure in GitLab UI: Settings > CI/CD > Variables
# Check "Mask variable"
```

### File Variables

```yaml
# Variable content is written to a file
# The variable contains the file path

deploy:
  script:
    - cat $KUBECONFIG  # Contains path to file
    - kubectl --kubeconfig=$KUBECONFIG apply -f manifest.yml
```

### Variable Scope

```yaml
# Group variables: Available to all projects in group
# Project variables: Available only to this project
# Job variables: Available only in specific job

job:
  variables:
    JOB_SPECIFIC: "only here"
```

---

## Pipeline Security Best Practices

### Image Security

```yaml
# Use SHA digests instead of tags
job:
  image: ruby@sha256:abc123def456...

# Or use protected registry
job:
  image: $CI_REGISTRY_IMAGE/ruby:verified
```

### Dependency Pinning

```yaml
# Pin dependencies with lock files
install:
  script:
    - npm ci  # Uses package-lock.json
    - pip install -r requirements.txt --require-hashes
    - bundle install --frozen
```

### Secure File Handling

```yaml
# Use GitLab Secure Files for certificates, keys
deploy:
  script:
    - curl --silent
        --header "PRIVATE-TOKEN: $SECURE_FILES_TOKEN"
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/secure_files/1/download"
        --output signing-key.pem
    - chmod 600 signing-key.pem
```

### Job Token Permissions

```yaml
# Limit CI_JOB_TOKEN scope in Settings > CI/CD > Token Access
# Only allow access to required projects

deploy:
  script:
    # Token can only access explicitly allowed projects
    - git clone https://gitlab-ci-token:$CI_JOB_TOKEN@gitlab.com/allowed/project.git
```

### Protected Environments

```yaml
# Configure in Settings > CI/CD > Protected environments
deploy-production:
  environment:
    name: production
  # Only allowed users/groups can trigger
  # Requires approval if configured
```

---

## Secure CI/CD Patterns

### Never Echo Secrets

```yaml
# BAD - exposes secret in logs
script:
  - echo $DATABASE_PASSWORD

# GOOD - use directly
script:
  - psql "postgresql://user:$DATABASE_PASSWORD@host/db" -c "SELECT 1"
```

### Minimal Variable Scope

```yaml
# Define at job level, not global
deploy:
  variables:
    DEPLOY_KEY: $PRODUCTION_KEY  # Only where needed
  script:
    - deploy.sh
```

### Audit Sensitive Operations

```yaml
deploy-production:
  before_script:
    - echo "Deploy initiated by $GITLAB_USER_LOGIN at $(date)"
    - echo "Pipeline $CI_PIPELINE_URL"
  script:
    - deploy.sh
  after_script:
    - notify-audit-log.sh
```

### Use Separate Credentials Per Environment

```yaml
.deploy-template:
  script:
    - deploy.sh

deploy-staging:
  extends: .deploy-template
  variables:
    DB_PASSWORD: $STAGING_DB_PASSWORD
  environment: staging

deploy-production:
  extends: .deploy-template
  variables:
    DB_PASSWORD: $PRODUCTION_DB_PASSWORD
  environment: production
```

---

## Supply Chain Security

### Include Integrity Verification

```yaml
include:
  - remote: https://example.com/template.yml
    integrity: sha256:abc123def456...
```

### Component Version Pinning

```yaml
include:
  # Pin to exact version
  - component: gitlab.com/components/sast@1.2.3

  # Avoid floating versions in production
  # - component: gitlab.com/components/sast@~latest  # NOT recommended
```

### Verified Components

Look for verified badges in CI/CD Catalog:
- **GitLab-maintained**: Official GitLab components
- **Partner**: Verified partner components
- **Verified creator**: Admin-verified publishers

---

## Troubleshooting

### "Secret not found"

```yaml
# Check secret path format
secrets:
  MY_SECRET:
    # Vault KV v2 paths include 'data'
    vault: secret/data/production/password@secrets  # Correct for KV v2
```

### "Authentication failed"

```yaml
# Verify id_token audience matches provider configuration
id_tokens:
  TOKEN:
    aud: https://exact-url-from-provider.com  # Must match exactly
```

### "Permission denied"

- Check Vault policies allow the GitLab project
- Verify cloud IAM roles trust the GitLab OIDC provider
- Ensure protected variables are used on protected branches

### Token Expiration

```yaml
# ID tokens expire (default: 5 minutes)
# For long jobs, refresh tokens in script
script:
  - ./long-running-task-part-1.sh
  - export NEW_TOKEN=$(get-new-token)  # Refresh if needed
  - ./long-running-task-part-2.sh
```
