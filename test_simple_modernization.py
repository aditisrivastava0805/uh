#!/usr/bin/env python3
"""
Simple test for the modernization system
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic modernization functionality"""
    
    print("🧪 Testing Basic Modernization Functionality")
    print("=" * 50)
    
    # Test file path
    test_file = "cec-adaptation-pod-main/cec-adaptation-pod-main/KAFKA_AIR/KPI_AIR.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Test file: {test_file}")
    print(f"🎯 Target Python version: 3.9")
    print("-" * 50)
    
    try:
        # Test file reading
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ File read successfully ({len(content)} characters)")
        
        # Test basic analysis (without LLM)
        print(f"📊 File size: {len(content)/1024:.1f}KB")
        
        # Check for Python 2 patterns
        import re
        
        print("\n🔍 Pattern Analysis:")
        patterns = {
            'print statements without parentheses': r'print\s+[^(]',
            'percent formatting': r'%[sd]',
            'function definitions': r'def\s+\w+',
            'class definitions': r'class\s+\w+',
            'import statements': r'import\s+\w+'
        }
        
        for description, pattern in patterns.items():
            matches = len(re.findall(pattern, content, re.MULTILINE))
            print(f"  {description}: {matches} found")
        
        print("\n✅ Basic functionality test completed")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality() 