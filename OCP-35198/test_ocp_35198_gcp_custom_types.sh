#!/bin/bash
#
# Test Case: OCP-35198
# Description: Test OpenShift installation with GCP custom machine types (good and bad)
# References:
#   - https://bugzilla.redhat.com/show_bug.cgi?id=1878108
#   - https://bugzilla.redhat.com/show_bug.cgi?id=1898194
#   - https://bugzilla.redhat.com/show_bug.cgi?id=1898713
#

set -euo pipefail

# Configuration
WORK_DIR="${WORK_DIR:-/tmp/ocp-35198-test}"
INSTALL_CONFIG_TEMPLATE="${INSTALL_CONFIG_TEMPLATE:-install-config.yaml.template}"
OPENSHIFT_INSTALL="${OPENSHIFT_INSTALL:-openshift-install}"
PROJECT_ID="${GCP_PROJECT_ID:-openshift-dev-installer}"
REGION="${GCP_REGION:-us-west1}"
ZONE="${GCP_ZONE:-us-west1-b}"
BASE_DOMAIN="${BASE_DOMAIN:-installer.gcp.devcluster.openshift.com}"
CLUSTER_NAME="${CLUSTER_NAME:-test-cluster}"
PULL_SECRET_FILE="${PULL_SECRET_FILE:-$HOME/secrets/pull-secrets.txt}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/github_ed25519.pub}"

# OpenShift Installer Environment Variables
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE="${OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE:-quay.io/openshift-release-dev/ocp-release:4.22.0-ec.5-x86_64}"
export OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY="${OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED_TESTS=0
FAILED_TESTS=0
declare -a FAILED_TEST_DETAILS

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((FAILED_TESTS++))
    FAILED_TEST_DETAILS+=("$*")
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test directories..."
    rm -rf "${WORK_DIR}"
}

# Setup function
setup() {
    log_info "Setting up test environment..."

    # Create work directory
    mkdir -p "${WORK_DIR}"

    # Verify prerequisites
    if ! command -v ${OPENSHIFT_INSTALL} &> /dev/null; then
        log_error "openshift-install not found in PATH"
        exit 1
    fi

    if [ -z "$PROJECT_ID" ]; then
        log_warning "GCP_PROJECT_ID not set, some validations may fail"
    fi

    if [ ! -f "$PULL_SECRET_FILE" ]; then
        log_warning "Pull secret not found at $PULL_SECRET_FILE"
    fi

    if [ ! -f "$SSH_KEY" ]; then
        log_warning "SSH key not found at $SSH_KEY"
    fi
}

# Generate install-config.yaml with specific machine type
generate_install_config() {
    local machine_type=$1
    local test_dir=$2
    local config_file="${test_dir}/install-config.yaml"

    mkdir -p "${test_dir}"

    cat > "${config_file}" <<EOF
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform:
    gcp:
      type: ${machine_type}
  replicas: 3
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform:
    gcp:
      type: ${machine_type}
  replicas: 3
metadata:
  name: ${CLUSTER_NAME}
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
    projectID: ${PROJECT_ID}
    region: ${REGION}
publish: External
EOF

    # Add pull secret if available
    if [ -f "$PULL_SECRET_FILE" ]; then
        echo "pullSecret: '$(cat $PULL_SECRET_FILE | tr -d '\n')'" >> "${config_file}"
    else
        echo "pullSecret: ''" >> "${config_file}"
    fi

    # Add SSH key if available
    if [ -f "$SSH_KEY" ]; then
        echo "sshKey: '$(cat $SSH_KEY | tr -d '\n')'" >> "${config_file}"
    else
        echo "sshKey: ''" >> "${config_file}"
    fi

    echo "${config_file}"
}

# Test function: validate install config
test_machine_type() {
    local machine_type=$1
    local expected_result=$2  # "pass" or "fail"
    local expected_error_pattern="${3:-}"  # Expected error pattern (optional)

    local test_dir="${WORK_DIR}/${machine_type//\//_}"
    local test_name="Machine type: ${machine_type}"

    log_info "Testing: ${test_name}"

    # Generate install config
    local config_file=$(generate_install_config "${machine_type}" "${test_dir}")

    # Run validation
    local output_file="${test_dir}/validation_output.txt"
    local exit_code=0

    ${OPENSHIFT_INSTALL} create manifests --dir="${test_dir}" > "${output_file}" 2>&1 || exit_code=$?

    if [ "$expected_result" == "pass" ]; then
        if [ $exit_code -eq 0 ]; then
            log_success "${test_name} - Validation succeeded as expected"
            return 0
        else
            log_error "${test_name} - Expected success but got error: $(tail -5 ${output_file})"
            return 1
        fi
    else
        # Expected to fail
        if [ $exit_code -ne 0 ]; then
            # Check if error message matches expected pattern
            if [ -n "$expected_error_pattern" ]; then
                if grep -q "$expected_error_pattern" "${output_file}"; then
                    log_success "${test_name} - Failed with expected error: ${expected_error_pattern}"
                    return 0
                else
                    log_error "${test_name} - Failed but error message didn't match expected pattern"
                    log_error "  Expected: ${expected_error_pattern}"
                    log_error "  Got: $(grep -i error ${output_file} | head -1)"
                    return 1
                fi
            else
                log_success "${test_name} - Failed as expected"
                return 0
            fi
        else
            log_error "${test_name} - Expected failure but validation succeeded"
            return 1
        fi
    fi
}

# Main test execution
main() {
    log_info "=========================================="
    log_info "OCP-35198: GCP Custom Machine Type Tests"
    log_info "=========================================="
    echo ""

    setup

    # Test 1: Good custom types (should pass)
    log_info "=== Test Group 1: Valid Custom Types ==="
    test_machine_type "n1-standard-4" "pass" || true
    test_machine_type "custom-4-16384" "pass" || true
    test_machine_type "n1-custom-4-16384" "pass" || true
    echo ""

    # Test 2: Bad types - 404 Not Found
    log_info "=== Test Group 2: Non-existent Machine Types (404) ==="
    test_machine_type "n1-dne-4" "fail" "Error 404.*not found" || true
    test_machine_type "custom-2" "fail" "Error 404.*not found" || true
    test_machine_type "custom-a" "fail" "Error 404.*not found" || true
    test_machine_type "custom-2-b" "fail" "Error 404.*not found" || true
    test_machine_type "n1-custom-2" "fail" "Error 404.*not found" || true
    test_machine_type "n1-custom-a" "fail" "Error 404.*not found" || true
    test_machine_type "n1-custom-2-b" "fail" "Error 404.*not found" || true
    echo ""

    # Test 3: Bad types - Invalid Resource Usage
    log_info "=== Test Group 3: Invalid Resource Usage (400) ==="
    test_machine_type "custom-4-16383" "fail" "Memory should be a multiple of 256" || true
    test_machine_type "n1-custom-4-16383" "fail" "Memory should be a multiple of 256" || true
    test_machine_type "custom-3-16384" "fail" "Number of vCPUs should be multiple of 2" || true
    test_machine_type "n1-custom-3-16384" "fail" "Number of vCPUs should be multiple of 2" || true
    echo ""

    # Test 4: Invalid memory and CPU (below minimum requirements)
    log_info "=== Test Group 4: Below Minimum Requirements ==="
    test_machine_type "n1-standard-2" "fail" "does not meet minimum resource requirements of 4 vCPUs" || true
    test_machine_type "custom-2-7680" "fail" "does not meet minimum resource requirements" || true
    test_machine_type "n1-custom-2-7680" "fail" "does not meet minimum resource requirements" || true
    echo ""

    # Print summary
    log_info "=========================================="
    log_info "Test Summary"
    log_info "=========================================="
    log_info "Total Passed: ${PASSED_TESTS}"
    log_info "Total Failed: ${FAILED_TESTS}"

    if [ ${FAILED_TESTS} -gt 0 ]; then
        log_error "Failed tests:"
        for detail in "${FAILED_TEST_DETAILS[@]}"; do
            echo "  - ${detail}"
        done
        echo ""
        log_error "Overall result: FAILED"
        exit 1
    else
        log_success "Overall result: PASSED"
        exit 0
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main
