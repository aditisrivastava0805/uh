#!/usr/bin/env python3
"""
Quick validation script for all KAFKA_SDP modules
Validates that all three modules (PREPAID, POSTPAID, GEORED) are production ready
"""

import os
import sys
import subprocess
from datetime import datetime

def check_module_tests(module_name, test_commands):
    """Check if a module's tests are working"""
    print(f"\n{'='*60}")
    print(f"🔍 Validating {module_name}")
    print(f"{'='*60}")
    
    module_path = os.path.join(os.getcwd(), module_name)
    tests_path = os.path.join(module_path, 'tests')
    
    if not os.path.exists(tests_path):
        print(f"❌ Tests directory not found for {module_name}")
        return False
    
    print(f"📁 Module path: {module_path}")
    print(f"📁 Tests path: {tests_path}")
    
    original_cwd = os.getcwd()
    success_count = 0
    
    try:
        os.chdir(tests_path)
        
        for command_name, command in test_commands.items():
            print(f"\n🧪 Running {command_name}...")
            
            try:
                result = os.system(command)
                if result == 0:
                    print(f"   ✅ {command_name} PASSED")
                    success_count += 1
                else:
                    print(f"   ❌ {command_name} FAILED")
            except Exception as e:
                print(f"   💥 {command_name} ERROR: {e}")
        
        return success_count == len(test_commands)
    
    finally:
        os.chdir(original_cwd)

def main():
    """Main validation function"""
    print("="*80)
    print("🧪 KAFKA_SDP Module Test Validation")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Define test commands for each module
    modules = {
        'KAFKA_SDP_PREPAID': {
            'Basic Tests': 'python test_basic_fixed.py',
            'Safe Functions': 'python test_safe_functions.py'
        },
        'KAFKA_SDP_POSTPAID': {
            'Basic Tests': 'python test_basic.py',
            'Safe Functions': 'python test_safe_functions.py'
        },
        'KAFKA_SDP_GEORED': {
            'All Tests': 'python run_simple_tests.py'
        }
    }
    
    results = {}
    
    # Test each module
    for module_name, test_commands in modules.items():
        success = check_module_tests(module_name, test_commands)
        results[module_name] = success
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*80}")
    
    successful_modules = sum(1 for success in results.values() if success)
    total_modules = len(results)
    
    for module_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {module_name}")
    
    print(f"\nModules validated: {successful_modules}/{total_modules}")
    
    if successful_modules == total_modules:
        print("\n🎉 ALL MODULES VALIDATED - PRODUCTION READY!")
        print("✅ All KAFKA_SDP modules have working test suites")
        print("✅ Core functionality validated across all modules")
        print("✅ Test infrastructure complete and reliable")
    elif successful_modules > 0:
        print(f"\n⚠️  PARTIAL SUCCESS - {successful_modules} modules validated")
        print("Some modules may need attention")
    else:
        print("\n❌ VALIDATION FAILED - No modules passed tests")
        print("Test infrastructure needs review")
    
    print(f"\n{'='*80}")
    
    return successful_modules, total_modules

if __name__ == '__main__':
    try:
        successful, total = main()
        if successful == total:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation error: {e}")
        sys.exit(1)
