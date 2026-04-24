# OCP-35198: GCP Custom Machine Type Tests

## Overview

This test suite validates OpenShift installation with GCP custom machine types, covering both valid and invalid configurations.

## References

- Primary Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1878108
- Regression (4.7): https://bugzilla.redhat.com/show_bug.cgi?id=1898194
- Additional Fix: https://bugzilla.redhat.com/show_bug.cgi?id=1898713

## Test Coverage

### Valid Machine Types (Expected to Pass)
- `n1-standard-4` - Standard GCP machine type
- `custom-4-16384` - Custom type with 4 vCPUs and 16GB RAM
- `n1-custom-4-16384` - N1 custom type with 4 vCPUs and 16GB RAM

### Invalid Machine Types - 404 Not Found
These machine types don't exist in GCP and should return 404 errors:
- `n1-dne-4`
- `custom-2`
- `custom-a`
- `custom-2-b`
- `n1-custom-2`
- `n1-custom-a`
- `n1-custom-2-b`

**Expected Error:**
```
controlPlane.platform.gcp.type: Internal error: googleapi: Error 404: The resource 'projects/myproject/zones/us-west1-b/machineTypes/custom-2' was not found, notFound
```

### Invalid Machine Types - 400 Invalid Resource Usage
These machine types violate GCP's resource constraints:

#### Memory Not Multiple of 256MiB
- `custom-4-16383`
- `n1-custom-4-16383`

**Expected Error:**
```
controlPlane.platform.gcp.type: Internal error: googleapi: Error 400: Invalid resource usage: 'Memory should be a multiple of 256MiB, while 16383MiB is requested'., invalidResourceUsage
```

#### vCPUs Not Multiple of 2
- `custom-3-16384`
- `n1-custom-3-16384`

**Expected Error:**
```
controlPlane.platform.gcp.type: Internal error: googleapi: Error 400: Invalid resource usage: 'Number of vCPUs should be multiple of 2 if greater than 2, while 3 is requested'., invalidResourceUsage
```

### Below Minimum Requirements
These machine types don't meet OpenShift's minimum resource requirements:
- `n1-standard-2` - Only 2 vCPUs (requires 4)
- `custom-2-7680` - Only 2 vCPUs and 7.5GB RAM
- `n1-custom-2-7680` - Only 2 vCPUs and 7.5GB RAM

**Expected Errors:**
```
controlPlane.platform.gcp.type: Invalid value: "custom-2-7680": instance type does not meet minimum resource requirements of 4 vCPUs
controlPlane.platform.gcp.type: Invalid value: "custom-2-7680": instance type does not meet minimum resource requirements of 15360 MB Memory
```

## Prerequisites

### Required Software
- `openshift-install` binary (must be in PATH or specify with `--openshift-install`)
- Python 3.6+ (for Python script)
- Bash 4.0+ (for shell script)

### Required Configuration
1. **GCP Project ID** - Set via environment variable or command line
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   ```

2. **Pull Secret** - OpenShift pull secret
   - Default location: `~/.openshift/pull-secret.json`
   - Or specify with `--pull-secret`
   - Download from: https://console.redhat.com/openshift/install/pull-secret

3. **SSH Key** (optional but recommended)
   - Default location: `~/.ssh/id_rsa.pub`
   - Or specify with `--ssh-key`

## Usage

### Python Script (Recommended)

#### Basic Usage
```bash
python3 test_ocp_35198_gcp_custom_types.py --project-id YOUR_PROJECT_ID
```

#### With All Options
```bash
python3 test_ocp_35198_gcp_custom_types.py \
  --project-id myproject \
  --region us-west1 \
  --zone us-west1-b \
  --base-domain example.com \
  --cluster-name test-cluster \
  --openshift-install /path/to/openshift-install \
  --pull-secret ~/.openshift/pull-secret.json \
  --ssh-key ~/.ssh/id_rsa.pub \
  --export-json results.json \
  --no-cleanup
```

#### Options
- `--work-dir` - Working directory for test files (default: `/tmp/ocp-35198-test`)
- `--project-id` - GCP project ID (required, or set `GCP_PROJECT_ID` env var)
- `--region` - GCP region (default: `us-west1`)
- `--zone` - GCP zone (default: `us-west1-b`)
- `--base-domain` - Base domain for cluster (default: `example.com`)
- `--cluster-name` - Cluster name (default: `test-cluster`)
- `--openshift-install` - Path to openshift-install binary (default: `openshift-install`)
- `--pull-secret` - Path to pull secret file (default: `~/.openshift/pull-secret.json`)
- `--ssh-key` - Path to SSH public key (default: `~/.ssh/id_rsa.pub`)
- `--export-json` - Export results to JSON file
- `--no-cleanup` - Keep test directories for debugging

### Bash Script

#### Basic Usage
```bash
export GCP_PROJECT_ID="your-project-id"
./test_ocp_35198_gcp_custom_types.sh
```

#### With Custom Configuration
```bash
export GCP_PROJECT_ID="myproject"
export GCP_REGION="us-west1"
export GCP_ZONE="us-west1-b"
export BASE_DOMAIN="example.com"
export CLUSTER_NAME="test-cluster"
export OPENSHIFT_INSTALL="/path/to/openshift-install"
export PULL_SECRET_FILE="~/.openshift/pull-secret.json"
export SSH_KEY="~/.ssh/id_rsa.pub"

./test_ocp_35198_gcp_custom_types.sh
```

## Output

### Console Output
Both scripts provide color-coded output:
- **BLUE** - Informational messages
- **GREEN** - Passed tests
- **RED** - Failed tests
- **YELLOW** - Warnings

### JSON Export (Python Only)
When using `--export-json`, the Python script generates a JSON file with detailed results:

```json
{
  "test_case": "OCP-35198",
  "description": "GCP Custom Machine Type Tests",
  "total_tests": 17,
  "passed": 17,
  "failed": 0,
  "results": [
    {
      "test_name": "Machine type: n1-standard-4",
      "machine_type": "n1-standard-4",
      "result": "PASS",
      "expected": "pass",
      "actual": "passed",
      "error_message": null
    }
  ]
}
```

## Exit Codes

- **0** - All tests passed
- **1** - One or more tests failed or setup error

## Debugging

### Keep Test Artifacts
To preserve test directories for inspection:

**Python:**
```bash
python3 test_ocp_35198_gcp_custom_types.py --project-id myproject --no-cleanup
```

**Bash:**
Comment out the `trap cleanup EXIT` line in the script.

### Test Artifacts Location
- Default: `/tmp/ocp-35198-test/`
- Each machine type gets its own subdirectory
- Contains:
  - `install-config.yaml` - Generated install configuration
  - `validation_output.txt` - Output from openshift-install validation

### Manual Testing
To manually test a specific machine type:

```bash
# Create test directory
mkdir -p /tmp/manual-test

# Create install-config.yaml with your machine type
cat > /tmp/manual-test/install-config.yaml <<EOF
apiVersion: v1
baseDomain: example.com
controlPlane:
  platform:
    gcp:
      type: n1-standard-4
# ... rest of config
EOF

# Run validation
openshift-install create manifests --dir=/tmp/manual-test
```

## CI/CD Integration

### Jenkins Pipeline Example
```groovy
stage('OCP-35198 Tests') {
    steps {
        sh '''
            python3 test_ocp_35198_gcp_custom_types.py \
                --project-id ${GCP_PROJECT_ID} \
                --export-json test-results.json
        '''
        archiveArtifacts artifacts: 'test-results.json'
        junit 'test-results.json'  // Convert to JUnit format if needed
    }
}
```

### GitHub Actions Example
```yaml
- name: Run OCP-35198 Tests
  env:
    GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  run: |
    python3 test_ocp_35198_gcp_custom_types.py \
      --project-id $GCP_PROJECT_ID \
      --export-json results.json
    
- name: Upload Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: results.json
```

## Notes

- Tests use `openshift-install create manifests` for validation without actually creating a cluster
- No actual GCP resources are created during testing
- Tests only validate the install-config.yaml and check for appropriate error messages
- The actual installation is not performed to save time and resources

## Troubleshooting

### "openshift-install not found"
Ensure the `openshift-install` binary is in your PATH or specify the full path with `--openshift-install`.

### "No access token" or API errors
The scripts don't actually call GCP APIs directly - they rely on `openshift-install` to validate the configuration. Ensure your GCP credentials are configured if you want full validation.

### "Pull secret not found"
Download your pull secret from https://console.redhat.com/openshift/install/pull-secret and save it to `~/.openshift/pull-secret.json`.

### Tests pass when they should fail
Some validations require actual GCP API access. If running in a restricted environment, some error validations may not trigger.

## License

Red Hat Internal Testing - Follow your organization's policies for test code.
