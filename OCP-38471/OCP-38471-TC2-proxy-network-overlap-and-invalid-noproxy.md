# Test Case 2: Proxy Network Overlap and Invalid noProxy Values

**Test Case ID:** OCP-38471-TC2  
**Polarion ID:** OCP-38471  
**Component:** OpenShift Installer  
**Feature:** Proxy Validation  
**Priority:** High  
**Automation:** Candidate

## Description
Verify that the OpenShift installer correctly validates proxy configuration and rejects:
- Proxy servers that overlap with service network CIDR
- Proxy servers that overlap with cluster network CIDR
- Invalid noProxy domain format (uppercase letters)
- Invalid noProxy CIDR notation (invalid subnet mask)

## Prerequisites
- OpenShift installer binary (openshift-install) is available
- Installation directory is prepared

## Test Steps

### Step 1: Create install-config.yaml with overlapping proxy and invalid noProxy

Create an `install-config.yaml` file with the following configuration:

```yaml
proxy:
  httpProxy: https://user:password@172.30.1.25:3128
  httpsProxy: http://user:password@10.128.1.25:3128
  noProxy: ABC.com,10.0.2.1/280

networking:
  clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
  machineNetwork:
  - cidr: 10.0.0.0/16
  networkType: OpenShiftSDN
  serviceNetwork:
  - 172.30.0.0/16
```

**Configuration Issues:**
- `httpProxy`: IP address `172.30.1.25` is part of the service network `172.30.0.0/16`
- `httpsProxy`: IP address `10.128.1.25` is part of the cluster network `10.128.0.0/14`
- `noProxy`: Contains uppercase domain `ABC.com` (should be lowercase)
- `noProxy`: Contains invalid CIDR `10.0.2.1/280` (subnet mask cannot exceed /32 for IPv4)

### Step 2: Create manifests using the install-config.yaml

Run the following command:
```bash
openshift-install create manifests --dir <installation_dir>
```

## Expected Results

### Expected Result for Step 2:
The command should **FAIL** with a FATAL error message indicating the proxy settings are incorrect:

```
level=fatal msg=failed to fetch Master Machines: failed to load asset "Install Config": 
invalid "install-config.yaml" file: [
proxy.httpProxy: Invalid value: "http://user:password@172.30.1.25:3128": proxy value is part of the service networks, 
proxy.httpsProxy: Invalid value: "https://user:password@10.128.1.25:3128": proxy value is part of the cluster networks, 
proxy.noProxy: Invalid value: "ABC.com,10.0.2.1/280": each element of noProxy must be a CIDR or domain without wildcard characters, 
which is violated by element 0 "ABC.com", 
proxy.noProxy: Invalid value: "ABC.com,10.0.2.1/280": each element of noProxy must be a CIDR or domain without wildcard characters, 
which is violated by element 1 "10.0.2.1/280"]
```

**Key Validation Points:**
1. ✓ httpProxy validation detects overlap with service network
2. ✓ httpsProxy validation detects overlap with cluster network
3. ✓ noProxy validation detects invalid domain format (uppercase/wildcard)
4. ✓ noProxy validation detects invalid CIDR notation
5. ✓ No manifests are created
6. ✓ Installation process stops with detailed error messages for each violation

## Pass/Fail Criteria

**PASS:** 
- The installer rejects the configuration with appropriate error messages for all validation failures
- Network overlap detection works correctly for both httpProxy and httpsProxy
- noProxy validation catches both invalid domain format and invalid CIDR
- No manifests are created
- Error messages clearly indicate which network is overlapping and what is wrong with each noProxy element

**FAIL:**
- The installer accepts proxy IPs that overlap with cluster or service networks
- Invalid noProxy values are not detected
- Manifests are created despite invalid settings
- Error messages are missing, unclear, or incomplete
- Any validation check is not performed

## Additional Test Scenarios

### Scenario A: Valid Configuration (Negative Test)
After fixing all issues, verify that a valid configuration is accepted:
```yaml
proxy:
  httpProxy: http://user:password@192.168.1.25:3128
  httpsProxy: https://user:password@192.168.1.25:3128
  noProxy: abc.com,10.0.2.1/24
```

### Scenario B: Edge Cases
Test boundary conditions:
- Proxy IP at the edge of service network range
- Valid CIDR with /32 mask
- Domain with hyphens and numbers

## Notes
- All validation errors should be reported in a single execution
- The error message format may vary slightly between OpenShift versions
- Pay attention to the specific element index reported for noProxy violations
- Network overlap detection should work regardless of proxy scheme (http/https)
