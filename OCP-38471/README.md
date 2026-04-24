# OCP-38471 Test Cases

## Overview
This directory contains test cases for validating OpenShift installer proxy configuration validation (Polarion work item OCP-38471).

## Features
- ✓ Bash and Python test implementations
- ✓ Environment variable configuration
- ✓ Release image override support
- ✓ Multiple platform support (AWS, GCP, Azure)
- ✓ Automated test execution
- ✓ Dynamic configuration generation

## Test Cases

### [TC1: Invalid Proxy Scheme and noProxy with Spaces](OCP-38471-TC1-invalid-proxy-scheme-and-noproxy-spaces.md)
Tests validation of:
- httpProxy without proper scheme
- httpsProxy with invalid scheme (ftp)
- noProxy values containing spaces

### [TC2: Proxy Network Overlap and Invalid noProxy Values](OCP-38471-TC2-proxy-network-overlap-and-invalid-noproxy.md)
Tests validation of:
- Proxy servers overlapping with service network
- Proxy servers overlapping with cluster network
- Invalid noProxy domain format
- Invalid noProxy CIDR notation

## Quick Start

### 1. Configure Environment (Optional)
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
vi .env
```

### 2. Generate Test Configurations
```bash
# Generate install-config.yaml files with your environment settings
./generate-test-configs.sh
```

### 3. Run Tests
```bash
# Bash implementation
./run-tests.sh

# Python implementation
./test_ocp_38471_proxy_validation.py
```

## Environment Configuration

The test suite supports configuration via environment variables or a `.env` file.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE` | Override OpenShift release image | (none) |
| `OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY` | Disable image policy validation | `false` |
| `OPENSHIFT_INSTALL` | Path to openshift-install binary | `openshift-install` |
| `PULL_SECRET_FILE` | Path to pull secret | `$HOME/secrets/pull-secrets.txt` |
| `SSH_KEY` | Path to SSH public key | `$HOME/.ssh/github_ed25519.pub` |
| `BASE_DOMAIN` | Cluster base domain | `installer.gcp.devcluster.openshift.com` |
| `CLUSTER_NAME` | Cluster name | `bbarbach-ocp-38471` |
| `PLATFORM` | Platform (aws, gcp, azure) | `gcp` |
| `GCP_PROJECT_ID` | GCP project ID | `openshift-dev-installer` |
| `GCP_REGION` | GCP region | `us-west1` |
| `WORK_DIR` | Test working directory | `/tmp/ocp-38471-test` |

See [`.env.example`](.env.example) for complete list.

### Example: Testing Specific Release

```bash
# Test against OpenShift 4.15
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
./run-tests.sh
```

## Quick Reference

### Common Commands
```bash
# Create manifests
openshift-install create manifests --dir <installation_dir>

# Clean up test directory
rm -rf <installation_dir>
```

### Sample install-config.yaml Template (GCP)
```yaml
apiVersion: v1
baseDomain: installer.gcp.devcluster.openshift.com
metadata:
  name: bbarbach-ocp-38471
proxy:
  httpProxy: http://user:password@proxy.example.com:3128
  httpsProxy: https://user:password@proxy.example.com:3128
  noProxy: installer.gcp.devcluster.openshift.com,localhost,127.0.0.1
networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OVNKubernetes
  serviceNetwork:
  - 172.30.0.0/16
platform:
  gcp:
    projectID: openshift-dev-installer
    region: us-west1
pullSecret: '<your-pull-secret>'
sshKey: '<your-ssh-key>'
```

## Validation Rules Summary

### httpProxy / httpsProxy
- **Must have** valid scheme: `http://` or `https://`
- **Must not** overlap with cluster network CIDR
- **Must not** overlap with service network CIDR
- **Must not** overlap with machine network CIDR

### noProxy
- **Must not** contain spaces
- **Must** use lowercase for domains
- **Must** have valid CIDR notation (for IP ranges)
- **Must not** contain wildcard characters
- Valid CIDR masks: /0 to /32 for IPv4, /0 to /128 for IPv6

## Expected Behavior
The OpenShift installer should:
1. Validate all proxy settings before creating manifests
2. Report all validation errors in a single execution
3. Provide clear, actionable error messages
4. Prevent manifest creation when validation fails
5. Exit with a FATAL error status

## Test Execution Tips
1. Always start with a clean installation directory
2. Keep a backup of working install-config.yaml files
3. Test one scenario at a time for clarity
4. Document actual vs expected results
5. Check installer version compatibility

## Related Documentation
- OpenShift Documentation: [Configuring a cluster-wide proxy](https://docs.openshift.com/container-platform/latest/installing/installing_bare_metal/installing-bare-metal-network-customizations.html#installation-configure-proxy_installing-bare-metal-network-customizations)
- Polarion Work Item: OCP-38471
