# GCP-Specific Setup for OCP-38471

This test suite is configured for **Google Cloud Platform (GCP)** by default.

## Default Configuration

| Setting | Value |
|---------|-------|
| Platform | `gcp` |
| GCP Project | `openshift-dev-installer` |
| GCP Region | `us-west1` |
| Base Domain | `installer.gcp.devcluster.openshift.com` |
| Cluster Name | `bbarbach-ocp-38471` |
| Network Type | `OVNKubernetes` |
| SSH Key | `$HOME/.ssh/github_ed25519.pub` |

## Quick Start (GCP)

### 1. Prerequisites

```bash
# Ensure you have GCP credentials configured
gcloud auth list

# Verify you have access to the project
gcloud config set project openshift-dev-installer

# Ensure openshift-install is available
which openshift-install
openshift-install version
```

### 2. Run Tests

```bash
# Run with defaults (GCP)
./run-tests.sh

# Or with Python
./test_ocp_38471_proxy_validation.py
```

### 3. Test Specific OpenShift Release on GCP

```bash
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
./run-tests.sh
```

## GCP Project Requirements

The test suite requires:
- ✓ Valid GCP project ID (`openshift-dev-installer` by default)
- ✓ Appropriate IAM permissions for OpenShift installation
- ✓ API access enabled (Compute Engine, IAM, etc.)

**Note:** These validation tests do NOT actually provision GCP resources. They only validate the install-config.yaml before any cloud API calls are made.

## Changing GCP Settings

### Option 1: Edit .env File

```bash
cp .env.example .env
vi .env

# Modify:
GCP_PROJECT_ID=my-custom-project
GCP_REGION=us-central1
BASE_DOMAIN=my-domain.gcp.example.com
CLUSTER_NAME=my-test-cluster
```

### Option 2: Environment Variables

```bash
export GCP_PROJECT_ID=my-custom-project
export GCP_REGION=us-central1
./generate-test-configs.sh
./run-tests.sh
```

## Testing on Different Platforms

### Switch to AWS

```bash
export PLATFORM=aws
export AWS_REGION=us-east-1
export BASE_DOMAIN=aws.example.com
./generate-test-configs.sh
./run-tests.sh
```

### Switch to Azure

```bash
export PLATFORM=azure
export AZURE_REGION=eastus
export BASE_DOMAIN=azure.example.com
./generate-test-configs.sh
./run-tests.sh
```

## GCP Network Configuration

The test uses these network CIDRs by default:

| Network | CIDR | Purpose |
|---------|------|---------|
| Cluster Network | `10.128.0.0/14` | Pod networking |
| Machine Network | `10.0.0.0/16` | Node networking |
| Service Network | `172.30.0.0/16` | Service networking |

These defaults work for GCP and align with OpenShift best practices.

## GCP-Specific Test Cases

### TC1: Invalid Proxy Schemes (GCP)
Tests that proxy validation works regardless of platform:
- Missing proxy scheme → Error
- Invalid proxy scheme (ftp) → Error
- noProxy with spaces → Error

### TC2: Network Overlap (GCP)
Tests that network overlap detection works on GCP:
- Proxy in service network (172.30.0.0/16) → Error
- Proxy in cluster network (10.128.0.0/14) → Error
- Invalid noProxy values → Error

## Troubleshooting GCP Issues

### Issue: GCP authentication errors

```bash
# Re-authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project openshift-dev-installer
```

### Issue: Different GCP project needed

```bash
# Update configuration
export GCP_PROJECT_ID=my-other-project
./generate-test-configs.sh
./run-tests.sh
```

### Issue: Want to use different region

```bash
# Change region
export GCP_REGION=europe-west1
./generate-test-configs.sh
./run-tests.sh
```

## Expected Behavior

Both test cases should **FAIL** with validation errors (before any GCP API calls):

**TC1 Expected:**
```
FATAL failed to fetch Master Machines: failed to load asset "Install Config":
 invalid "install-config.yaml" file: 
[proxy.httpProxy: Unsupported value: "user": supported values: "http",
 proxy.httpsProxy: Unsupported value: "ftp": supported values: "http", "https",
 proxy.noProxy: Invalid value: noProxy must not have spaces]
```

**TC2 Expected:**
```
level=fatal msg=failed to fetch Master Machines: failed to load asset "Install Config": 
invalid "install-config.yaml" file: [
proxy.httpProxy: Invalid value: proxy value is part of the service networks, 
proxy.httpsProxy: Invalid value: proxy value is part of the cluster networks, 
proxy.noProxy: Invalid value: each element of noProxy must be a CIDR or domain...]
```

## CI/CD Integration for GCP

### Example: GitLab CI

```yaml
test-ocp-38471-gcp:
  stage: test
  script:
    - gcloud auth activate-service-account --key-file=${GCP_SERVICE_ACCOUNT_KEY}
    - export GCP_PROJECT_ID=${GCP_PROJECT_ID}
    - export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=${OCP_RELEASE}
    - cd OCP-38471
    - ./run-tests.sh
  variables:
    PLATFORM: gcp
    GCP_REGION: us-west1
```

## Resources

- [OpenShift on GCP Documentation](https://docs.openshift.com/container-platform/latest/installing/installing_gcp/preparing-to-install-on-gcp.html)
- [GCP Project Setup](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [OpenShift GCP Requirements](https://docs.openshift.com/container-platform/latest/installing/installing_gcp/installing-gcp-account.html)
