#!/usr/bin/env python3
"""
Test runner for KAFKA_CSA module test suite.

This script provides a comprehensive test runner for all KAFKA_CSA tests,
including individual test modules, full suite execution, and detailed reporting.

Features:
- Run individual test modules or complete suite
- Detailed test reporting and statistics
- Cross-platform compatibility
- Error handling and graceful failures
- Performance timing and metrics

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --module basic     # Run specific test module
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --quick            # Quick test mode (skip slow tests)

Author: Test Suite Generator
Date: 2025-07-23
"""

import unittest
import sys
import os
import argparse
import time
from pathlib import Path

# Add the parent directory to sys.path to import test modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Import all test modules
try:
    import test_basic
    import test_safe_functions
    import test_kpi_helper
    import test_main
    import test_kpi_csa
    import test_integration
    TEST_MODULES_AVAILABLE = True
    TEST_IMPORT_ERROR = None
except Exception as e:
    TEST_MODULES_AVAILABLE = False
    TEST_IMPORT_ERROR = str(e)


class CSATestRunner:
    """Main test runner for KAFKA_CSA module tests."""
    
    def __init__(self, verbose=False, quick=False):
        """Initialize the test runner."""
        self.verbose = verbose
        self.quick = quick
        self.test_modules = {
            'basic': test_basic,
            'safe_functions': test_safe_functions,
            'kpi_helper': test_kpi_helper,
            'main': test_main,
            'kpi_csa': test_kpi_csa,
            'integration': test_integration
        }
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_single_module(self, module_name):
        """Run tests for a single module."""
        if not TEST_MODULES_AVAILABLE:
            print(f"❌ Test modules not available: {TEST_IMPORT_ERROR}")
            return False
        
        if module_name not in self.test_modules:
            print(f"❌ Unknown test module: {module_name}")
            print(f"Available modules: {', '.join(self.test_modules.keys())}")
            return False
        
        print(f"\n{'='*60}")
        print(f"Running KAFKA_CSA {module_name} tests...")
        print(f"{'='*60}")
        
        module = self.test_modules[module_name]
        
        # Create test suite for the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=2 if self.verbose else 1,
            stream=sys.stdout,
            buffer=True
        )
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Store results
        self.results[module_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'duration': end_time - start_time,
            'successful': result.wasSuccessful()
        }
        
        # Print module summary
        self._print_module_summary(module_name, result, end_time - start_time)
        
        return result.wasSuccessful()
    
    def run_all_tests(self):
        """Run all test modules."""
        if not TEST_MODULES_AVAILABLE:
            print(f"❌ Test modules not available: {TEST_IMPORT_ERROR}")
            return False
        
        print(f"\n{'='*80}")
        print(f"KAFKA_CSA Complete Test Suite")
        print(f"{'='*80}")
        
        self.start_time = time.time()
        all_successful = True
        
        # Define test execution order (basic tests first, integration last)
        execution_order = ['basic', 'safe_functions', 'kpi_helper', 'main', 'kpi_csa', 'integration']
        
        for module_name in execution_order:
            if module_name in self.test_modules:
                # Skip slow tests in quick mode
                if self.quick and module_name == 'integration':
                    print(f"\n⏩ Skipping {module_name} tests (quick mode)")
                    continue
                
                success = self.run_single_module(module_name)
                if not success:
                    all_successful = False
                
                # Small delay between modules for readability
                time.sleep(0.1)
        
        self.end_time = time.time()
        
        # Print final summary
        self._print_final_summary()
        
        return all_successful
    
    def run_quick_tests(self):
        """Run a quick subset of tests for rapid feedback."""
        if not TEST_MODULES_AVAILABLE:
            print(f"❌ Test modules not available: {TEST_IMPORT_ERROR}")
            return False
        
        print(f"\n{'='*60}")
        print(f"KAFKA_CSA Quick Test Suite")
        print(f"{'='*60}")
        
        # Run only basic and safe function tests for quick feedback
        quick_modules = ['basic', 'safe_functions']
        all_successful = True
        
        for module_name in quick_modules:
            if module_name in self.test_modules:
                success = self.run_single_module(module_name)
                if not success:
                    all_successful = False
        
        return all_successful
    
    def _print_module_summary(self, module_name, result, duration):
        """Print summary for a single module."""
        status = "✅ PASSED" if result.wasSuccessful() else "❌ FAILED"
        
        print(f"\n{'-'*50}")
        print(f"Module: {module_name} - {status}")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Duration: {duration:.2f}s")
        
        if result.failures:
            print(f"\nFailures in {module_name}:")
            for test, traceback in result.failures:
                test_name = str(test).split()[0]
                error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
                print(f"  - {test_name}: {error_msg}")
        
        if result.errors:
            print(f"\nErrors in {module_name}:")
            for test, traceback in result.errors:
                test_name = str(test).split()[0]
                error_msg = traceback.split('Error: ')[-1].split('\n')[0] if 'Error: ' in traceback else 'Unknown error'
                print(f"  - {test_name}: {error_msg}")
    
    def _print_final_summary(self):
        """Print final comprehensive summary."""
        if not self.results:
            print("\n❌ No test results available")
            return
        
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        print(f"\n{'='*80}")
        print(f"KAFKA_CSA TEST SUITE FINAL SUMMARY")
        print(f"{'='*80}")
        
        # Calculate totals
        total_tests = sum(r['tests_run'] for r in self.results.values())
        total_failures = sum(r['failures'] for r in self.results.values())
        total_errors = sum(r['errors'] for r in self.results.values())
        total_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        modules_passed = sum(1 for r in self.results.values() if r['successful'])
        
        print(f"Total Modules: {len(self.results)}")
        print(f"Modules Passed: {modules_passed}")
        print(f"Modules Failed: {len(self.results) - modules_passed}")
        print(f"Total Tests: {total_tests}")
        print(f"Total Failures: {total_failures}")
        print(f"Total Errors: {total_errors}")
        print(f"Overall Success Rate: {total_success_rate:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Per-module breakdown
        print(f"\nPer-Module Results:")
        print(f"{'Module':<15} {'Tests':<6} {'Fails':<6} {'Errors':<7} {'Rate':<8} {'Time':<8} {'Status'}")
        print(f"{'-'*70}")
        
        for module_name, result in self.results.items():
            status = "PASS" if result['successful'] else "FAIL"
            print(f"{module_name:<15} {result['tests_run']:<6} {result['failures']:<6} "
                  f"{result['errors']:<7} {result['success_rate']:<7.1f}% {result['duration']:<7.2f}s {status}")
        
        # Final status
        overall_success = all(r['successful'] for r in self.results.values())
        final_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
        print(f"\n{final_status}")
        
        # Recommendations
        if not overall_success:
            print(f"\n📋 Recommendations:")
            failed_modules = [name for name, result in self.results.items() if not result['successful']]
            print(f"• Review failed modules: {', '.join(failed_modules)}")
            print(f"• Check error details above for specific issues")
            print(f"• Consider running individual modules for detailed debugging")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description='KAFKA_CSA Test Suite Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --module basic     # Run basic tests only
  python run_tests.py --verbose          # Verbose output
  python run_tests.py --quick            # Quick test mode
  python run_tests.py --list-modules     # List available modules
        """
    )
    
    parser.add_argument(
        '--module', '-m',
        help='Run tests for specific module only',
        choices=['basic', 'safe_functions', 'kpi_helper', 'main', 'kpi_csa', 'integration']
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose test output'
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Run quick tests only (skips integration tests)'
    )
    
    parser.add_argument(
        '--list-modules', '-l',
        action='store_true',
        help='List available test modules'
    )
    
    args = parser.parse_args()
    
    # Handle list modules request
    if args.list_modules:
        print("Available test modules:")
        modules = ['basic', 'safe_functions', 'kpi_helper', 'main', 'kpi_csa', 'integration']
        for module in modules:
            print(f"  • {module}")
        return 0
    
    # Create test runner
    runner = CSATestRunner(verbose=args.verbose, quick=args.quick)
    
    # Execute tests based on arguments
    try:
        if args.module:
            success = runner.run_single_module(args.module)
        elif args.quick:
            success = runner.run_quick_tests()
        else:
            success = runner.run_all_tests()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
