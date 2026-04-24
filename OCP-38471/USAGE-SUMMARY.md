# OCP-38471 Usage Summary

## Quick Start (3 Steps)

### 1. Configure (Optional)
```bash
cp .env.example .env
# Edit .env with your settings (or skip for defaults)
```

### 2. Generate Configs
```bash
./generate-test-configs.sh
```

### 3. Run Tests
```bash
# Bash implementation
./run-tests.sh

# OR Python implementation
./test_ocp_38471_proxy_validation.py
```

## Common Use Cases

### Test Specific OpenShift Release
```bash
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=quay.io/openshift-release-dev/ocp-release:4.15.0-x86_64
./run-tests.sh
```

### Test with Development/Nightly Build
```bash
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=registry.ci.openshift.org/ocp/release:4.16.0-0.nightly-2024-03-15-123456
export OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY=true
./run-tests.sh
```

### Test Different Platform (AWS)
```bash
export PLATFORM=aws
export AWS_REGION=us-east-1
./generate-test-configs.sh
./run-tests.sh
```

### Keep Test Output for Debugging
```bash
export KEEP_TEST_DIRS=true
./test_ocp_38471_proxy_validation.py
ls -la test-runs/
```

## File Overview

| File | Purpose |
|------|---------|
| `.env.example` | Environment variable template |
| `run-tests.sh` | Bash test runner (automated) |
| `test_ocp_38471_proxy_validation.py` | Python test runner (automated) |
| `generate-test-configs.sh` | Generate configs from env vars |
| `OCP-38471-TC1-*.md` | Test Case 1 documentation |
| `OCP-38471-TC2-*.md` | Test Case 2 documentation |
| `README.md` | Project overview |
| `TEST-EXECUTION-GUIDE.md` | Detailed execution guide |
| `ENVIRONMENT-EXAMPLES.md` | Environment configuration examples |
| `test-configs/tc1-install-config.yaml` | TC1 test configuration |
| `test-configs/tc2-install-config.yaml` | TC2 test configuration |
| `test-configs/valid-install-config.yaml` | Valid config (negative test) |

## Key Features

✓ **Environment Variable Support** - Configure via `.env` or export  
✓ **Release Image Override** - Test any OpenShift version  
✓ **Multi-Platform** - AWS, GCP, Azure support  
✓ **Dual Implementation** - Bash and Python versions  
✓ **Auto-Generated Configs** - Dynamic config generation  
✓ **Detailed Logging** - Captures all output for analysis  
✓ **CI/CD Ready** - Easy integration with pipelines  

## Expected Results

Both test cases (TC1 and TC2) should **FAIL** with validation errors:

**TC1 Validates:**
- httpProxy without scheme → Error
- httpsProxy with invalid scheme (ftp) → Error
- noProxy with spaces → Error

**TC2 Validates:**
- httpProxy overlaps service network → Error
- httpsProxy overlaps cluster network → Error
- noProxy invalid domain format → Error
- noProxy invalid CIDR (/280) → Error

## Troubleshooting

### Tests Pass (Should Fail)
```bash
# Check installer version
openshift-install version

# Verify test configs haven't been modified
diff test-configs/tc1-install-config.yaml <expected>
```

### Missing openshift-install
```bash
# Set path to installer
export OPENSHIFT_INSTALL=/path/to/openshift-install
./run-tests.sh
```

### Different Error Messages
- Document actual errors
- Compare with expected results in test case docs
- May indicate different OpenShift version behavior

## Documentation

- **Quick Reference**: See `README.md`
- **Detailed Guide**: See `TEST-EXECUTION-GUIDE.md`
- **Environment Examples**: See `ENVIRONMENT-EXAMPLES.md`
- **Test Case 1**: See `OCP-38471-TC1-invalid-proxy-scheme-and-noproxy-spaces.md`
- **Test Case 2**: See `OCP-38471-TC2-proxy-network-overlap-and-invalid-noproxy.md`

## Support

- Polarion Work Item: OCP-38471
- GitHub Issues: Report test suite issues to QE team
- OpenShift Docs: [Configuring cluster-wide proxy](https://docs.openshift.com/container-platform/latest/installing/installing_bare_metal/installing-bare-metal-network-customizations.html#installation-configure-proxy_installing-bare-metal-network-customizations)
