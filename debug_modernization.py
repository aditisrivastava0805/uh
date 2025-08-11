#!/usr/bin/env python3
"""
Debug script to test the modernization process step by step.
"""

import os
import sys

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_file_filtering():
    """Test if file filtering is working correctly."""
    print("🧪 Testing file filtering...")
    
    # Simulate the file filtering logic
    repo_path = "cec-adaptation-pod-main"
    
    def find_python_files(repo_path):
        python_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    all_python_files = find_python_files(repo_path)
    print(f"📁 Found {len(all_python_files)} total Python files")
    
    # Test with SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER module
    selected_modules = ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER"]
    print(f"🎯 Selected modules: {selected_modules}")
    
    # Filter files based on selected modules
    if selected_modules:
        python_files = []
        for file_path in all_python_files:
            # Check if file path contains any of the selected modules
            file_included = False
            for module in selected_modules:
                if module.lower() in file_path.lower():
                    python_files.append(file_path)
                    file_included = True
                    break
            if not file_included:
                print(f"  ⏭️  Skipping {os.path.basename(file_path)}")
    
    print(f"✅ Found {len(python_files)} files for selected modules:")
    for file_path in python_files:
        print(f"  📄 {file_path}")
    
    return python_files

def test_llm_modernization():
    """Test if LLM modernization is working."""
    print("\n🧪 Testing LLM modernization...")
    
    try:
        # Try to import the modules
        from genai_uplifter_simplified import analyze_python_code, get_llm_suggestion
        
        # Test with a simple Python file
        test_file = "cec-adaptation-pod-main/cec-adaptation-pod-main/SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER/sdptrafficsplunk.py"
        
        if os.path.exists(test_file):
            print(f"📄 Testing with file: {test_file}")
            
            # Test analysis
            analysis = analyze_python_code(test_file, "3.9")
            print(f"🔍 Analysis result: {analysis}")
            
            # Test LLM suggestion (this will fail if no API token)
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                updated_code, change_summary = get_llm_suggestion(
                    code, analysis, "3.9", [], "python"
                )
                
                if updated_code:
                    print(f"✅ LLM modernization successful")
                    print(f"📝 Change summary: {change_summary[:200]}...")
                else:
                    print(f"❌ LLM modernization failed: {change_summary}")
                    
            except Exception as e:
                print(f"⚠️  LLM modernization error: {e}")
        else:
            print(f"❌ Test file not found: {test_file}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing dependencies: pip3 install -r requirements.txt")

def test_config_passing():
    """Test if configuration is being passed correctly."""
    print("\n🧪 Testing configuration passing...")
    
    # Simulate the config that should be passed
    uplift_config = {
        "type": "python",
        "target_version": "3.9",
        "selected_modules": ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER"]
    }
    
    print(f"📋 Uplift config: {uplift_config}")
    print(f"🎯 Selected modules: {uplift_config.get('selected_modules', [])}")
    
    # Check if the config structure matches what the function expects
    if "selected_modules" in uplift_config:
        print("✅ Config contains selected_modules")
        if uplift_config["selected_modules"]:
            print("✅ Selected modules list is not empty")
        else:
            print("❌ Selected modules list is empty")
    else:
        print("❌ Config missing selected_modules")

if __name__ == "__main__":
    print("🔍 Debugging modernization process...")
    
    test_file_filtering()
    test_config_passing()
    test_llm_modernization()
    
    print("\n🎯 Debug complete!") 