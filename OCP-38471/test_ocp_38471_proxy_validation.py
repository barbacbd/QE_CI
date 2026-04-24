#!/usr/bin/env python3
"""
Test Case: OCP-38471
Description: Test OpenShift installer proxy configuration validation
Author: QE Team
"""

import os
import sys
import subprocess
import tempfile
import shutil
import yaml
from typing import Dict, List, Tuple
from pathlib import Path

# Colors for terminal output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

class TestResult:
    """Test result tracking"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.details = []

    def add_pass(self, message: str):
        self.passed += 1
        print(f"{Colors.GREEN}[PASS]{Colors.NC} {message}")

    def add_fail(self, message: str):
        self.failed += 1
        print(f"{Colors.RED}[FAIL]{Colors.NC} {message}")
        self.details.append(message)

    def log_info(self, message: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

    def log_warning(self, message: str):
        print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")

    def summary(self):
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        print(f"Total Passed: {self.passed}")
        print(f"Total Failed: {self.failed}")

        if self.failed > 0:
            print(f"\n{Colors.RED}Failed tests:{Colors.NC}")
            for detail in self.details:
                print(f"  - {detail}")
            return False
        else:
            print(f"\n{Colors.GREEN}Overall result: PASSED{Colors.NC}")
            return True


class ProxyValidationTest:
    """OCP-38471 Proxy Validation Test"""

    def __init__(self):
        self.openshift_install = os.getenv('OPENSHIFT_INSTALL', 'openshift-install')
        self.base_domain = os.getenv('BASE_DOMAIN', 'installer.gcp.devcluster.openshift.com')
        self.cluster_name = os.getenv('CLUSTER_NAME', 'bbarbach-ocp-38471')
        self.platform = os.getenv('PLATFORM', 'gcp')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.gcp_project_id = os.getenv('GCP_PROJECT_ID', 'openshift-dev-installer')
        self.gcp_region = os.getenv('GCP_REGION', 'us-west1')
        self.work_dir = os.getenv('WORK_DIR', '/tmp/ocp-38471-test')
        self.pull_secret = os.getenv('PULL_SECRET_FILE', os.path.expanduser('~/secrets/pull-secrets.txt'))
        self.ssh_key = os.getenv('SSH_KEY', os.path.expanduser('~/.ssh/github_ed25519.pub'))

        # Set OpenShift installer environment variables
        if os.getenv('OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE'):
            os.environ['OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE'] = os.getenv('OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE')

        if os.getenv('OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY'):
            os.environ['OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY'] = os.getenv('OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY')

        self.results = TestResult()

    def generate_base_config(self) -> Dict:
        """Generate base install-config structure"""
        # Generate platform-specific config
        platform_config = {}
        if self.platform == 'aws':
            platform_config = {'region': self.aws_region}
        elif self.platform == 'gcp':
            platform_config = {
                'projectID': self.gcp_project_id,
                'region': self.gcp_region
            }

        return {
            'apiVersion': 'v1',
            'baseDomain': self.base_domain,
            'metadata': {
                'name': self.cluster_name
            },
            'networking': {
                'clusterNetwork': [{
                    'cidr': '10.128.0.0/14',
                    'hostPrefix': 23
                }],
                'machineNetwork': [{
                    'cidr': '10.0.0.0/16'
                }],
                'networkType': 'OVNKubernetes',
                'serviceNetwork': ['172.30.0.0/16']
            },
            'platform': {
                self.platform: platform_config
            },
            'pullSecret': '{"auths":{"fake.registry.io":{"auth":"dGVzdDp0ZXN0"}}}',
            'sshKey': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC test@example.com'
        }

    def create_install_config(self, test_dir: str, proxy_config: Dict) -> str:
        """Create install-config.yaml with specified proxy configuration"""
        config = self.generate_base_config()
        config['proxy'] = proxy_config

        config_path = os.path.join(test_dir, 'install-config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        return config_path

    def run_validation(self, test_dir: str) -> Tuple[int, str]:
        """Run openshift-install create manifests and return exit code and output"""
        cmd = [self.openshift_install, 'create', 'manifests', '--dir', test_dir]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stderr + result.stdout
        except subprocess.TimeoutExpired:
            return -1, "Command timeout"
        except Exception as e:
            return -1, str(e)

    def test_case_1_invalid_schemes_and_spaces(self):
        """TC1: Invalid Proxy Scheme and noProxy with Spaces"""
        self.results.log_info("\n" + "=" * 50)
        self.results.log_info("TC1: Invalid Proxy Scheme and noProxy with Spaces")
        self.results.log_info("=" * 50)

        test_dir = tempfile.mkdtemp(prefix='ocp38471-tc1-', dir=self.work_dir)

        try:
            proxy_config = {
                'httpProxy': 'user:password@127.0.0.1:3128',  # Missing scheme
                'httpsProxy': 'ftp://user:password@127.0.0.1:3128',  # Invalid scheme
                'noProxy': 'test.no-proxy.com, localhost'  # Contains space
            }

            self.create_install_config(test_dir, proxy_config)
            exit_code, output = self.run_validation(test_dir)

            # Save output
            with open(os.path.join(test_dir, 'output.log'), 'w') as f:
                f.write(output)

            # Verify failure
            if exit_code == 0:
                self.results.add_fail("TC1: Command succeeded but should have failed")
                return

            # Check for expected error messages
            checks = [
                ('httpProxy: Unsupported value' in output or 'httpProxy' in output,
                 "httpProxy validation"),
                ('httpsProxy: Unsupported value: "ftp"' in output or 'ftp' in output,
                 "httpsProxy invalid scheme (ftp)"),
                ('noProxy' in output and 'space' in output.lower(),
                 "noProxy space validation")
            ]

            all_passed = True
            for check, description in checks:
                if check:
                    self.results.log_info(f"  ✓ {description} detected")
                else:
                    self.results.log_warning(f"  ✗ {description} NOT detected")
                    all_passed = False

            if all_passed:
                self.results.add_pass("TC1: All validations detected correctly")
            else:
                self.results.add_fail("TC1: Some validations missing")

        finally:
            if os.getenv('KEEP_TEST_DIRS') != 'true':
                shutil.rmtree(test_dir, ignore_errors=True)

    def test_case_2_network_overlap_and_invalid_noproxy(self):
        """TC2: Proxy Network Overlap and Invalid noProxy Values"""
        self.results.log_info("\n" + "=" * 50)
        self.results.log_info("TC2: Proxy Network Overlap and Invalid noProxy")
        self.results.log_info("=" * 50)

        test_dir = tempfile.mkdtemp(prefix='ocp38471-tc2-', dir=self.work_dir)

        try:
            proxy_config = {
                'httpProxy': 'https://user:password@172.30.1.25:3128',  # Overlaps service network
                'httpsProxy': 'http://user:password@10.128.1.25:3128',  # Overlaps cluster network
                'noProxy': 'ABC.com,10.0.2.1/280'  # Invalid domain and CIDR
            }

            self.create_install_config(test_dir, proxy_config)
            exit_code, output = self.run_validation(test_dir)

            # Save output
            with open(os.path.join(test_dir, 'output.log'), 'w') as f:
                f.write(output)

            # Verify failure
            if exit_code == 0:
                self.results.add_fail("TC2: Command succeeded but should have failed")
                return

            # Check for expected error messages
            checks = [
                ('service network' in output.lower() and '172.30' in output,
                 "httpProxy service network overlap"),
                ('cluster network' in output.lower() and '10.128' in output,
                 "httpsProxy cluster network overlap"),
                ('ABC.com' in output or 'noProxy' in output,
                 "noProxy invalid domain"),
                ('280' in output or 'CIDR' in output,
                 "noProxy invalid CIDR")
            ]

            all_passed = True
            for check, description in checks:
                if check:
                    self.results.log_info(f"  ✓ {description} detected")
                else:
                    self.results.log_warning(f"  ✗ {description} NOT detected")
                    all_passed = False

            if all_passed:
                self.results.add_pass("TC2: All validations detected correctly")
            else:
                self.results.add_fail("TC2: Some validations missing")

        finally:
            if os.getenv('KEEP_TEST_DIRS') != 'true':
                shutil.rmtree(test_dir, ignore_errors=True)

    def run(self):
        """Run all tests"""
        self.results.log_info("=" * 50)
        self.results.log_info("OCP-38471: Proxy Validation Tests")
        self.results.log_info("=" * 50)

        # Setup
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

        # Verify openshift-install is available
        try:
            result = subprocess.run(
                [self.openshift_install, 'version'],
                capture_output=True,
                text=True
            )
            self.results.log_info(f"OpenShift Installer: {result.stdout.strip()}")
        except Exception as e:
            self.results.add_fail(f"openshift-install not found: {e}")
            return False

        # Run test cases
        self.test_case_1_invalid_schemes_and_spaces()
        self.test_case_2_network_overlap_and_invalid_noproxy()

        # Print summary
        return self.results.summary()


def main():
    """Main entry point"""
    test = ProxyValidationTest()
    success = test.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
