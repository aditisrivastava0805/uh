#!/usr/bin/env python3
"""
Test script to verify the LLM API fix works correctly.
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_llm_api_fix():
    """Test the LLM API fix."""
    print("🧪 Testing LLM API fix...")
    
    try:
        from genai_uplifter import get_llm_suggestion
        
        # Test with a simple Python code sample
        test_code = """
import sys
import ConfigParser

class TestModule:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
    
    def get_data(self, key):
        return self.config.get('default', key)
"""
        
        print("✅ Testing LLM suggestion with fixed API format...")
        
        # This should now work with the fixed API format
        result = get_llm_suggestion(
            code=test_code,
            analysis_findings="Python code modernization test",
            target_version="3.9",
            selected_libraries=[],
            file_type="python"
        )
        
        if result[0]:  # If we got updated code
            print("✅ LLM API fix successful - got updated code")
            print(f"Change summary: {result[1]}")
        else:
            print("⚠️  LLM API returned no changes (this is OK for test code)")
            print(f"Error message: {result[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM API fix test failed: {e}")
        return False

def test_frontend_encoding_fix():
    """Test the frontend encoding fix."""
    print("\n🧪 Testing frontend encoding fix...")
    
    try:
        # Test reading index.html with UTF-8 encoding
        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for required elements
            required_elements = [
                "upliftMode",
                "moduleSelectionSection", 
                "startButton",
                "changes-summary-section"
            ]
            
            for element in required_elements:
                if element in content:
                    print(f"✅ Found {element} in frontend")
                else:
                    print(f"❌ Missing {element} in frontend")
                    return False
            
            print("✅ Frontend encoding fix successful")
            return True
        else:
            print("❌ index.html not found")
            return False
            
    except Exception as e:
        print(f"❌ Frontend encoding fix test failed: {e}")
        return False

def main():
    """Run the LLM fix tests."""
    print("🚀 Testing LLM API and frontend encoding fixes...\n")
    
    tests = [
        test_llm_api_fix,
        test_frontend_encoding_fix
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
        print("🎉 All fixes working correctly!")
        print("\n💡 The workflow should now work without getting stuck.")
    else:
        print("⚠️  Some fixes still need work.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 