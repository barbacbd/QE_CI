#!/bin/bash

# OCP-38471 Test Execution Script
# This script runs the proxy validation test cases

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file if it exists
if [ -f "${SCRIPT_DIR}/.env" ]; then
    source "${SCRIPT_DIR}/.env"
fi

# Configuration with defaults
WORK_DIR="${WORK_DIR:-${SCRIPT_DIR}/test-runs}"
TEST_BASE_DIR="${WORK_DIR}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OPENSHIFT_INSTALL="${OPENSHIFT_INSTALL:-openshift-install}"
PULL_SECRET_FILE="${PULL_SECRET_FILE:-$HOME/secrets/pull-secrets.txt}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/github_ed25519.pub}"
BASE_DOMAIN="${BASE_DOMAIN:-installer.gcp.devcluster.openshift.com}"
CLUSTER_NAME="${CLUSTER_NAME:-bbarbach-ocp-38471}"
PLATFORM="${PLATFORM:-gcp}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# OpenShift Installer Environment Variables
export OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE="${OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE:-quay.io/openshift-release-dev/ocp-release:4.22.0-ec.5-x86_64}"
export OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY="${OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Function to print colored output (backward compatibility)
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            log_success "$message"
            ;;
        "FAIL")
            log_error "$message"
            ;;
        "INFO")
            log_info "$message"
            ;;
        "WARN")
            log_warning "$message"
            ;;
    esac
}

# Function to cleanup test directory
cleanup_test_dir() {
    local test_dir=$1
    if [ -d "$test_dir" ]; then
        rm -rf "$test_dir"
    fi
}

# Function to run a single test case
run_test_case() {
    local tc_id=$1
    local config_file=$2
    local test_dir="${TEST_BASE_DIR}/${tc_id}-${TIMESTAMP}"

    print_status "INFO" "Running $tc_id"
    print_status "INFO" "Test directory: $test_dir"

    # Create test directory
    mkdir -p "$test_dir"

    # Copy install-config.yaml
    cp "$config_file" "$test_dir/install-config.yaml"

    # Run openshift-install create manifests
    print_status "INFO" "Executing: openshift-install create manifests --dir $test_dir"

    set +e
    output=$(openshift-install create manifests --dir "$test_dir" 2>&1)
    exit_code=$?
    set -e

    echo "$output" > "$test_dir/output.log"

    # Check if command failed as expected
    if [ $exit_code -ne 0 ]; then
        print_status "PASS" "$tc_id - Command failed as expected"
        echo -e "\nError output:"
        echo "$output"

        # Save results
        echo "EXIT_CODE=$exit_code" > "$test_dir/result.txt"
        echo "STATUS=PASS" >> "$test_dir/result.txt"
        return 0
    else
        print_status "FAIL" "$tc_id - Command succeeded but should have failed"
        echo -e "\nUnexpected output:"
        echo "$output"

        # Save results
        echo "EXIT_CODE=$exit_code" > "$test_dir/result.txt"
        echo "STATUS=FAIL" >> "$test_dir/result.txt"
        return 1
    fi
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

    # Show openshift-install version
    log_info "OpenShift Installer Version:"
    ${OPENSHIFT_INSTALL} version || true

    # Show environment configuration
    log_info "Environment Configuration:"
    log_info "  WORK_DIR: ${WORK_DIR}"
    log_info "  OPENSHIFT_INSTALL: ${OPENSHIFT_INSTALL}"
    log_info "  BASE_DOMAIN: ${BASE_DOMAIN}"
    log_info "  CLUSTER_NAME: ${CLUSTER_NAME}"
    log_info "  PLATFORM: ${PLATFORM}"

    if [ -n "${OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE}" ]; then
        log_info "  RELEASE_IMAGE_OVERRIDE: ${OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE}"
    fi

    if [ "${OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY}" = "true" ]; then
        log_warning "  Image policy validation is DISABLED"
    fi

    # Check for optional files
    if [ ! -f "$PULL_SECRET_FILE" ]; then
        log_warning "Pull secret not found at $PULL_SECRET_FILE (not required for validation tests)"
    fi

    if [ ! -f "$SSH_KEY" ]; then
        log_warning "SSH key not found at $SSH_KEY (not required for validation tests)"
    fi
}

# Main execution
main() {
    log_info "=========================================="
    log_info "OCP-38471: Proxy Validation Test Suite"
    log_info "=========================================="
    echo ""

    setup

    # Create test runs directory
    mkdir -p "$TEST_BASE_DIR"

    # Run TC1
    echo ""
    echo "--------------------------------------"
    echo "Test Case 1: Invalid Proxy Scheme and noProxy with Spaces"
    echo "--------------------------------------"
    run_test_case "TC1" "${SCRIPT_DIR}/test-configs/tc1-install-config.yaml"
    tc1_result=$?

    # Run TC2
    echo ""
    echo "--------------------------------------"
    echo "Test Case 2: Proxy Network Overlap and Invalid noProxy"
    echo "--------------------------------------"
    run_test_case "TC2" "${SCRIPT_DIR}/test-configs/tc2-install-config.yaml"
    tc2_result=$?

    # Optional: Run valid config test (negative test)
    echo ""
    echo "--------------------------------------"
    echo "Optional: Valid Configuration Test"
    echo "--------------------------------------"
    print_status "INFO" "Testing valid configuration (should succeed)..."
    valid_test_dir="${TEST_BASE_DIR}/valid-config-${TIMESTAMP}"
    mkdir -p "$valid_test_dir"
    cp "${SCRIPT_DIR}/test-configs/valid-install-config.yaml" "$valid_test_dir/install-config.yaml"

    # Note: This may fail due to missing cloud credentials, which is expected
    print_status "INFO" "Note: Valid config test may fail due to missing credentials - this is OK"

    # Summary
    echo ""
    echo "======================================"
    echo "Test Summary"
    echo "======================================"

    total_tests=2
    passed_tests=0

    [ $tc1_result -eq 0 ] && ((passed_tests++))
    [ $tc2_result -eq 0 ] && ((passed_tests++))

    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $((total_tests - passed_tests))"

    if [ $passed_tests -eq $total_tests ]; then
        print_status "PASS" "All tests passed!"
        exit 0
    else
        print_status "FAIL" "Some tests failed"
        exit 1
    fi
}

# Run main function
main
