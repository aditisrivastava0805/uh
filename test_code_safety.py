#!/usr/bin/env python3
"""
Test script for the new code safety validation system
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from genai_uplifter_simplified import validate_code_safety

def test_code_safety():
    """Test the code safety validation system"""
    
    print("🧪 Testing Code Safety Validation System")
    print("=" * 50)
    
    # Test 1: Safe modernization (only syntax changes)
    print("\n📝 Test 1: Safe Modernization")
    print("-" * 30)
    
    original_code = '''
import json
import os

def process_data(data):
    """Process the input data."""
    result = []
    for item in data:
        if len(item) > 0:
            result.append(item)
    return result

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        self.data.append(item)
    
    def process(self):
        return process_data(self.data)

# Main execution
if __name__ == "__main__":
    processor = DataProcessor()
    processor.add_item("test")
    print processor.process()  # Python 2 style print
'''
    
    modernized_code = '''
import json
import os

def process_data(data):
    """Process the input data."""
    result = []
    for item in data:
        if len(item) > 0:
            result.append(item)
    return result

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        self.data.append(item)
    
    def process(self):
        return process_data(self.data)

# Main execution
if __name__ == "__main__":
    processor = DataProcessor()
    processor.add_item("test")
    print(processor.process())  # Python 3 style print
'''
    
    result = validate_code_safety(original_code, modernized_code)
    print(f"✅ Safety check result: {result}")
    
    # Test 2: Dangerous modernization (function deleted)
    print("\n📝 Test 2: Dangerous Modernization (Function Deleted)")
    print("-" * 30)
    
    dangerous_code = '''
import json
import os

# process_data function was deleted!

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        self.data.append(item)
    
    def process(self):
        return process_data(self.data)  # This will fail!

# Main execution
if __name__ == "__main__":
    processor = DataProcessor()
    processor.add_item("test")
    print(processor.process())
'''
    
    result = validate_code_safety(original_code, dangerous_code)
    print(f"❌ Safety check result: {result}")
    
    # Test 3: Very dangerous modernization (class deleted)
    print("\n📝 Test 3: Very Dangerous Modernization (Class Deleted)")
    print("-" * 30)
    
    very_dangerous_code = '''
import json
import os

def process_data(data):
    """Process the input data."""
    result = []
    for item in data:
        if len(item) > 0:
            result.append(item)
    return result

# DataProcessor class was deleted!

# Main execution
if __name__ == "__main__":
    processor = DataProcessor()  # This will fail!
    processor.add_item("test")
    print(processor.process())
'''
    
    result = validate_code_safety(original_code, very_dangerous_code)
    print(f"❌ Safety check result: {result}")

if __name__ == "__main__":
    test_code_safety() 