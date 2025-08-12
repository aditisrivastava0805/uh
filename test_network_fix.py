#!/usr/bin/env python3
"""
Test script to verify that network errors are now handled gracefully.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_utils():
    """Test RAG utilities with network fallback."""
    print("🧪 Testing RAG Utilities...")
    
    try:
        from rag_utils import get_api_status, get_available_libraries
        
        # Check API status
        status = get_api_status()
        print(f"✅ API Status: {status}")
        
        # Test getting libraries (should use fallback)
        libraries = get_available_libraries()
        print(f"✅ Libraries retrieved: {len(libraries)} categories")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Utils test failed: {e}")
        return False

def test_genai_uplifter():
    """Test GenAI Uplifter with network fallback."""
    print("\n🧪 Testing GenAI Uplifter...")
    
    try:
        from genai_uplifter_simplified import get_llm_api_url, get_local_modernization_guidance
        
        # Check LLM API URL
        llm_url = get_llm_api_url()
        print(f"✅ LLM API URL: {llm_url}")
        
        # Test local modernization guidance
        test_code = "print 'Hello World'\nraw_input('Enter name: ')"
        updated_code, summary = get_local_modernization_guidance(
            test_code, "Python 2 to 3", "3.9", "python"
        )
        print(f"✅ Local modernization: {summary}")
        print(f"   Updated code preview: {updated_code[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ GenAI Uplifter test failed: {e}")
        return False

def test_network_error_handling():
    """Test that network errors are handled gracefully."""
    print("\n🧪 Testing Network Error Handling...")
    
    try:
        from rag_utils import query_rag_api
        
        # This should trigger the network error handling
        result = query_rag_api("test query", max_evidences=2)
        
        if result.get("local_mode"):
            print("✅ Network error handled gracefully - local mode activated")
            print(f"   Response: {result.get('answer', 'No answer')}")
            return True
        else:
            print(f"⚠️  Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Network error handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Network Error Fixes")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_rag_utils():
        tests_passed += 1
    
    if test_genai_uplifter():
        tests_passed += 1
    
    if test_network_error_handling():
        tests_passed += 1
    
    print(f"\n🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Network errors are now handled gracefully.")
        print("\n📝 The system will now:")
        print("   - Use local fallback URLs when Ericsson network is unreachable")
        print("   - Provide local modernization guidance without external APIs")
        print("   - Continue working even when network is unavailable")
    else:
        print("❌ Some tests failed. Check the error messages above.") 