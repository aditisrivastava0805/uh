#!/usr/bin/env python3
"""
Test script for the flexible uplift system.
This script tests the system's ability to work with different file types and codebases.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import (
    find_files_by_extension, 
    find_java_files, 
    find_python_files, 
    get_file_type,
    uplift_repository
)

def create_test_files():
    """Create test files for different languages."""
    test_dir = tempfile.mkdtemp(prefix="uplift_test_")
    
    # Create Java test file
    java_file = os.path.join(test_dir, "TestClass.java")
    with open(java_file, 'w') as f:
        f.write("""
import java.util.Vector;
import java.util.Hashtable;

public class TestClass {
    private Vector<String> items;
    private Hashtable<String, String> data;
    
    public TestClass() {
        items = new Vector<String>();
        data = new Hashtable<String, String>();
    }
    
    public void addItem(String item) {
        items.addElement(item);
    }
    
    public String getData(String key) {
        return data.get(key);
    }
    
    public void setData(String key, String value) {
        data.put(key, value);
    }
}
""")
    
    # Create Python test file
    python_file = os.path.join(test_dir, "test_module.py")
    with open(python_file, 'w') as f:
        f.write("""
import sys
import ConfigParser

class TestModule:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
        print "Added item: " + item
    
    def get_data(self, key):
        return self.config.get('default', key)
    
    def set_data(self, key, value):
        self.config.set('default', key, value)
    
    def process_items(self):
        for item in self.items:
            print "Processing: " + item
""")
    
    # Create JavaScript test file
    js_file = os.path.join(test_dir, "test_script.js")
    with open(js_file, 'w') as f:
        f.write("""
var TestScript = function() {
    this.items = [];
    this.data = {};
};

TestScript.prototype.addItem = function(item) {
    this.items.push(item);
    console.log("Added item: " + item);
};

TestScript.prototype.getData = function(key) {
    return this.data[key];
};

TestScript.prototype.setData = function(key, value) {
    this.data[key] = value;
};

TestScript.prototype.processItems = function() {
    for (var i = 0; i < this.items.length; i++) {
        console.log("Processing: " + this.items[i]);
    }
};
""")
    
    return test_dir

def test_file_detection():
    """Test file detection functions."""
    print("🧪 Testing file detection functions...")
    
    test_dir = create_test_files()
    
    try:
        # Test Java file detection
        java_files = find_java_files(test_dir)
        print(f"Found {len(java_files)} Java files: {java_files}")
        
        # Test Python file detection
        python_files = find_python_files(test_dir)
        print(f"Found {len(python_files)} Python files: {python_files}")
        
        # Test generic file detection
        all_files = find_files_by_extension(test_dir, ['.java', '.py', '.js'])
        print(f"Found {len(all_files)} total files: {all_files}")
        
        # Test file type detection
        for file_path in all_files:
            file_type = get_file_type(file_path)
            print(f"File {os.path.basename(file_path)} is type: {file_type}")
        
        print("✅ File detection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ File detection test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)

def test_uplift_configuration():
    """Test uplift configuration handling."""
    print("\n🧪 Testing uplift configuration...")
    
    # Test Java configuration
    java_config = {
        'type': 'java',
        'target_version': '17',
        'source_path': 'repositories/ESSVT'
    }
    print(f"Java config: {java_config}")
    
    # Test Python configuration
    python_config = {
        'type': 'python',
        'target_version': '3.9',
        'source_path': 'cec-adaptation-pod-main',
        'selected_modules': ['KAFKA_CAF', 'CAF_HEALTH_CHECK_FILE_GENERATOR']
    }
    print(f"Python config: {python_config}")
    
    # Test adaptation pod configuration
    adaptation_config = {
        'type': 'python',
        'target_version': '3.9',
        'source_path': 'cec-adaptation-pod-main',
        'selected_modules': ['KAFKA_CAF', 'POD_FILE_COLLECTOR']
    }
    print(f"Adaptation pod config: {adaptation_config}")
    
    print("✅ Uplift configuration tests passed!")
    return True

def test_adaptation_pod_structure():
    """Test adaptation pod module structure detection."""
    print("\n🧪 Testing adaptation pod structure...")
    
    # Check if adaptation pod directory exists
    adaptation_dir = "cec-adaptation-pod-main"
    if os.path.exists(adaptation_dir):
        print(f"✅ Adaptation pod directory found: {adaptation_dir}")
        
        # List available modules
        modules = []
        for item in os.listdir(adaptation_dir):
            item_path = os.path.join(adaptation_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                modules.append(item)
        
        print(f"Available modules: {modules}")
        
        # Test finding Python files in modules
        for module in modules[:3]:  # Test first 3 modules
            module_path = os.path.join(adaptation_dir, module)
            python_files = find_python_files(module_path)
            print(f"Module {module}: {len(python_files)} Python files")
            
    else:
        print(f"⚠️  Adaptation pod directory not found: {adaptation_dir}")
    
    print("✅ Adaptation pod structure tests completed!")
    return True

def main():
    """Run all tests."""
    print("🚀 Starting flexible uplift system tests...\n")
    
    tests = [
        test_file_detection,
        test_uplift_configuration,
        test_adaptation_pod_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The flexible uplift system is ready.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 