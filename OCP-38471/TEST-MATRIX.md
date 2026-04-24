# OCP-38471 Test Matrix

## Test Case Overview

| ID | Test Case | Validation Type | Expected Result |
|----|-----------|----------------|-----------------|
| TC1 | Invalid Proxy Scheme and noProxy Spaces | Input Validation | FAIL with errors |
| TC2 | Network Overlap and Invalid noProxy | Network Validation | FAIL with errors |

## TC1: Invalid Proxy Scheme and noProxy with Spaces

### Test Scenarios

| Scenario | Configuration | Expected Error |
|----------|---------------|----------------|
| 1.1 | `httpProxy: user:password@127.0.0.1:3128` | Unsupported value: "user": supported values: "http" |
| 1.2 | `httpsProxy: ftp://user:password@127.0.0.1:3128` | Unsupported value: "ftp": supported values: "http", "https" |
| 1.3 | `noProxy: test.no-proxy.com, localhost` | Invalid value: noProxy must not have spaces |

### Validation Points
- ✓ Proxy scheme validation (http/https only)
- ✓ noProxy whitespace detection
- ✓ All errors reported in single execution

## TC2: Proxy Network Overlap and Invalid noProxy Values

### Test Scenarios

| Scenario | Configuration | Network | Expected Error |
|----------|---------------|---------|----------------|
| 2.1 | `httpProxy: https://user:password@172.30.1.25:3128` | Service: 172.30.0.0/16 | proxy value is part of the service networks |
| 2.2 | `httpsProxy: http://user:password@10.128.1.25:3128` | Cluster: 10.128.0.0/14 | proxy value is part of the cluster networks |
| 2.3 | `noProxy: ABC.com` | N/A | each element of noProxy must be a CIDR or domain without wildcard characters |
| 2.4 | `noProxy: 10.0.2.1/280` | N/A | Invalid CIDR (subnet mask > 32) |

### Validation Points
- ✓ Service network overlap detection
- ✓ Cluster network overlap detection
- ✓ Machine network overlap detection (implied)
- ✓ noProxy domain format validation
- ✓ noProxy CIDR validation

## Network Configuration Matrix

### Default Test Networks

| Network Type | CIDR | Used By |
|-------------|------|---------|
| Cluster Network | 10.128.0.0/14 | Pod networking |
| Machine Network | 10.0.0.0/16 | Node networking |
| Service Network | 172.30.0.0/16 | Service networking |

### Valid Proxy Examples (Non-overlapping)

| Proxy Type | Example URL | Status |
|-----------|-------------|--------|
| httpProxy | `http://192.168.1.25:3128` | ✓ Valid (outside all networks) |
| httpsProxy | `https://192.168.1.25:3128` | ✓ Valid (outside all networks) |
| noProxy | `example.com,10.0.2.1/24` | ✓ Valid (proper format) |

### Invalid Proxy Examples (Overlapping)

| Proxy Type | Example URL | Overlaps With | Status |
|-----------|-------------|---------------|--------|
| httpProxy | `http://172.30.1.25:3128` | Service Network | ✗ Invalid |
| httpsProxy | `https://10.128.1.25:3128` | Cluster Network | ✗ Invalid |
| httpProxy | `http://10.0.1.25:3128` | Machine Network | ✗ Invalid |

## Platform Support Matrix

| Platform | Supported | Notes |
|----------|-----------|-------|
| AWS | ✓ Yes | Default test platform |
| GCP | ✓ Yes | Requires GCP_PROJECT_ID |
| Azure | ✓ Yes | Requires resource group |
| vSphere | ✓ Yes | Generic platform config |
| BareMetal | ✓ Yes | Generic platform config |
| OpenStack | ✓ Yes | Generic platform config |

## OpenShift Version Compatibility

| Version | Validation Support | Notes |
|---------|-------------------|-------|
| 4.12.x | ✓ Yes | Full proxy validation |
| 4.13.x | ✓ Yes | Full proxy validation |
| 4.14.x | ✓ Yes | Enhanced validation messages |
| 4.15.x | ✓ Yes | Current stable |
| 4.16.x | ✓ Yes | Latest/nightly |

**Note:** Error message format may vary between versions, but validation logic remains consistent.

## Test Execution Matrix

### Implementation Options

| Implementation | Language | Use Case |
|---------------|----------|----------|
| `run-tests.sh` | Bash | Quick testing, CI/CD integration |
| `test_ocp_38471_proxy_validation.py` | Python | Detailed analysis, programmatic access |

### Environment Configuration Options

| Method | File | Priority | Use Case |
|--------|------|----------|----------|
| `.env` file | `.env` | Medium | Persistent configuration |
| Export variables | N/A | High | One-off testing |
| Inline | N/A | Highest | Script execution |

### Release Testing Matrix

| Scenario | Command | Purpose |
|----------|---------|---------|
| Default Release | `./run-tests.sh` | Test with system default |
| Specific Release | `OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE=... ./run-tests.sh` | Test specific version |
| Nightly Build | `OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY=true ...` | Test unreleased builds |
| Multiple Releases | Loop through release array | Version compatibility testing |

## Expected Results Matrix

### TC1 Expected Outputs

| Check | Error Pattern | Status |
|-------|---------------|--------|
| httpProxy scheme | `Unsupported value: "user"` | Must match |
| httpsProxy scheme | `Unsupported value: "ftp"` | Must match |
| noProxy spaces | `noProxy must not have spaces` | Must match |
| Exit code | Non-zero | Required |
| Manifests created | No | Required |

### TC2 Expected Outputs

| Check | Error Pattern | Status |
|-------|---------------|--------|
| httpProxy overlap | `part of the service networks` | Must match |
| httpsProxy overlap | `part of the cluster networks` | Must match |
| noProxy domain | `element 0.*ABC.com` | Must match |
| noProxy CIDR | `element 1.*280` | Must match |
| Exit code | Non-zero | Required |
| Manifests created | No | Required |

## Pass/Fail Criteria

### PASS Conditions
- ✓ openshift-install exits with non-zero code
- ✓ All expected validation errors are reported
- ✓ No manifests directory created
- ✓ Error messages are clear and specific
- ✓ All errors reported in single execution

### FAIL Conditions
- ✗ openshift-install exits with zero (success)
- ✗ Some validation errors are missing
- ✗ Manifests are created despite errors
- ✗ Error messages are vague or missing
- ✗ Multiple executions needed to see all errors

## Test Coverage Summary

### Proxy Configuration Validation
- ✓ httpProxy scheme validation
- ✓ httpsProxy scheme validation
- ✓ Proxy URL format validation
- ✓ noProxy format validation
- ✓ noProxy whitespace validation
- ✓ noProxy CIDR validation
- ✓ noProxy domain validation

### Network Overlap Detection
- ✓ Service network overlap
- ✓ Cluster network overlap
- ✓ Machine network overlap (via cluster network)

### Error Handling
- ✓ Multiple simultaneous errors
- ✓ Clear error messages
- ✓ Proper exit codes
- ✓ Prevents manifest generation

## CI/CD Integration Matrix

| CI System | Integration Method | Example |
|-----------|-------------------|---------|
| Jenkins | Pipeline | See ENVIRONMENT-EXAMPLES.md |
| GitLab CI | .gitlab-ci.yml | See ENVIRONMENT-EXAMPLES.md |
| GitHub Actions | Workflow | Standard bash execution |
| Tekton | Task/Pipeline | Standard bash execution |
| Prow | Job config | Standard bash execution |

## Documentation Coverage

| Document | Coverage |
|----------|----------|
| Test Case Specs | OCP-38471-TC1/TC2-*.md |
| Execution Guide | TEST-EXECUTION-GUIDE.md |
| Environment Config | ENVIRONMENT-EXAMPLES.md |
| Quick Reference | README.md, USAGE-SUMMARY.md |
| Test Matrix | TEST-MATRIX.md (this file) |

## Related Polarion Work Items

| ID | Description | Relationship |
|----|-------------|--------------|
| OCP-38471 | Proxy validation testing | This test |
| OCP-35198 | GCP machine type validation | Similar pattern |

## Test Maintenance

### When to Update Tests

- New OpenShift version released
- Proxy validation logic changes
- New network types introduced
- Error message format changes
- New platforms supported

### Regression Testing

Run these tests:
- Before each OpenShift release
- After installer code changes
- When proxy-related bugs are fixed
- As part of nightly CI

## Metrics and Reporting

### Success Metrics
- All tests execute without errors
- Both test cases fail with expected errors
- Test execution time < 2 minutes
- Clear, actionable error messages

### Reporting Template

```
Test Run: OCP-38471
Date: YYYY-MM-DD
OpenShift Version: X.Y.Z
Platform: AWS/GCP/Azure

TC1 Result: PASS/FAIL
  - httpProxy validation: PASS/FAIL
  - httpsProxy validation: PASS/FAIL
  - noProxy validation: PASS/FAIL

TC2 Result: PASS/FAIL
  - Service network overlap: PASS/FAIL
  - Cluster network overlap: PASS/FAIL
  - noProxy domain: PASS/FAIL
  - noProxy CIDR: PASS/FAIL

Overall: PASS/FAIL
Notes: [Any deviations or observations]
```
