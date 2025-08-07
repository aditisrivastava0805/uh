#!/usr/bin/env python3
"""
Test Runner for KAFKA_SDP_POSTPAID Module

This script runs all test suites for the KAFKA_SDP_POSTPAID module and provides
a comprehensive test report.

Usage:
    python run_tests.py
    python run_tests.py --verbose
    python run_tests.py --test-file test_basic.py
"""

import unittest
import sys
import os
import argparse
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test modules
TEST_MODULES = [
    'test_basic',
    'test_safe_functions', 
    'test_main',
    'test_kpi_sdp',
    'test_logger_subprocess',
    'test_integration'
]


def run_single_test_file(test_file, verbose=False):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    try:
        # Import the test module
        test_module = __import__(test_file)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests
        verbosity = 2 if verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
        result = runner.run(suite)
        
        return {
            'module': test_file,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success': result.wasSuccessful()
        }
        
    except ImportError as e:
        print(f"⚠️ Could not import {test_file}: {e}")
        return {
            'module': test_file,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'skipped': 0,
            'success': False,
            'import_error': str(e)
        }
    except Exception as e:
        print(f"⚠️ Error running {test_file}: {e}")
        return {
            'module': test_file,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'skipped': 0,
            'success': False,
            'error': str(e)
        }


def run_all_tests(verbose=False, specific_test=None):
    """Run all test modules"""
    start_time = datetime.now()
    
    print("🧪 KAFKA_SDP_POSTPAID Test Suite")
    print("=" * 80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if specific_test:
        # Run only the specified test
        test_modules = [specific_test.replace('.py', '')]
    else:
        test_modules = TEST_MODULES
    
    results = []
    
    for test_module in test_modules:
        result = run_single_test_file(test_module, verbose)
        results.append(result)
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = sum(r['tests_run'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_skipped = sum(r['skipped'] for r in results)
    total_success = sum(1 for r in results if r['success'])
    
    print(f"Duration: {duration}")
    print(f"Test modules run: {len(results)}")
    print(f"Successful modules: {total_success}/{len(results)}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failed: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    
    # Detailed results per module
    print(f"\n{'='*80}")
    print("DETAILED RESULTS")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['module']:<25} "
              f"Tests: {result['tests_run']:>3} "
              f"Failures: {result['failures']:>2} "
              f"Errors: {result['errors']:>2} "
              f"Skipped: {result['skipped']:>2}")
        
        if 'import_error' in result:
            print(f"     Import Error: {result['import_error']}")
        elif 'error' in result:
            print(f"     Error: {result['error']}")
    
    # Overall status
    overall_success = all(r['success'] for r in results)
    print(f"\n{'='*80}")
    if overall_success:
        print("🎉 ALL TESTS PASSED!")
        return_code = 0
    else:
        print("💥 SOME TESTS FAILED!")
        return_code = 1
    
    print(f"{'='*80}")
    
    return return_code


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run KAFKA_SDP_POSTPAID tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Run tests in verbose mode')
    parser.add_argument('--test-file', '-t', type=str,
                       help='Run specific test file (e.g., test_basic.py)')
    
    args = parser.parse_args()
    
    return_code = run_all_tests(verbose=args.verbose, specific_test=args.test_file)
    sys.exit(return_code)


if __name__ == '__main__':
    main()
