#!/usr/bin/env python3
"""
Robot Framework Test Validation Script

This script validates that all Robot Framework test files exist and are properly structured
for the target modules: KAFKA_UAF, NFS_DISK_STATUS_CHECK, POD_FILE_COLLECTOR, 
POD_FILE_SENDER, and SDP_STAT.
"""

import os
import sys
from pathlib import Path
import re

def validate_robot_file(file_path):
    """Validate a Robot Framework test file structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        errors = []
        warnings = []
        
        # Check for required sections
        required_sections = ['*** Settings ***', '*** Test Cases ***']
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: {section}")
                
        # Check for recommended sections
        recommended_sections = ['*** Variables ***', '*** Keywords ***']
        for section in recommended_sections:
            if section not in content:
                warnings.append(f"Missing recommended section: {section}")
                
        # Check for resource file import
        if 'Resource ' not in content:
            warnings.append("No Resource file import found")
            
        # Check for documentation
        if 'Documentation' not in content:
            warnings.append("No Documentation found")
            
        # Check for test tags
        if '[Tags]' not in content and 'Force Tags' not in content:
            warnings.append("No test tags found")
            
        # Count test cases
        test_case_count = len(re.findall(r'^[A-Za-z][A-Za-z0-9 _-]*$', content, re.MULTILINE))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'test_case_count': test_case_count,
            'file_size': os.path.getsize(file_path)
        }
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Failed to read file: {str(e)}"],
            'warnings': [],
            'test_case_count': 0,
            'file_size': 0
        }

def main():
    """Main validation function."""
    workspace_root = Path('.')
    target_modules = [
        'KAFKA_UAF',
        'NFS_DISK_STATUS_CHECK', 
        'POD_FILE_COLLECTOR',
        'POD_FILE_SENDER',
        'SDP_STAT'
    ]
    
    print("🤖 Robot Framework Test Validation")
    print("=" * 50)
    
    all_valid = True
    summary = {}
    
    for module in target_modules:
        print(f"\n📁 Validating {module}...")
        
        module_dir = workspace_root / module
        tests_dir = module_dir / 'tests'
        
        module_results = {
            'module_exists': module_dir.exists(),
            'tests_dir_exists': tests_dir.exists(),
            'test_files': [],
            'resource_files': []
        }
        
        if not module_dir.exists():
            print(f"  ❌ Module directory not found: {module_dir}")
            all_valid = False
            summary[module] = module_results
            continue
            
        if not tests_dir.exists():
            print(f"  ❌ Tests directory not found: {tests_dir}")
            all_valid = False
            summary[module] = module_results
            continue
            
        print(f"  ✅ Module directory: {module_dir}")
        print(f"  ✅ Tests directory: {tests_dir}")
        
        # Find test files
        test_files = list(tests_dir.glob("*tests.robot")) + list(tests_dir.glob("*test.robot"))
        resource_files = list(tests_dir.glob("*resource.robot"))
        
        if not test_files:
            print(f"  ❌ No test files found in {tests_dir}")
            all_valid = False
        else:
            print(f"  ✅ Found {len(test_files)} test file(s)")
            
        if not resource_files:
            print(f"  ⚠️  No resource files found in {tests_dir}")
        else:
            print(f"  ✅ Found {len(resource_files)} resource file(s)")
            
        # Validate each test file
        for test_file in test_files:
            print(f"    📄 Validating: {test_file.name}")
            validation = validate_robot_file(test_file)
            
            if validation['valid']:
                print(f"      ✅ Valid Robot Framework file")
                print(f"      📊 Estimated test cases: {validation['test_case_count']}")
                print(f"      📏 File size: {validation['file_size']} bytes")
            else:
                print(f"      ❌ Invalid Robot Framework file")
                for error in validation['errors']:
                    print(f"        🔸 Error: {error}")
                all_valid = False
                
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"        ⚠️  Warning: {warning}")
                    
            module_results['test_files'].append({
                'name': test_file.name,
                'path': str(test_file),
                'validation': validation
            })
            
        # Validate resource files
        for resource_file in resource_files:
            print(f"    📄 Validating resource: {resource_file.name}")
            validation = validate_robot_file(resource_file)
            
            module_results['resource_files'].append({
                'name': resource_file.name,
                'path': str(resource_file),
                'validation': validation
            })
            
        summary[module] = module_results
        
    # Print summary
    print(f"\n{'='*50}")
    print("📋 Validation Summary")
    print(f"{'='*50}")
    
    total_modules = len(target_modules)
    valid_modules = sum(1 for m, r in summary.items() 
                       if r['module_exists'] and r['tests_dir_exists'] and r['test_files'])
    
    total_test_files = sum(len(r['test_files']) for r in summary.values())
    valid_test_files = sum(1 for r in summary.values() 
                          for tf in r['test_files'] 
                          if tf['validation']['valid'])
    
    print(f"📁 Modules: {valid_modules}/{total_modules} valid")
    print(f"📄 Test files: {valid_test_files}/{total_test_files} valid")
    
    if all_valid:
        print(f"\n🎉 All Robot Framework tests are valid!")
    else:
        print(f"\n❌ Some validation errors found. Please fix them before running tests.")
        
    # Print detailed module status
    print(f"\n📊 Module Status:")
    for module, results in summary.items():
        status = "✅" if (results['module_exists'] and 
                         results['tests_dir_exists'] and 
                         results['test_files'] and
                         all(tf['validation']['valid'] for tf in results['test_files'])) else "❌"
        test_count = len(results['test_files'])
        print(f"  {status} {module:20} ({test_count} test files)")
        
    print(f"\n🚀 To run all tests: python robot_test_runner.py")
    print(f"🔍 To run validation only: python robot_test_runner.py --validate-only")
    
    return 0 if all_valid else 1

if __name__ == '__main__':
    sys.exit(main())
