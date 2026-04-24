#!/usr/bin/env python3
"""
Test Case: OCP-35198
Description: Test OpenShift installation with GCP custom machine types (good and bad)
References:
  - https://bugzilla.redhat.com/show_bug.cgi?id=1878108
  - https://bugzilla.redhat.com/show_bug.cgi?id=1898194
  - https://bugzilla.redhat.com/show_bug.cgi?id=1898713
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TestResult(Enum):
    """Test result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


class Colors:
    """ANSI color codes"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


@dataclass
class TestCase:
    """Test case definition"""
    machine_type: str
    expected_result: str  # "pass" or "fail"
    expected_error_pattern: Optional[str] = None
    description: str = ""
    bugzilla_ref: Optional[str] = None


@dataclass
class TestRunResult:
    """Individual test run result"""
    test_name: str
    machine_type: str
    result: TestResult
    expected: str
    actual: str
    error_message: Optional[str] = None
    validation_output: Optional[str] = None


class GCPCustomTypeTest:
    """Main test class for GCP custom machine type validation"""

    def __init__(self, config: Dict):
        self.config = config
        self.work_dir = Path(config.get('work_dir', '/tmp/ocp-35198-test'))
        self.openshift_install = config.get('openshift_install', 'openshift-install')
        self.project_id = config.get('project_id', '')
        self.region = config.get('region', 'us-west1')
        self.zone = config.get('zone', 'us-west1-b')
        self.base_domain = config.get('base_domain', 'example.com')
        self.cluster_name = config.get('cluster_name', 'test-cluster')
        self.pull_secret_file = config.get('pull_secret_file',
                                          os.path.expanduser('~/.openshift/pull-secret.json'))
        self.ssh_key = config.get('ssh_key',
                                 os.path.expanduser('~/.ssh/id_rsa.pub'))

        self.results: List[TestRunResult] = []

    def log(self, level: str, message: str, color: str = Colors.NC):
        """Log a message with color"""
        print(f"{color}[{level}]{Colors.NC} {message}")

    def setup(self):
        """Setup test environment"""
        self.log("INFO", "Setting up test environment...", Colors.BLUE)

        # Create work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Verify openshift-install is available
        if not shutil.which(self.openshift_install):
            self.log("ERROR", f"{self.openshift_install} not found in PATH", Colors.RED)
            return False

        # Check for pull secret
        if not os.path.exists(self.pull_secret_file):
            self.log("WARN", f"Pull secret not found at {self.pull_secret_file}", Colors.YELLOW)

        # Check for SSH key
        if not os.path.exists(self.ssh_key):
            self.log("WARN", f"SSH key not found at {self.ssh_key}", Colors.YELLOW)

        return True

    def cleanup(self):
        """Cleanup test directories"""
        self.log("INFO", "Cleaning up test directories...", Colors.BLUE)
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

    def generate_install_config(self, machine_type: str, test_dir: Path) -> Path:
        """Generate install-config.yaml with specified machine type"""
        test_dir.mkdir(parents=True, exist_ok=True)
        config_file = test_dir / "install-config.yaml"

        # Read pull secret
        pull_secret = "''"
        if os.path.exists(self.pull_secret_file):
            with open(self.pull_secret_file, 'r') as f:
                pull_secret = f"'{f.read().strip()}'"

        # Read SSH key
        ssh_key = "''"
        if os.path.exists(self.ssh_key):
            with open(self.ssh_key, 'r') as f:
                ssh_key = f"'{f.read().strip()}'"

        config_content = f"""apiVersion: v1
baseDomain: {self.base_domain}
compute:
- architecture: amd64
  hyperthreading: Enabled
  name: worker
  platform:
    gcp:
      type: {machine_type}
  replicas: 3
controlPlane:
  architecture: amd64
  hyperthreading: Enabled
  name: master
  platform:
    gcp:
      type: {machine_type}
  replicas: 3
metadata:
  name: {self.cluster_name}
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
    projectID: {self.project_id}
    region: {self.region}
publish: External
pullSecret: {pull_secret}
sshKey: {ssh_key}
"""

        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    def test_machine_type(self, test_case: TestCase) -> TestRunResult:
        """Test a specific machine type"""
        test_name = f"Machine type: {test_case.machine_type}"
        self.log("INFO", f"Testing: {test_name}", Colors.BLUE)

        # Create test directory
        test_dir = self.work_dir / test_case.machine_type.replace('/', '_')

        # Generate install config
        config_file = self.generate_install_config(test_case.machine_type, test_dir)

        # Run validation
        output_file = test_dir / "validation_output.txt"

        try:
            # Set up environment variables for openshift-install
            env = os.environ.copy()
            env['OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE'] = os.getenv(
                'OPENSHIFT_INSTALL_RELEASE_IMAGE_OVERRIDE',
                'quay.io/openshift-release-dev/ocp-release:4.22.0-ec.5-x86_64'
            )
            env['OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY'] = os.getenv(
                'OPENSHIFT_INSTALL_EXPERIMENTAL_DISABLE_IMAGE_POLICY',
                'true'
            )

            result = subprocess.run(
                [self.openshift_install, 'create', 'manifests', f'--dir={test_dir}'],
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            exit_code = result.returncode
            validation_output = result.stdout + result.stderr

            with open(output_file, 'w') as f:
                f.write(validation_output)

        except subprocess.TimeoutExpired:
            validation_output = "Command timed out after 300 seconds"
            exit_code = 1
        except Exception as e:
            validation_output = f"Exception occurred: {str(e)}"
            exit_code = 1

        # Determine result
        if test_case.expected_result == "pass":
            if exit_code == 0:
                result_enum = TestResult.PASS
                actual = "passed"
                error_msg = None
                self.log("PASS", f"{test_name} - Validation succeeded as expected", Colors.GREEN)
            else:
                result_enum = TestResult.FAIL
                actual = "failed"
                error_msg = validation_output[-500:] if len(validation_output) > 500 else validation_output
                self.log("FAIL", f"{test_name} - Expected success but got error", Colors.RED)
        else:
            # Expected to fail
            if exit_code != 0:
                # Check if error message matches expected pattern
                if test_case.expected_error_pattern:
                    import re
                    if re.search(test_case.expected_error_pattern, validation_output, re.IGNORECASE):
                        result_enum = TestResult.PASS
                        actual = "failed with expected error"
                        error_msg = None
                        self.log("PASS",
                                f"{test_name} - Failed with expected error: {test_case.expected_error_pattern}",
                                Colors.GREEN)
                    else:
                        result_enum = TestResult.FAIL
                        actual = "failed with unexpected error"
                        error_msg = f"Expected pattern: {test_case.expected_error_pattern}"
                        self.log("FAIL",
                                f"{test_name} - Failed but error message didn't match expected pattern",
                                Colors.RED)
                else:
                    result_enum = TestResult.PASS
                    actual = "failed"
                    error_msg = None
                    self.log("PASS", f"{test_name} - Failed as expected", Colors.GREEN)
            else:
                result_enum = TestResult.FAIL
                actual = "passed"
                error_msg = "Expected failure but validation succeeded"
                self.log("FAIL", f"{test_name} - {error_msg}", Colors.RED)

        return TestRunResult(
            test_name=test_name,
            machine_type=test_case.machine_type,
            result=result_enum,
            expected=test_case.expected_result,
            actual=actual,
            error_message=error_msg,
            validation_output=validation_output
        )

    def get_test_cases(self) -> List[TestCase]:
        """Define all test cases"""
        return [
            # Good custom types (should pass)
            TestCase("n1-standard-4", "pass",
                    description="Standard GCP machine type"),
            TestCase("custom-4-16384", "pass",
                    description="Custom type with 4 vCPUs and 16GB RAM"),
            TestCase("n1-custom-4-16384", "pass",
                    description="N1 custom type with 4 vCPUs and 16GB RAM",
                    bugzilla_ref="1898713"),

            # Bad types - 404 Not Found
            TestCase("n1-dne-4", "fail", "Error 404.*not found",
                    description="Non-existent machine type"),
            TestCase("custom-2", "fail", "Error 404.*not found",
                    description="Incomplete custom type specification"),
            TestCase("custom-a", "fail", "Error 404.*not found",
                    description="Invalid custom type with letter"),
            TestCase("custom-2-b", "fail", "Error 404.*not found",
                    description="Invalid custom type with letter in memory"),
            TestCase("n1-custom-2", "fail", "Error 404.*not found",
                    description="Incomplete n1-custom type"),
            TestCase("n1-custom-a", "fail", "Error 404.*not found",
                    description="Invalid n1-custom type with letter"),
            TestCase("n1-custom-2-b", "fail", "Error 404.*not found",
                    description="Invalid n1-custom type with letter in memory"),

            # Bad types - Invalid Resource Usage
            TestCase("custom-4-16383", "fail", "Memory should be a multiple of 256",
                    description="Memory not multiple of 256MiB"),
            TestCase("n1-custom-4-16383", "fail", "Memory should be a multiple of 256",
                    description="N1 memory not multiple of 256MiB"),
            TestCase("custom-3-16384", "fail", "Number of vCPUs should be multiple of 2",
                    description="vCPUs not multiple of 2"),
            TestCase("n1-custom-3-16384", "fail", "Number of vCPUs should be multiple of 2",
                    description="N1 vCPUs not multiple of 2"),

            # Invalid memory and CPU (below minimum requirements)
            TestCase("n1-standard-2", "fail", "does not meet minimum resource requirements of 4 vCPUs",
                    description="Below minimum 4 vCPUs requirement"),
            TestCase("custom-2-7680", "fail", "does not meet minimum resource requirements",
                    description="Below minimum vCPU and memory requirements"),
            TestCase("n1-custom-2-7680", "fail", "does not meet minimum resource requirements",
                    description="N1 below minimum vCPU and memory requirements"),
        ]

    def run_tests(self) -> bool:
        """Run all test cases"""
        self.log("INFO", "=" * 50, Colors.BLUE)
        self.log("INFO", "OCP-35198: GCP Custom Machine Type Tests", Colors.BLUE)
        self.log("INFO", "=" * 50, Colors.BLUE)
        print()

        if not self.setup():
            return False

        test_cases = self.get_test_cases()

        # Group tests
        good_types = [tc for tc in test_cases if tc.expected_result == "pass"]
        bad_404 = [tc for tc in test_cases if "404" in str(tc.expected_error_pattern)]
        bad_400 = [tc for tc in test_cases if "multiple" in str(tc.expected_error_pattern)]
        bad_min = [tc for tc in test_cases if "minimum resource" in str(tc.expected_error_pattern)]

        # Run test groups
        self.log("INFO", "=== Test Group 1: Valid Custom Types ===", Colors.BLUE)
        for tc in good_types:
            result = self.test_machine_type(tc)
            self.results.append(result)
        print()

        self.log("INFO", "=== Test Group 2: Non-existent Machine Types (404) ===", Colors.BLUE)
        for tc in bad_404:
            result = self.test_machine_type(tc)
            self.results.append(result)
        print()

        self.log("INFO", "=== Test Group 3: Invalid Resource Usage (400) ===", Colors.BLUE)
        for tc in bad_400:
            result = self.test_machine_type(tc)
            self.results.append(result)
        print()

        self.log("INFO", "=== Test Group 4: Below Minimum Requirements ===", Colors.BLUE)
        for tc in bad_min:
            result = self.test_machine_type(tc)
            self.results.append(result)
        print()

        return self.print_summary()

    def print_summary(self) -> bool:
        """Print test summary"""
        passed = sum(1 for r in self.results if r.result == TestResult.PASS)
        failed = sum(1 for r in self.results if r.result == TestResult.FAIL)

        self.log("INFO", "=" * 50, Colors.BLUE)
        self.log("INFO", "Test Summary", Colors.BLUE)
        self.log("INFO", "=" * 50, Colors.BLUE)
        self.log("INFO", f"Total Passed: {passed}", Colors.GREEN if failed == 0 else Colors.BLUE)
        self.log("INFO", f"Total Failed: {failed}", Colors.RED if failed > 0 else Colors.BLUE)

        if failed > 0:
            self.log("ERROR", "Failed tests:", Colors.RED)
            for result in self.results:
                if result.result == TestResult.FAIL:
                    print(f"  - {result.test_name}")
                    if result.error_message:
                        print(f"    Error: {result.error_message}")
            print()
            self.log("ERROR", "Overall result: FAILED", Colors.RED)
            return False
        else:
            self.log("PASS", "Overall result: PASSED", Colors.GREEN)
            return True

    def export_results(self, output_file: str):
        """Export results to JSON file"""
        results_dict = {
            'test_case': 'OCP-35198',
            'description': 'GCP Custom Machine Type Tests',
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r.result == TestResult.PASS),
            'failed': sum(1 for r in self.results if r.result == TestResult.FAIL),
            'results': [
                {
                    'test_name': r.test_name,
                    'machine_type': r.machine_type,
                    'result': r.result.value,
                    'expected': r.expected,
                    'actual': r.actual,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2)

        self.log("INFO", f"Results exported to {output_file}", Colors.BLUE)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test OCP-35198: GCP Custom Machine Type validation'
    )
    parser.add_argument('--work-dir', default='/tmp/ocp-35198-test',
                       help='Working directory for test files')
    parser.add_argument('--project-id', required=False,
                       help='GCP project ID')
    parser.add_argument('--region', default='us-west1',
                       help='GCP region')
    parser.add_argument('--zone', default='us-west1-b',
                       help='GCP zone')
    parser.add_argument('--base-domain', default='example.com',
                       help='Base domain for cluster')
    parser.add_argument('--cluster-name', default='test-cluster',
                       help='Cluster name')
    parser.add_argument('--openshift-install', default='openshift-install',
                       help='Path to openshift-install binary')
    parser.add_argument('--pull-secret',
                       default=os.path.expanduser('~/.openshift/pull-secret.json'),
                       help='Path to pull secret file')
    parser.add_argument('--ssh-key',
                       default=os.path.expanduser('~/.ssh/id_rsa.pub'),
                       help='Path to SSH public key')
    parser.add_argument('--export-json',
                       help='Export results to JSON file')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Do not cleanup test directories')

    args = parser.parse_args()

    config = {
        'work_dir': args.work_dir,
        'project_id': args.project_id or os.getenv('GCP_PROJECT_ID', ''),
        'region': args.region,
        'zone': args.zone,
        'base_domain': args.base_domain,
        'cluster_name': args.cluster_name,
        'openshift_install': args.openshift_install,
        'pull_secret_file': args.pull_secret,
        'ssh_key': args.ssh_key,
    }

    tester = GCPCustomTypeTest(config)

    try:
        success = tester.run_tests()

        if args.export_json:
            tester.export_results(args.export_json)

        sys.exit(0 if success else 1)

    finally:
        if not args.no_cleanup:
            tester.cleanup()


if __name__ == '__main__':
    main()
