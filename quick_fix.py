#!/usr/bin/env python3
"""
Quick fix script to override the unreachable Ericsson hostname URLs.
Run this before running your main modernization scripts.
"""

import os
import sys

def apply_quick_fix():
    """Apply quick fix by setting environment variables."""
    
    # Set fallback URLs
    os.environ["LLM_API_URL"] = "http://localhost:8000/api/llm/generate"
    os.environ["RAG_API_URL"] = "http://localhost:8000/api/rag/query"
    os.environ["RAG_FILTERS_URL"] = "http://localhost:8000/api/rag/search_filters"
    
    # Set a dummy token for testing
    os.environ["LLM_API_TOKEN"] = "dummy_token_for_local_testing"
    os.environ["RAG_API_TOKEN"] = "dummy_token_for_local_testing"
    
    print("✅ Quick fix applied!")
    print("   - LLM_API_URL set to: http://localhost:8000/api/llm/generate")
    print("   - RAG_API_URL set to: http://localhost:8000/api/rag/query")
    print("   - RAG_FILTERS_URL set to: http://localhost:8000/api/rag/search_filters")
    print("   - Dummy tokens set for local testing")
    print()
    print("⚠️  Note: You'll need to set up local API endpoints or")
    print("   configure real API tokens for actual functionality.")

def test_import():
    """Test if we can import the modules after the fix."""
    try:
        # Apply the fix first
        apply_quick_fix()
        
        # Try to import rag_utils
        print("\n🧪 Testing imports...")
        from rag_utils import get_api_status
        print("✅ rag_utils imported successfully")
        
        # Show status
        status = get_api_status()
        print("\n🔧 Current API Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
            
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Fix for Ericsson Hostname Issue")
    print("=" * 50)
    
    if test_import():
        print("\n🎉 Quick fix successful! You can now run your modernization scripts.")
        print("\n📝 Next steps:")
        print("   1. Set up local API endpoints at localhost:8000, OR")
        print("   2. Configure real API tokens in environment variables, OR")
        print("   3. Use the system in fallback mode with dummy data")
    else:
        print("\n❌ Quick fix failed. Check the error messages above.") 