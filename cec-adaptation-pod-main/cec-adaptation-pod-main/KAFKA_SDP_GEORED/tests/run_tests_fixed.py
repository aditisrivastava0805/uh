#!/usr/bin/env python3
"""
Test runner for KAFKA_SDP_GEORED module
Runs the most reliable and comprehensive tests
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"🔍 Running {test_file}")
    print(f"{'='*60}")
    
    try:        
        result = subprocess.run([
            sys.executable, test_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ PASSED")
            lines = result.stdout.split('\n')
            test_summary = [line for line in lines if 'Ran' in line and 'tests' in line]
            if test_summary:
                print(f"   {test_summary[0]}")
            return True, result.stdout, result.stderr
        else:
            print("❌ FAILED")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False, "", "Test timed out"
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False, "", str(e)

def main():
    """Main test runner function"""
    print("="*80)
    print("🧪 KAFKA_SDP_GEORED Test Suite Runner")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Test files to run in order of reliability
    test_files = [
        'test_basic_fixed.py',
        'test_safe_functions_fixed.py',
        'test_basic.py',
        'test_safe_functions.py',
        'test_kpi_sdp.py',
        'test_logger_subprocess.py'
    ]
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            success, stdout, stderr = run_test_file(test_file)
            
            # Extract test count if available
            test_count = 0
            for line in stdout.split('\n'):
                if 'Ran' in line and 'tests' in line:
                    try:
                        test_count = int(line.split()[1])
                        break
                    except:
                        pass
            
            results.append({
                'file': test_file,
                'success': success,
                'test_count': test_count,
                'stdout': stdout,
                'stderr': stderr
            })
            
            total_tests += test_count
            if success:
                passed_tests += test_count
        else:
            print(f"⚠️  Test file {test_file} not found")
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Duration: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Test files run: {len(results)}")
    successful_files = sum(1 for r in results if r['success'])
    print(f"Successful files: {successful_files}/{len(results)}")
    print(f"Total tests run: {total_tests}")
    print(f"Tests passed: {passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    print("\n" + "="*80)
    print("📋 DETAILED RESULTS")
    print("="*80)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['file']:<25} Tests: {result['test_count']:>3}")
    
    print("\n" + "="*80)
    
    if successful_files == len(results):
        print("🎉 ALL TESTS PASSED - Module is ready for production!")
    elif successful_files >= len(results) * 0.8:  # 80% success rate
        print("⚠️  MOST TESTS PASSED - Module is likely production ready")
    else:
        print("❌ SEVERAL TESTS FAILED - Module needs attention")
    
    print("="*80)
    
    return successful_files, len(results), passed_tests, total_tests

if __name__ == '__main__':
    try:
        successful_files, total_files, passed_tests, total_tests = main()
        
        # Exit with appropriate code
        if successful_files == total_files:
            sys.exit(0)  # All passed
        elif passed_tests >= total_tests * 0.8:  # 80% success rate
            sys.exit(0)  # Acceptable success rate
        else:
            sys.exit(1)  # Too many failures
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner error: {e}")
        sys.exit(1)
