#!/usr/bin/env python3
"""
Comprehensive test runner for cec-adaptation-pod Robot Framework test suites.
This script runs all test suites for BACKUP_POD, AIR_STAT, CDRS_TRANSFER, KAFKA_UAF, 
NFS_DISK_STATUS_CHECK, POD_FILE_COLLECTOR, POD_FILE_SENDER, and SDP_STAT modules.
"""

import os
import sys
import subprocess
import argparse
import datetime
import json
from pathlib import Path

class TestRunner:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root)
        self.modules = [
            'BACKUP_POD', 'AIR_STAT', 'CDRS_TRANSFER', 'KAFKA_UAF', 
            'NFS_DISK_STATUS_CHECK', 'POD_FILE_COLLECTOR', 'POD_FILE_SENDER', 'SDP_STAT'
        ]
        self.results_dir = self.workspace_root / 'test_results'
        
    def setup_results_directory(self):
        """Create results directory structure."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_results_dir = self.results_dir / f"run_{timestamp}"
        self.current_results_dir.mkdir(parents=True, exist_ok=True)
        
        for module in self.modules:
            (self.current_results_dir / module).mkdir(exist_ok=True)
            
        print(f"Results will be stored in: {self.current_results_dir}")
        
    def run_module_tests(self, module, tags=None, exclude_tags=None):
        """Run tests for a specific module."""
        module_dir = self.workspace_root / module
        tests_dir = module_dir / 'tests'
        
        if not tests_dir.exists():
            print(f"Warning: Tests directory not found for {module}")
            return False
            
        test_file = tests_dir / f"{module.lower()}_tests.robot"
        if not test_file.exists():
            print(f"Warning: Test file not found for {module}: {test_file}")
            return False
            
        # Prepare robot command
        cmd = [
            'robot',
            '--outputdir', str(self.current_results_dir / module),
            '--name', f"{module}_Tests",
            '--log', f"{module}_log.html",
            '--report', f"{module}_report.html",
            '--output', f"{module}_output.xml"
        ]
        
        if tags:
            for tag in tags:
                cmd.extend(['--include', tag])
                
        if exclude_tags:
            for tag in exclude_tags:
                cmd.extend(['--exclude', tag])
                
        cmd.append(str(test_file))
        
        print(f"\nRunning tests for {module}...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tests_dir))
            
            # Save command output
            with open(self.current_results_dir / module / "command_output.txt", 'w') as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
                
            if result.returncode == 0:
                print(f"✓ {module} tests completed successfully")
            else:
                print(f"✗ {module} tests failed with return code {result.returncode}")
                
            return result.returncode == 0
            
        except FileNotFoundError:
            print(f"Error: Robot Framework not found. Please install robot framework.")
            print("Install with: pip install robotframework")
            return False
        except Exception as e:
            print(f"Error running tests for {module}: {e}")
            return False
            
    def run_all_tests(self, tags=None, exclude_tags=None, modules=None):
        """Run tests for all or specified modules."""
        self.setup_results_directory()
        
        test_modules = modules if modules else self.modules
        results = {}
        
        print(f"Starting test execution for modules: {', '.join(test_modules)}")
        start_time = datetime.datetime.now()
        
        for module in test_modules:
            module_start = datetime.datetime.now()
            success = self.run_module_tests(module, tags, exclude_tags)
            module_end = datetime.datetime.now()
            
            results[module] = {
                'success': success,
                'duration': str(module_end - module_start),
                'start_time': module_start.isoformat(),
                'end_time': module_end.isoformat()
            }
            
        end_time = datetime.datetime.now()
        total_duration = end_time - start_time
        
        # Generate summary report
        self.generate_summary_report(results, start_time, end_time, total_duration)
        
        return results
        
    def generate_summary_report(self, results, start_time, end_time, total_duration):
        """Generate a summary report of all test executions."""
        summary = {
            'execution_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration': str(total_duration),
                'modules_tested': len(results),
                'successful_modules': sum(1 for r in results.values() if r['success']),
                'failed_modules': sum(1 for r in results.values() if not r['success'])
            },
            'module_results': results
        }
        
        # Save JSON summary
        summary_file = self.current_results_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        # Save human-readable summary
        text_summary_file = self.current_results_dir / "test_summary.txt"
        with open(text_summary_file, 'w') as f:
            f.write("CEC Adaptation Pod - Test Execution Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Execution Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {total_duration}\n")
            f.write(f"Modules Tested: {len(results)}\n")
            f.write(f"Successful: {summary['execution_summary']['successful_modules']}\n")
            f.write(f"Failed: {summary['execution_summary']['failed_modules']}\n\n")
            
            f.write("Module Results:\n")
            f.write("-" * 30 + "\n")
            for module, result in results.items():
                status = "PASS" if result['success'] else "FAIL"
                f.write(f"{module:15} {status:4} ({result['duration']})\n")
                
        print(f"\nTest execution completed!")
        print(f"Summary saved to: {text_summary_file}")
        print(f"Detailed results in: {self.current_results_dir}")
        
    def validate_environment(self):
        """Validate test environment prerequisites."""
        print("Validating test environment...")
        
        # Check Robot Framework installation
        try:
            subprocess.run(['robot', '--version'], capture_output=True, check=True)
            print("✓ Robot Framework found")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("✗ Robot Framework not found")
            return False
            
        # Check module directories
        missing_modules = []
        for module in self.modules:
            module_dir = self.workspace_root / module
            if not module_dir.exists():
                missing_modules.append(module)
                
        if missing_modules:
            print(f"✗ Missing module directories: {', '.join(missing_modules)}")
            return False
        else:
            print("✓ All module directories found")
            
        # Check test files
        missing_tests = []
        for module in self.modules:
            test_file = self.workspace_root / module / 'tests' / f"{module.lower()}_tests.robot"
            if not test_file.exists():
                missing_tests.append(f"{module}/{test_file.name}")
                
        if missing_tests:
            print(f"✗ Missing test files: {', '.join(missing_tests)}")
            return False
        else:
            print("✓ All test files found")
            
        print("Environment validation passed!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Run Robot Framework tests for cec-adaptation-pod modules")
    parser.add_argument('--workspace', default='.', help='Workspace root directory')
    parser.add_argument('--modules', nargs='+', 
                       choices=['BACKUP_POD', 'AIR_STAT', 'CDRS_TRANSFER', 'KAFKA_UAF', 
                               'NFS_DISK_STATUS_CHECK', 'POD_FILE_COLLECTOR', 'POD_FILE_SENDER', 'SDP_STAT'], 
                       help='Specific modules to test')
    parser.add_argument('--tags', nargs='+', help='Include tests with these tags')
    parser.add_argument('--exclude-tags', nargs='+', help='Exclude tests with these tags')
    parser.add_argument('--validate-only', action='store_true', help='Only validate environment')
    
    args = parser.parse_args()
    
    # Convert workspace to absolute path
    workspace_root = os.path.abspath(args.workspace)
    runner = TestRunner(workspace_root)
    
    # Validate environment
    if not runner.validate_environment():
        print("Environment validation failed. Please fix the issues and try again.")
        sys.exit(1)
        
    if args.validate_only:
        print("Environment validation passed!")
        sys.exit(0)
        
    # Run tests
    results = runner.run_all_tests(
        tags=args.tags,
        exclude_tags=args.exclude_tags,
        modules=args.modules
    )
    
    # Exit with appropriate code
    failed_modules = [module for module, result in results.items() if not result['success']]
    if failed_modules:
        print(f"\nTests failed for modules: {', '.join(failed_modules)}")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
