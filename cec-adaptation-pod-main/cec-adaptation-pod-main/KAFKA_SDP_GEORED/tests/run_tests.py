#!/usr/bin/env python3
"""
KAFKA_SDP_GEORED Test Runner
Comprehensive test execution script for KAFKA_SDP_GEORED module.
"""

import os
import sys
import unittest
import time
from datetime import datetime

def print_header(title):
    """Print a formatted header."""
    print("=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "-" * 60)
    print(f"🔍 {title}")
    print("-" * 60)

def run_test_suite(test_module_name, description):
    """Run a specific test suite and return results."""
    print_section(f"Running {test_module_name}")
    
    try:
        # Import the test module
        test_module = __import__(test_module_name)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        result = runner.run(suite)
        
        return {
            'module': test_module_name,
            'description': description,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'success': result.wasSuccessful()
        }
        
    except Exception as e:
        print(f"❌ Error running {test_module_name}: {str(e)}")
        return {
            'module': test_module_name,
            'description': description,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'skipped': 0,
            'success': False,
            'error': str(e)
        }

def main():
    """Main test execution function."""
    print_header("KAFKA_SDP_GEORED Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_header("")
    
    # Test modules to run
    test_modules = [
        ('test_basic', 'Basic functionality and import tests'),
        ('test_safe_functions', 'Safe function tests without complex mocking'),
        ('test_main', 'Main module tests with mocking'),
        ('test_kpi_sdp', 'KPI_SDP class tests'),
        ('test_logger_subprocess', 'Logger and SubprocessClass tests'),
        ('test_integration', 'Integration testing scenarios')
    ]
    
    results = []
    start_time = time.time()
    
    # Run each test module
    for module_name, description in test_modules:
        result = run_test_suite(module_name, description)
        results.append(result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Generate summary report
    print_header("TEST SUMMARY")
    print(f"Duration: {datetime.fromtimestamp(duration).strftime('%H:%M:%S')}")
    
    total_tests = sum(r['tests_run'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_skipped = sum(r['skipped'] for r in results)
    successful_modules = sum(1 for r in results if r['success'])
    
    print(f"Test modules run: {len(results)}")
    print(f"Successful modules: {successful_modules}/{len(results)}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failed: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    
    print_header("DETAILED RESULTS")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['module']:<20} Tests: {result['tests_run']:3d} "
              f"Failures: {result['failures']:2d} Errors: {result['errors']:2d} "
              f"Skipped: {result['skipped']:2d}")
    
    print_header("")
    
    # Overall result
    if successful_modules == len(results) and total_errors == 0:
        print("🎉 ALL TESTS PASSED!")
        return_code = 0
    elif successful_modules >= len(results) // 2:
        print("⚠️  SOME TESTS FAILED - Check individual results")
        return_code = 1
    else:
        print("💥 MANY TESTS FAILED!")
        return_code = 2
    
    print_header("")
    
    return return_code

if __name__ == '__main__':
    sys.exit(main())
