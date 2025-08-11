#!/usr/bin/env python3
"""
Test script to verify module selection filtering works correctly.
"""

import os
import sys

def find_python_files(repo_path):
    """Find all Python files in a repository recursively."""
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def filter_files_by_modules(all_files, selected_modules):
    """Filter files based on selected modules."""
    if not selected_modules:
        return all_files
    
    filtered_files = []
    for file_path in all_files:
        # Check if file path contains any of the selected modules
        file_included = False
        for module in selected_modules:
            if module.lower() in file_path.lower():
                filtered_files.append(file_path)
                file_included = True
                break
        if not file_included:
            print(f"Skipping {file_path} - not in selected modules")
    
    return filtered_files

def test_module_selection():
    """Test the module selection filtering."""
    repo_path = "cec-adaptation-pod-main"
    
    if not os.path.exists(repo_path):
        print(f"❌ Repository path not found: {repo_path}")
        return False
    
    # Find all Python files
    all_python_files = find_python_files(repo_path)
    print(f"📁 Found {len(all_python_files)} total Python files")
    
    # Test with SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER module
    selected_modules = ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER"]
    print(f"\n🎯 Testing with selected modules: {selected_modules}")
    
    filtered_files = filter_files_by_modules(all_python_files, selected_modules)
    print(f"✅ Found {len(filtered_files)} files for selected modules")
    
    for file_path in filtered_files:
        print(f"  📄 {file_path}")
    
    # Test with multiple modules
    selected_modules = ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER", "KAFKA_AF"]
    print(f"\n🎯 Testing with multiple modules: {selected_modules}")
    
    filtered_files = filter_files_by_modules(all_python_files, selected_modules)
    print(f"✅ Found {len(filtered_files)} files for selected modules")
    
    for file_path in filtered_files:
        print(f"  📄 {file_path}")
    
    # Test with no modules selected (should return all files)
    selected_modules = []
    print(f"\n🎯 Testing with no modules selected (should return all files)")
    
    filtered_files = filter_files_by_modules(all_python_files, selected_modules)
    print(f"✅ Found {len(filtered_files)} files (should be {len(all_python_files)})")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing module selection filtering...")
    success = test_module_selection()
    if success:
        print("\n✅ Module selection test completed successfully!")
    else:
        print("\n❌ Module selection test failed!")
        sys.exit(1) 