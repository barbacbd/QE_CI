# Test Execution Guide - OCP-38471

## Prerequisites

Before running these tests, ensure you have:

1. **OpenShift Installer Binary**
   ```bash
   # Verify openshift-install is available
   which openshift-install
   openshift-install version
   ```

2. **Required Permissions**
   - Write access to the test directory
   - Sufficient disk space for test runs

3. **Test Environment**
   - These tests do NOT require actual cloud credentials
   - Tests are designed to fail at the validation stage (before cloud interaction)
   - Pull secret and SSH key are optional for validation tests

4. **Optional: Python 3.6+ and PyYAML** (for Python test implementation)
   ```bash
   python3 --version
   pip3 install pyyaml
   ```

## Environment Configuration

### Option 1: Using .env File (Recommended)

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
vi .env

# Generate test configs with your settings
./generate-test-configs.sh

# Run tests
./run-tests.sh
```

### Option 2: Export Environment Variables

```bash
# Set release image override
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64

# Optionally disable image policy validation
export OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY=true

# Run tests
./run-tests.sh
```

### Option 3: Inline Variables

```bash
# Run with specific configuration
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64 \
  PLATFORM=gcp \
  ./run-tests.sh
```

## Quick Start

### Automated Test Execution

#### Bash Implementation
Run all test cases using Bash:
```bash
cd /Users/bbarbach/Desktop/QE_CI_Tests/OCP-38471

# Option 1: Run with defaults
./run-tests.sh

# Option 2: Run with specific release
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64 ./run-tests.sh

# Option 3: Run with custom configuration
source .env && ./run-tests.sh
```

#### Python Implementation
Run all test cases using Python:
```bash
cd /Users/bbarbach/Desktop/QE_CI_Tests/OCP-38471

# Option 1: Run with defaults
./test_ocp_38471_proxy_validation.py

# Option 2: Run with environment variables
OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64 \
  KEEP_TEST_DIRS=true \
  ./test_ocp_38471_proxy_validation.py
```

The scripts will:
- Display environment configuration
- Run both test cases (TC1 and TC2)
- Create timestamped test directories
- Capture all output to log files
- Provide a summary of results

### Manual Test Execution

#### Test Case 1: Invalid Proxy Scheme and noProxy with Spaces

```bash
# Create test directory
mkdir -p tc1-test

# Copy test configuration
cp test-configs/tc1-install-config.yaml tc1-test/install-config.yaml

# Run the installer (should fail with validation errors)
openshift-install create manifests --dir tc1-test

# Expected: FATAL error with messages about:
# - httpProxy unsupported value
# - httpsProxy unsupported value (ftp)
# - noProxy spaces
```

#### Test Case 2: Proxy Network Overlap and Invalid noProxy

```bash
# Create test directory
mkdir -p tc2-test

# Copy test configuration
cp test-configs/tc2-install-config.yaml tc2-test/install-config.yaml

# Run the installer (should fail with validation errors)
openshift-install create manifests --dir tc2-test

# Expected: FATAL error with messages about:
# - httpProxy overlaps with service network
# - httpsProxy overlaps with cluster network
# - noProxy invalid domain format
# - noProxy invalid CIDR notation
```

## Verifying Results

### Expected Behavior

For **both test cases**, the command should:
1. **Exit with non-zero status** (failure)
2. **Display FATAL error** message
3. **List all validation failures** in one execution
4. **NOT create manifest files**

### Validation Checklist

#### Test Case 1 (TC1)
- [ ] Error mentions httpProxy missing scheme
- [ ] Error mentions httpsProxy invalid scheme (ftp)
- [ ] Error mentions noProxy contains spaces
- [ ] No manifests directory created
- [ ] Exit code is non-zero

#### Test Case 2 (TC2)
- [ ] Error mentions httpProxy overlaps with service network (172.30.0.0/16)
- [ ] Error mentions httpsProxy overlaps with cluster network (10.128.0.0/14)
- [ ] Error mentions noProxy element 0 invalid (ABC.com)
- [ ] Error mentions noProxy element 1 invalid (10.0.2.1/280)
- [ ] No manifests directory created
- [ ] Exit code is non-zero

## Troubleshooting

### Test Passes When It Should Fail

**Problem:** The installer accepts invalid configuration

**Possible Causes:**
- Older version of openshift-install that doesn't have these validations
- Test configuration was modified incorrectly

**Solution:**
```bash
# Check installer version
openshift-install version

# Verify test config hasn't been modified
diff test-configs/tc1-install-config.yaml <original-config>
```

### Test Fails with Different Error

**Problem:** Getting different error messages than expected

**Possible Causes:**
- Different OpenShift version with different error message formats
- Additional validation rules added in newer versions

**Action:**
- Document the actual error message
- Verify all expected validation points are still covered
- Update expected results if behavior is improved but functionally equivalent

### Cannot Find openshift-install

**Problem:** `command not found: openshift-install`

**Solution:**
```bash
# Add to PATH or use full path
export PATH=$PATH:/path/to/openshift-install

# Or use absolute path in test
/full/path/to/openshift-install create manifests --dir tc1-test
```

## Test Results Location

After running `run-tests.sh`, results are stored in:
```
test-runs/
├── TC1-<timestamp>/
│   ├── install-config.yaml
│   ├── output.log
│   └── result.txt
└── TC2-<timestamp>/
    ├── install-config.yaml
    ├── output.log
    └── result.txt
```

### Analyzing Results

```bash
# View TC1 output
cat test-runs/TC1-*/output.log

# View TC2 output
cat test-runs/TC2-*/output.log

# Check result status
cat test-runs/TC1-*/result.txt
cat test-runs/TC2-*/result.txt
```

## Cleanup

```bash
# Remove all test run directories
rm -rf test-runs/

# Remove individual test directories (if run manually)
rm -rf tc1-test tc2-test
```

## Reporting Results

When reporting test results to Polarion (OCP-38471), include:

1. **Test Case ID** (TC1 or TC2)
2. **Pass/Fail Status**
3. **OpenShift Installer Version**
   ```bash
   openshift-install version
   ```
4. **Actual Error Output** (from output.log)
5. **Any Deviations** from expected results
6. **Environment Details**
   - OS version
   - Test execution date
   - Any modifications made to test configs

## Example Test Report

```
Test Case: OCP-38471-TC1
Status: PASS
Date: 2026-04-23
Installer Version: openshift-install 4.15.0

Expected Results: ✓ All validation errors detected
- httpProxy scheme validation: ✓
- httpsProxy scheme validation: ✓  
- noProxy space validation: ✓
- No manifests created: ✓

Actual Output:
[paste actual error output here]

Notes: All validations working as expected. Error messages are clear and actionable.
```

## Advanced Testing

### Testing with Different Network CIDRs

Modify `tc2-install-config.yaml` to test different network overlaps:

```yaml
# Test different cluster network
networking:
  clusterNetwork:
  - cidr: 192.168.0.0/16  # Change this
    
# Update proxy to overlap
proxy:
  httpsProxy: http://user:password@192.168.1.25:3128  # Match new CIDR
```

### Testing Edge Cases

1. **Proxy at network boundary:**
   ```yaml
   proxy:
     httpProxy: http://user:password@172.30.0.1:3128  # First IP in service network
   ```

2. **Valid CIDR edge case:**
   ```yaml
   proxy:
     noProxy: 10.0.2.1/32  # /32 is valid for IPv4
   ```

3. **Multiple spaces in noProxy:**
   ```yaml
   proxy:
     noProxy: example.com,  localhost,  127.0.0.1  # Multiple spaces
   ```

## Support

For issues with:
- **Test cases**: Review test case documentation in TC1/TC2 .md files
- **OpenShift installer**: Consult OpenShift documentation
- **Polarion work item**: OCP-38471

## References

- [TC1 Documentation](OCP-38471-TC1-invalid-proxy-scheme-and-noproxy-spaces.md)
- [TC2 Documentation](OCP-38471-TC2-proxy-network-overlap-and-invalid-noproxy.md)
- [Project README](README.md)
