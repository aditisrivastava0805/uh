#!/usr/bin/env python3
"""
Simple test script to debug RAG utilities and show configuration status.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rag_utils import get_api_status, test_rag_connection, get_available_libraries
    print("✅ Successfully imported rag_utils")
    
    # Show API configuration status
    print("\n🔧 API Configuration Status:")
    print("=" * 50)
    status = get_api_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Test basic functionality
    print("\n🧪 Testing Basic Functions:")
    print("=" * 50)
    
    # Test get_available_libraries
    try:
        libraries = get_available_libraries()
        if "error" in libraries:
            print(f"❌ get_available_libraries failed: {libraries['error']}")
        else:
            print(f"✅ get_available_libraries succeeded: {len(libraries)} categories found")
    except Exception as e:
        print(f"❌ get_available_libraries exception: {e}")
    
    # Test RAG connection
    try:
        success, message = test_rag_connection()
        if success:
            print(f"✅ RAG connection test: {message}")
        else:
            print(f"❌ RAG connection test: {message}")
    except Exception as e:
        print(f"❌ RAG connection test exception: {e}")
    
    print("\n🎯 Summary:")
    print("=" * 50)
    if status["fallback_mode"]:
        print("⚠️  Running in FALLBACK mode (Ericsson network unreachable)")
        print("   This is expected when working outside the corporate network")
    else:
        print("✅ Running with Ericsson internal network access")
    
    if not status["has_token"]:
        print("⚠️  No API token configured - some functions may not work")
    else:
        print("✅ API token configured")
        
except ImportError as e:
    print(f"❌ Failed to import rag_utils: {e}")
    print("This suggests there's a syntax error in the file")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc() 