# Environment Configuration Examples

This document provides examples for common test scenarios using environment variables.

## Example 1: Testing Specific OpenShift Release

Test against OpenShift 4.15.0:

```bash
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
./run-tests.sh
```

## Example 2: Testing with Development Build

Test with a nightly or CI build:

```bash
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=registry.ci.openshift.org/ocp/release:4.16.0-0.nightly-2024-03-15-123456
export OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY=true
./run-tests.sh
```

## Example 3: AWS Platform Configuration

Create `.env` file for AWS testing:

```bash
cat > .env <<'EOF'
# Platform
PLATFORM=aws
AWS_REGION=us-west-2

# Credentials
PULL_SECRET_FILE=/home/user/pull-secret.txt
SSH_KEY=/home/user/.ssh/openshift.pub

# Cluster Config
BASE_DOMAIN=aws.example.com
CLUSTER_NAME=ocp-proxy-test

# Release
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
EOF

./generate-test-configs.sh
./run-tests.sh
```

## Example 4: GCP Platform Configuration

Create `.env` file for GCP testing:

```bash
cat > .env <<'EOF'
# Platform
PLATFORM=gcp
GCP_PROJECT_ID=openshift-dev-12345
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# Credentials
PULL_SECRET_FILE=/home/user/pull-secret.txt
SSH_KEY=/home/user/.ssh/openshift.pub

# Cluster Config
BASE_DOMAIN=gcp.example.com
CLUSTER_NAME=ocp-proxy-test

# Release
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
EOF

./generate-test-configs.sh
./run-tests.sh
```

## Example 5: Azure Platform Configuration

Create `.env` file for Azure testing:

```bash
cat > .env <<'EOF'
# Platform
PLATFORM=azure
AZURE_REGION=eastus
AZURE_BASE_DOMAIN_RESOURCE_GROUP_NAME=os4-common

# Credentials
PULL_SECRET_FILE=/home/user/pull-secret.txt
SSH_KEY=/home/user/.ssh/openshift.pub

# Cluster Config
BASE_DOMAIN=azure.example.com
CLUSTER_NAME=ocp-proxy-test

# Release
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
EOF

./generate-test-configs.sh
./run-tests.sh
```

## Example 6: Custom Network Configuration

Test with custom network CIDRs:

```bash
cat > .env <<'EOF'
# Custom Network Settings
CLUSTER_NETWORK_CIDR=192.168.0.0/16
CLUSTER_NETWORK_HOST_PREFIX=24
MACHINE_NETWORK_CIDR=10.10.0.0/16
SERVICE_NETWORK_CIDR=172.20.0.0/16
NETWORK_TYPE=OVNKubernetes

# Other settings
BASE_DOMAIN=example.com
CLUSTER_NAME=custom-network-test
PLATFORM=aws
AWS_REGION=us-east-1
EOF

./generate-test-configs.sh
./run-tests.sh
```

## Example 7: Testing Multiple Releases

Test against multiple OpenShift versions:

```bash
#!/bin/bash

RELEASES=(
    "4.13.0-x86_64"
    "4.14.0-x86_64"
    "4.15.0-x86_64"
    "4.16.0-rc.1-x86_64"
)

for release in "${RELEASES[@]}"; do
    echo "Testing release: $release"
    export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE="quay.io/openshift-release-dev/ocp-release:${release}"
    ./run-tests.sh
    echo "---"
done
```

## Example 8: CI/CD Pipeline Integration

Example GitLab CI configuration:

```yaml
test-ocp-38471:
  stage: test
  script:
    - export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=${OCP_RELEASE_IMAGE}
    - export WORK_DIR=/tmp/ci-test-${CI_JOB_ID}
    - cd /path/to/OCP-38471
    - ./run-tests.sh
  artifacts:
    when: always
    paths:
      - test-runs/*/output.log
      - test-runs/*/result.txt
  variables:
    OCP_RELEASE_IMAGE: "quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64"
```

Example Jenkins Pipeline:

```groovy
pipeline {
    agent any
    
    environment {
        OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE = "quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64"
        WORK_DIR = "/tmp/jenkins-${BUILD_ID}"
        PLATFORM = "aws"
        AWS_REGION = "us-east-1"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'cd OCP-38471 && ./generate-test-configs.sh'
            }
        }
        
        stage('Test') {
            steps {
                sh 'cd OCP-38471 && ./run-tests.sh'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'test-runs/*/output.log, test-runs/*/result.txt', allowEmptyArchive: true
        }
    }
}
```

## Example 9: Keep Test Directories for Debugging

Preserve test directories for troubleshooting:

```bash
export KEEP_TEST_DIRS=true
export VERBOSE=true
./test_ocp_38471_proxy_validation.py

# Inspect results
ls -la test-runs/
cat test-runs/TC1-*/output.log
```

## Example 10: Using Python Tests with Custom Config

```bash
# Set environment
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
export WORK_DIR=/tmp/my-proxy-tests
export PLATFORM=gcp
export GCP_PROJECT_ID=my-gcp-project
export GCP_REGION=us-west1
export KEEP_TEST_DIRS=true

# Run Python tests
./test_ocp_38471_proxy_validation.py

# Check results
ls -la /tmp/my-proxy-tests/
```

## Environment Variable Reference

### OpenShift Installer Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE` | Override default release image | `quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64` |
| `OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY` | Disable image policy checks | `true` or `false` |
| `OPENSHIFT_INSTALL` | Path to installer binary | `/usr/local/bin/openshift-install` |

### Test Configuration Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `WORK_DIR` | Test execution directory | `/tmp/ocp-38471-test` |
| `PLATFORM` | Cloud platform | `aws` |
| `BASE_DOMAIN` | Cluster base domain | `example.com` |
| `CLUSTER_NAME` | Cluster name | `test-cluster` |
| `KEEP_TEST_DIRS` | Keep test dirs after run | `false` |
| `VERBOSE` | Verbose output | `false` |

### Platform-Specific Variables

#### AWS
- `AWS_REGION` - AWS region (default: `us-east-1`)

#### GCP
- `GCP_PROJECT_ID` - GCP project ID
- `GCP_REGION` - GCP region (default: `us-west1`)
- `GCP_ZONE` - GCP zone (default: `us-west1-b`)

#### Azure
- `AZURE_REGION` - Azure region (default: `eastus`)
- `AZURE_BASE_DOMAIN_RESOURCE_GROUP_NAME` - Resource group (default: `os4-common`)

### Network Configuration Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLUSTER_NETWORK_CIDR` | Cluster network CIDR | `10.128.0.0/14` |
| `CLUSTER_NETWORK_HOST_PREFIX` | Host prefix | `23` |
| `MACHINE_NETWORK_CIDR` | Machine network CIDR | `10.0.0.0/16` |
| `SERVICE_NETWORK_CIDR` | Service network CIDR | `172.30.0.0/16` |
| `NETWORK_TYPE` | Network plugin | `OVNKubernetes` |

## Tips

1. **Always regenerate configs** after changing environment variables:
   ```bash
   ./generate-test-configs.sh
   ```

2. **Test your environment** before running full test suite:
   ```bash
   openshift-install version
   echo $OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE
   ```

3. **Use `.env` files** for persistent configurations, environment variables for one-off tests

4. **Keep test directories** when debugging:
   ```bash
   export KEEP_TEST_DIRS=true
   ```

5. **Check logs** for detailed error information:
   ```bash
   tail -f test-runs/TC1-*/output.log
   ```
