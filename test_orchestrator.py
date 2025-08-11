#!/usr/bin/env python3
"""
Test script to verify the orchestrator is working correctly.
"""

import os
import sys

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_orchestrator_logic():
    """Test the orchestrator logic without running the full process."""
    print("🧪 Testing orchestrator logic...")
    
    try:
        # Import the orchestrator functions
        from orchestrator_simplified import modernize_adaptation_pod_scripts, find_python_files
        
        # Test the file filtering logic
        repo_path = "cec-adaptation-pod-main"
        
        # Simulate the config that should be passed from frontend
        uplift_config = {
            "type": "python",
            "target_version": "3.9",
            "selected_modules": ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER"]
        }
        
        print(f"📋 Uplift config: {uplift_config}")
        print(f"🎯 Selected modules: {uplift_config.get('selected_modules', [])}")
        
        # Test the find_python_files function
        all_python_files = find_python_files(repo_path)
        print(f"📁 Found {len(all_python_files)} total Python files")
        
        # Test the filtering logic that should be used in modernize_adaptation_pod_scripts
        selected_modules = uplift_config.get('selected_modules', [])
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
        else:
            python_files = all_python_files
        
        print(f"✅ Found {len(python_files)} files for selected modules:")
        for file_path in python_files:
            print(f"  📄 {file_path}")
        
        # Now test if the modernize_adaptation_pod_scripts function would use this correctly
        print(f"\n🔍 Testing if modernize_adaptation_pod_scripts would use the correct config...")
        
        # Check if the function signature matches what we expect
        import inspect
        sig = inspect.signature(modernize_adaptation_pod_scripts)
        print(f"📝 Function signature: {sig}")
        
        # Check if the function expects uplift_config as second parameter
        params = list(sig.parameters.keys())
        if len(params) >= 2 and params[1] == 'uplift_config':
            print("✅ Function signature is correct")
        else:
            print("❌ Function signature mismatch - uplift_config not in expected position")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_config():
    """Test if the frontend is sending the correct config."""
    print("\n🧪 Testing frontend config structure...")
    
    # Simulate what the frontend should send
    frontend_request = {
        "uplift_config": {
            "type": "python",
            "target_version": "3.9",
            "selected_modules": ["SDP_SPLUNK_FORWARDER_TRAFFIC_HANDLER"]
        },
        "selected_libraries": []
    }
    
    print(f"📤 Frontend sends: {frontend_request}")
    
    # Simulate what the backend receives
    uplift_config = frontend_request.get("uplift_config", {})
    selected_libraries = frontend_request.get("selected_libraries", [])
    
    print(f"📥 Backend receives:")
    print(f"  - uplift_config: {uplift_config}")
    print(f"  - selected_libraries: {selected_libraries}")
    
    # Check if selected_modules is properly included
    if "selected_modules" in uplift_config:
        print("✅ selected_modules is included in uplift_config")
        if uplift_config["selected_modules"]:
            print("✅ selected_modules list is not empty")
            print(f"  - Modules: {uplift_config['selected_modules']}")
        else:
            print("❌ selected_modules list is empty")
    else:
        print("❌ selected_modules is missing from uplift_config")

if __name__ == "__main__":
    print("🔍 Testing orchestrator configuration...")
    
    success1 = test_orchestrator_logic()
    test_frontend_config()
    
    if success1:
        print("\n✅ Orchestrator logic test completed successfully!")
        print("💡 The issue might be in the actual execution flow")
    else:
        print("\n❌ Orchestrator logic test failed!")
    
    print("\n🎯 Next steps:")
    print("1. Check if the frontend is actually sending selected_modules")
    print("2. Check if the backend is receiving the config correctly")
    print("3. Check if the config is being passed to the modernization function") 