#!/usr/bin/env python3
"""
Simple Robot Framework test runner for the five modules: KAFKA_UAF, NFS_DISK_STATUS_CHECK, 
POD_FILE_COLLECTOR, POD_FILE_SENDER, and SDP_STAT.

Compatible with Python 3.6+ and provides basic test execution functionality.
"""

import os
import sys
import subprocess
import argparse
import datetime
import json
from pathlib import Path
import platform

class SimpleRobotTestRunner:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root)
        self.target_modules = [
            'KAFKA_UAF', 
            'NFS_DISK_STATUS_CHECK', 
            'POD_FILE_COLLECTOR', 
            'POD_FILE_SENDER', 
            'SDP_STAT'
        ]
        self.results_dir = self.workspace_root / 'robot_test_results'
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_results_directory(self):
        """Create results directory structure."""
        self.current_results_dir = self.results_dir / f"run_{self.timestamp}"
        self.current_results_dir.mkdir(parents=True, exist_ok=True)
        
        for module in self.target_modules:
            (self.current_results_dir / module).mkdir(exist_ok=True)
            
        print(f"📁 Results will be stored in: {self.current_results_dir}")
        
    def validate_environment(self):
        """Validate test environment prerequisites."""
        print("🔍 Validating test environment...")
        
        # Check Robot Framework installation
        try:
            result = subprocess.run(['robot', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                print(f"✅ Robot Framework found: {result.stdout.strip()}")
            else:
                print("❌ Robot Framework not found")
                print("   Install with: pip install robotframework")
                return False
        except FileNotFoundError:
            print("❌ Robot Framework not found")
            print("   Install with: pip install robotframework")
            return False
                
        # Check module directories and test files
        missing_modules = []
        missing_tests = []
        
        for module in self.target_modules:
            module_dir = self.workspace_root / module
            if not module_dir.exists():
                missing_modules.append(module)
                continue
                
            tests_dir = module_dir / 'tests'
            if not tests_dir.exists():
                missing_tests.append(f"{module}/tests")
                continue
                
            # Check for test files
            test_files = list(tests_dir.glob("*tests.robot")) + list(tests_dir.glob("*test.robot"))
            if not test_files:
                missing_tests.append(f"{module}/tests/*.robot")
                
        if missing_modules:
            print(f"❌ Missing module directories: {', '.join(missing_modules)}")
            return False
        else:
            print("✅ All module directories found")
            
        if missing_tests:
            print(f"❌ Missing test files: {', '.join(missing_tests)}")
            return False
        else:
            print("✅ All test files found")
            
        print("✅ Environment validation passed!")
        return True
        
    def get_test_files(self, module):
        """Get test files for a module."""
        tests_dir = self.workspace_root / module / 'tests'
        test_files = []
        
        # Look for various test file patterns
        patterns = ['*tests.robot', '*test.robot', f'{module.lower()}*.robot']
        for pattern in patterns:
            test_files.extend(tests_dir.glob(pattern))
            
        return list(set(test_files))  # Remove duplicates
        
    def run_module_tests(self, module, tags=None, exclude_tags=None):
        """Run tests for a specific module."""
        print(f"\n🧪 Running tests for {module}...")
        
        test_files = self.get_test_files(module)
        if not test_files:
            print(f"❌ No test files found for {module}")
            return False
            
        module_results_dir = self.current_results_dir / module
        
        # Prepare robot command
        cmd = [
            'robot',
            '--outputdir', str(module_results_dir),
            '--name', f"{module}_Tests",
            '--log', f"{module}_log.html",
            '--report', f"{module}_report.html",
            '--output', f"{module}_output.xml",
            '--loglevel', 'INFO'
        ]
        
        # Add tag filters
        if tags:
            for tag in tags:
                cmd.extend(['--include', tag])
                
        if exclude_tags:
            for tag in exclude_tags:
                cmd.extend(['--exclude', tag])
                
        # Add all test files
        for test_file in test_files:
            cmd.append(str(test_file))
            
        print(f"   Command: robot --outputdir {module_results_dir} ...")
        
        try:
            start_time = datetime.datetime.now()
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            
            # Save execution details
            execution_details = {
                'module': module,
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': str(duration),
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            with open(module_results_dir / "execution_details.json", 'w') as f:
                json.dump(execution_details, f, indent=2)
                
            with open(module_results_dir / "command_output.txt", 'w') as f:
                f.write(f"Module: {module}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write(f"Duration: {duration}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
                
            if result.returncode == 0:
                print(f"✅ {module} tests completed successfully ({duration})")
                return True
            else:
                print(f"❌ {module} tests failed with return code {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}...")
                return False
                
        except FileNotFoundError:
            print(f"❌ Robot Framework not found")
            return False
        except Exception as e:
            print(f"❌ Error running tests for {module}: {e}")
            return False
            
    def run_all_tests(self, tags=None, exclude_tags=None, modules=None):
        """Run tests for all or specified modules."""
        test_modules = modules if modules else self.target_modules
        results = {}
        
        print(f"🚀 Starting test execution for modules: {', '.join(test_modules)}")
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
        
        self.generate_summary_report(results, start_time, end_time, total_duration)
        return results
        
    def generate_summary_report(self, results, start_time, end_time, total_duration):
        """Generate comprehensive summary report."""
        successful_modules = [m for m, r in results.items() if r['success']]
        failed_modules = [m for m, r in results.items() if not r['success']]
        
        summary = {
            'execution_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration': str(total_duration),
                'modules_tested': len(results),
                'successful_modules': len(successful_modules),
                'failed_modules': len(failed_modules),
                'success_rate': f"{len(successful_modules)/len(results)*100:.1f}%" if results else "0%",
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'timestamp': self.timestamp
            },
            'successful_modules': successful_modules,
            'failed_modules': failed_modules,
            'module_results': results
        }
        
        # Save JSON summary
        summary_file = self.current_results_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        # Save human-readable summary
        text_summary_file = self.current_results_dir / "test_summary.txt"
        with open(text_summary_file, 'w') as f:
            f.write("🤖 Robot Framework Test Execution Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"📅 Execution Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"⏱️  Total Duration: {total_duration}\n")
            f.write(f"🧪 Modules Tested: {len(results)}\n")
            f.write(f"✅ Successful: {len(successful_modules)}\n")
            f.write(f"❌ Failed: {len(failed_modules)}\n")
            f.write(f"📊 Success Rate: {summary['execution_summary']['success_rate']}\n")
            f.write(f"💻 Platform: {platform.platform()}\n")
            f.write(f"🐍 Python: {platform.python_version()}\n\n")
            
            f.write("📋 Module Results:\n")
            f.write("-" * 40 + "\n")
            for module, result in results.items():
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                duration = result.get('duration', 'N/A')
                f.write(f"{module:20} {status} ({duration})\n")
                
            if failed_modules:
                f.write(f"\n❌ Failed Modules: {', '.join(failed_modules)}\n")
            else:
                f.write(f"\n🎉 All tests passed successfully!\n")
                
        # Print summary
        print(f"\n{'='*60}")
        print(f"🏁 Test execution completed!")
        print(f"⏱️  Duration: {total_duration}")
        print(f"📊 Success Rate: {summary['execution_summary']['success_rate']}")
        print(f"✅ Successful: {len(successful_modules)}")
        print(f"❌ Failed: {len(failed_modules)}")
        print(f"📁 Summary saved to: {text_summary_file}")
        print(f"📁 Detailed results in: {self.current_results_dir}")
        print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(
        description="Simple Robot Framework test runner for KAFKA_UAF, NFS_DISK_STATUS_CHECK, POD_FILE_COLLECTOR, POD_FILE_SENDER, and SDP_STAT modules"
    )
    
    parser.add_argument('--workspace', default='.', help='Workspace root directory (default: current directory)')
    parser.add_argument('--modules', nargs='+', 
                       choices=['KAFKA_UAF', 'NFS_DISK_STATUS_CHECK', 'POD_FILE_COLLECTOR', 'POD_FILE_SENDER', 'SDP_STAT'], 
                       help='Specific modules to test')
    parser.add_argument('--tags', nargs='+', help='Include tests with these tags')
    parser.add_argument('--exclude-tags', nargs='+', help='Exclude tests with these tags')
    parser.add_argument('--validate-only', action='store_true', help='Only validate environment')
    
    args = parser.parse_args()
    
    # Convert workspace to absolute path
    workspace_root = os.path.abspath(args.workspace)
    runner = SimpleRobotTestRunner(workspace_root)
    
    print("🤖 Robot Framework Test Runner for CEC Adaptation Pod")
    print("=" * 60)
    print(f"📁 Workspace: {workspace_root}")
    print(f"🎯 Target modules: {', '.join(runner.target_modules)}")
    
    # Validate environment
    if not runner.validate_environment():
        print("❌ Environment validation failed. Please fix the issues and try again.")
        sys.exit(1)
        
    if args.validate_only:
        print("✅ Environment validation passed!")
        sys.exit(0)
        
    # Setup results directory
    runner.setup_results_directory()
    
    # Run tests
    results = runner.run_all_tests(
        tags=args.tags,
        exclude_tags=args.exclude_tags,
        modules=args.modules
    )
    
    # Exit with appropriate code
    failed_modules = [module for module, result in results.items() if not result['success']]
    if failed_modules:
        print(f"\n❌ Tests failed for modules: {', '.join(failed_modules)}")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
