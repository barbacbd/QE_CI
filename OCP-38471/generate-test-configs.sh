#!/bin/bash

# Script to generate test install-config.yaml files with environment variables
# This allows dynamic configuration of credentials and platform settings

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file if it exists
if [ -f "${SCRIPT_DIR}/.env" ]; then
    source "${SCRIPT_DIR}/.env"
fi

# Configuration with defaults
PULL_SECRET_FILE="${PULL_SECRET_FILE:-$HOME/secrets/pull-secrets.txt}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/github_ed25519.pub}"
BASE_DOMAIN="${BASE_DOMAIN:-installer.gcp.devcluster.openshift.com}"
CLUSTER_NAME="${CLUSTER_NAME:-bbarbach-ocp-38471}"
PLATFORM="${PLATFORM:-gcp}"
AWS_REGION="${AWS_REGION:-us-east-1}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-openshift-dev-installer}"
GCP_REGION="${GCP_REGION:-us-west1}"
CLUSTER_NETWORK_CIDR="${CLUSTER_NETWORK_CIDR:-10.128.0.0/14}"
CLUSTER_NETWORK_HOST_PREFIX="${CLUSTER_NETWORK_HOST_PREFIX:-23}"
MACHINE_NETWORK_CIDR="${MACHINE_NETWORK_CIDR:-10.0.0.0/16}"
SERVICE_NETWORK_CIDR="${SERVICE_NETWORK_CIDR:-172.30.0.0/16}"
NETWORK_TYPE="${NETWORK_TYPE:-OVNKubernetes}"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Function to get pull secret
get_pull_secret() {
    if [ -f "$PULL_SECRET_FILE" ]; then
        cat "$PULL_SECRET_FILE" | tr -d '\n'
    else
        log_warning "Pull secret file not found, using placeholder"
        echo '{"auths":{"fake.registry.io":{"auth":"dGVzdDp0ZXN0"}}}'
    fi
}

# Function to get SSH key
get_ssh_key() {
    if [ -f "$SSH_KEY" ]; then
        cat "$SSH_KEY" | tr -d '\n'
    else
        log_warning "SSH key not found, using placeholder"
        echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC test@example.com'
    fi
}

# Function to generate platform configuration
generate_platform_config() {
    case $PLATFORM in
        aws)
            cat <<EOF
platform:
  aws:
    region: ${AWS_REGION}
EOF
            ;;
        gcp)
            cat <<EOF
platform:
  gcp:
    projectID: ${GCP_PROJECT_ID}
    region: ${GCP_REGION}
EOF
            ;;
        azure)
            cat <<EOF
platform:
  azure:
    region: ${AZURE_REGION:-eastus}
    baseDomainResourceGroupName: ${AZURE_BASE_DOMAIN_RESOURCE_GROUP_NAME:-os4-common}
EOF
            ;;
        *)
            cat <<EOF
platform:
  aws:
    region: us-east-1
EOF
            ;;
    esac
}

# Generate TC1 config
generate_tc1_config() {
    local output_file="${SCRIPT_DIR}/test-configs/tc1-install-config.yaml"
    log_info "Generating TC1 config: $output_file"

    cat > "$output_file" <<EOF
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
metadata:
  name: ${CLUSTER_NAME}
proxy:
  httpProxy: user:password@127.0.0.1:3128
  httpsProxy: ftp://user:password@127.0.0.1:3128
  noProxy: test.no-proxy.com, localhost
networking:
  clusterNetwork:
  - cidr: ${CLUSTER_NETWORK_CIDR}
    hostPrefix: ${CLUSTER_NETWORK_HOST_PREFIX}
  machineNetwork:
  - cidr: ${MACHINE_NETWORK_CIDR}
  networkType: ${NETWORK_TYPE}
  serviceNetwork:
  - ${SERVICE_NETWORK_CIDR}
$(generate_platform_config)
pullSecret: '$(get_pull_secret)'
sshKey: '$(get_ssh_key)'
EOF

    log_success "TC1 config generated"
}

# Generate TC2 config
generate_tc2_config() {
    local output_file="${SCRIPT_DIR}/test-configs/tc2-install-config.yaml"
    log_info "Generating TC2 config: $output_file"

    cat > "$output_file" <<EOF
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
metadata:
  name: ${CLUSTER_NAME}
proxy:
  httpProxy: https://user:password@172.30.1.25:3128
  httpsProxy: http://user:password@10.128.1.25:3128
  noProxy: ABC.com,10.0.2.1/280
networking:
  clusterNetwork:
  - cidr: ${CLUSTER_NETWORK_CIDR}
    hostPrefix: ${CLUSTER_NETWORK_HOST_PREFIX}
  machineNetwork:
  - cidr: ${MACHINE_NETWORK_CIDR}
  networkType: ${NETWORK_TYPE}
  serviceNetwork:
  - ${SERVICE_NETWORK_CIDR}
$(generate_platform_config)
pullSecret: '$(get_pull_secret)'
sshKey: '$(get_ssh_key)'
EOF

    log_success "TC2 config generated"
}

# Generate valid config
generate_valid_config() {
    local output_file="${SCRIPT_DIR}/test-configs/valid-install-config.yaml"
    log_info "Generating valid config: $output_file"

    cat > "$output_file" <<EOF
apiVersion: v1
baseDomain: ${BASE_DOMAIN}
metadata:
  name: ${CLUSTER_NAME}
proxy:
  httpProxy: http://user:password@192.168.1.25:3128
  httpsProxy: https://user:password@192.168.1.25:3128
  noProxy: ${BASE_DOMAIN},localhost,127.0.0.1,.svc,.cluster.local
networking:
  clusterNetwork:
  - cidr: ${CLUSTER_NETWORK_CIDR}
    hostPrefix: ${CLUSTER_NETWORK_HOST_PREFIX}
  machineNetwork:
  - cidr: ${MACHINE_NETWORK_CIDR}
  networkType: ${NETWORK_TYPE}
  serviceNetwork:
  - ${SERVICE_NETWORK_CIDR}
$(generate_platform_config)
pullSecret: '$(get_pull_secret)'
sshKey: '$(get_ssh_key)'
EOF

    log_success "Valid config generated"
}

# Main
main() {
    log_info "=========================================="
    log_info "Generating Test Configurations"
    log_info "=========================================="
    echo ""

    # Show configuration
    log_info "Configuration:"
    log_info "  BASE_DOMAIN: ${BASE_DOMAIN}"
    log_info "  CLUSTER_NAME: ${CLUSTER_NAME}"
    log_info "  PLATFORM: ${PLATFORM}"
    log_info "  NETWORK_TYPE: ${NETWORK_TYPE}"
    echo ""

    # Create test-configs directory
    mkdir -p "${SCRIPT_DIR}/test-configs"

    # Generate configs
    generate_tc1_config
    generate_tc2_config
    generate_valid_config

    echo ""
    log_success "All test configurations generated successfully!"
    log_info "Configs location: ${SCRIPT_DIR}/test-configs/"
}

main
