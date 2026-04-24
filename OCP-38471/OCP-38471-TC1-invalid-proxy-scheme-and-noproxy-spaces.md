# Test Case 1: Invalid Proxy Scheme and noProxy with Spaces

**Test Case ID:** OCP-38471-TC1  
**Polarion ID:** OCP-38471  
**Component:** OpenShift Installer  
**Feature:** Proxy Validation  
**Priority:** High  
**Automation:** Candidate

## Description
Verify that the OpenShift installer correctly validates proxy configuration and rejects:
- httpProxy without a proper scheme
- httpsProxy with an invalid scheme (ftp)
- noProxy values containing spaces

## Prerequisites
- OpenShift installer binary (openshift-install) is available
- Installation directory is prepared

## Test Steps

### Step 1: Create install-config.yaml with invalid proxy settings

Create an `install-config.yaml` file with the following invalid proxy configuration:

```yaml
proxy:
  httpProxy: user:password@127.0.0.1:3128
  httpsProxy: ftp://user:password@127.0.0.1:3128
  noProxy: test.no-proxy.com, localhost
```

**Configuration Issues:**
- `httpProxy`: Missing scheme (should start with `http://` or `https://`)
- `httpsProxy`: Uses invalid scheme `ftp://` (only `http://` or `https://` allowed)
- `noProxy`: Contains space after comma (spaces not allowed)

### Step 2: Create manifests using the install-config.yaml

Run the following command:
```bash
openshift-install create manifests --dir <installation_dir>
```

## Expected Results

### Expected Result for Step 2:
The command should **FAIL** with a FATAL error message indicating the proxy settings are incorrect:

```
FATAL failed to fetch Master Machines: failed to load asset "Install Config":
 invalid "install-config.yaml" file: 
[proxy.httpProxy: Unsupported value: "user": supported values: "http",
 proxy.httpsProxy: Unsupported value: "ftp": supported values: "http", "https",
 proxy.noProxy: Invalid value: "test.no-proxy.com, localhost": noProxy must not have spaces]
```

**Key Validation Points:**
1. ✓ httpProxy validation detects missing scheme
2. ✓ httpsProxy validation rejects unsupported scheme (ftp)
3. ✓ noProxy validation detects spaces in the value
4. ✓ No manifests are created
5. ✓ Installation process stops with clear error messages

## Pass/Fail Criteria

**PASS:** 
- The installer rejects the configuration with appropriate error messages for all three validation failures
- No manifests are created
- Error messages clearly indicate what is wrong with each proxy field

**FAIL:**
- The installer accepts invalid proxy configuration
- Manifests are created despite invalid settings
- Error messages are missing or unclear
- Any validation check is not performed

## Notes
- All three validation errors should be reported in a single execution
- Error messages should be clear and actionable for users
