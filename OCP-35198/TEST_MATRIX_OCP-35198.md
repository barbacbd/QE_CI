# OCP-35198 Test Matrix

## Quick Reference: Machine Types and Expected Results

| Machine Type | Expected Result | Error Category | Error Message Pattern |
|-------------|----------------|----------------|----------------------|
| **VALID TYPES** | | | |
| `n1-standard-4` | ✅ PASS | - | Should succeed |
| `custom-4-16384` | ✅ PASS | - | Should succeed |
| `n1-custom-4-16384` | ✅ PASS | - | Should succeed (BZ#1898713) |
| **404 NOT FOUND** | | | |
| `n1-dne-4` | ❌ FAIL | 404 | `Error 404.*not found` |
| `custom-2` | ❌ FAIL | 404 | `Error 404.*not found` |
| `custom-a` | ❌ FAIL | 404 | `Error 404.*not found` |
| `custom-2-b` | ❌ FAIL | 404 | `Error 404.*not found` |
| `n1-custom-2` | ❌ FAIL | 404 | `Error 404.*not found` |
| `n1-custom-a` | ❌ FAIL | 404 | `Error 404.*not found` |
| `n1-custom-2-b` | ❌ FAIL | 404 | `Error 404.*not found` |
| **400 INVALID RESOURCE** | | | |
| `custom-4-16383` | ❌ FAIL | 400 | Memory not multiple of 256MiB |
| `n1-custom-4-16383` | ❌ FAIL | 400 | Memory not multiple of 256MiB |
| `custom-3-16384` | ❌ FAIL | 400 | vCPUs not multiple of 2 |
| `n1-custom-3-16384` | ❌ FAIL | 400 | vCPUs not multiple of 2 |
| **MINIMUM REQUIREMENTS** | | | |
| `n1-standard-2` | ❌ FAIL | Validation | Minimum 4 vCPUs required |
| `custom-2-7680` | ❌ FAIL | Validation | Minimum 4 vCPUs / 15360 MB |
| `n1-custom-2-7680` | ❌ FAIL | Validation | Minimum 4 vCPUs / 15360 MB |

## OpenShift Minimum Requirements

- **Control Plane**: 4 vCPUs, 15360 MB (15 GB) Memory
- **Compute Nodes**: 2 vCPUs, 8192 MB (8 GB) Memory

## GCP Custom Machine Type Format

### Standard Format
```
custom-[NUMBER_OF_CPUS]-[AMOUNT_OF_MEMORY_IN_MB]
```
Example: `custom-4-16384` = 4 vCPUs, 16GB RAM

### N1 Custom Format
```
n1-custom-[NUMBER_OF_CPUS]-[AMOUNT_OF_MEMORY_IN_MB]
```
Example: `n1-custom-4-16384` = 4 vCPUs, 16GB RAM

### Constraints
- **vCPUs**: Must be multiple of 2 (if > 2)
- **Memory**: Must be multiple of 256 MiB
- **Memory Range**: 0.9 GB to 6.5 GB per vCPU

## Test Execution

### Quick Test
```bash
# Set your GCP project
export GCP_PROJECT_ID="myproject"

# Run Python version
python3 test_ocp_35198_gcp_custom_types.py --project-id $GCP_PROJECT_ID

# OR run Bash version
./test_ocp_35198_gcp_custom_types.sh
```

### With JSON Output
```bash
python3 test_ocp_35198_gcp_custom_types.py \
  --project-id myproject \
  --export-json results.json
```

## Expected Test Summary

```
Total Tests: 17
├── Valid Types: 3 tests → Should PASS
├── 404 Not Found: 7 tests → Should FAIL with 404
├── 400 Invalid Resource: 4 tests → Should FAIL with 400
└── Below Minimum: 3 tests → Should FAIL with validation error
```

## Related Bugzillas

1. **BZ#1878108** - Main bug for custom type support
2. **BZ#1898194** - Regression in 4.7
3. **BZ#1898713** - Fix for n1-custom-4-16384
4. **BZ#1898713** - Related to OCP-36151 (minimum requirements)

## Test Strategy

1. **Positive Testing**: Verify valid custom types work
2. **Negative Testing - 404**: Non-existent types return proper 404 errors
3. **Negative Testing - 400**: Invalid formats return proper 400 errors  
4. **Negative Testing - Validation**: Below-minimum specs caught early

## Common Issues

### Test shows PASS but should FAIL
- May need actual GCP API access for some validations
- Check if openshift-install has GCP credentials configured

### All validations show PASS
- Validations may be bypassed without proper GCP authentication
- Ensure you have valid GCP credentials: `gcloud auth application-default login`

### Tests timeout
- Increase timeout in Python script (default: 300 seconds)
- Check network connectivity to GCP APIs
