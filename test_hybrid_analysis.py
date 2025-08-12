#!/usr/bin/env python3
"""
Test script for the new hybrid LLM + regex analysis approach
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from genai_uplifter_simplified import analyze_python_code

def test_hybrid_analysis():
    """Test the hybrid analysis on the KAFKA_SDP_KPI module"""
    
    print("🧪 Testing Hybrid LLM + Regex Analysis")
    print("=" * 50)
    
    # Test file path
    test_file = "cec-adaptation-pod-main/cec-adaptation-pod-main/KAFKA_SDP_KPI/kafka_sdpkpi.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Analyzing: {test_file}")
    print(f"🎯 Target Python version: 3.9")
    print("-" * 50)
    
    try:
        # Run the hybrid analysis
        analysis_result = analyze_python_code(test_file, "3.9")
        
        print("🔍 Analysis Complete!")
        print("=" * 50)
        print(analysis_result)
        print("=" * 50)
        
        # Check if analysis found opportunities
        if "modernization opportunities found" in analysis_result.lower():
            print("✅ SUCCESS: Analysis detected modernization opportunities!")
        elif "python 2 style code" in analysis_result.lower():
            print("✅ SUCCESS: Analysis detected Python 2 style code!")
        else:
            print("⚠️  Analysis completed but no clear opportunities identified")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_analysis() 