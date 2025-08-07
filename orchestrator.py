#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil
import datetime
# import glob
import xml.etree.ElementTree as ET
from genai_uplifter import  analyze_with_modernizer, get_llm_suggestion
from rag_utils import get_available_libraries
from genai_uplifter import initialize_llm_api, analyze_with_modernizer, get_llm_suggestion
from rag_utils import extract_java_guidance, get_ericsson_java_libraries, get_available_libraries
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uvicorn
import threading
import queue
import time

LLM_API_TOKEN = os.getenv("LLM_API_TOKEN", "")

# Global summary log
summary_log = []

# Global variables for process control
process_running = False      # Add this if missing
current_stage = "idle"       # Add this if missing  
process_status = "IDLE"      # Should already exist
event_queue = queue.Queue()  # Should already exist
process_thread = None        # Should already exist
selected_libraries = []      # Store selected library IDs for RAG context
uplift_config = {}          # Store uplift configuration

# Create output directories if they don't exist
os.makedirs("baseline_output", exist_ok=True)
os.makedirs("essvt_output", exist_ok=True)
os.makedirs("final_output", exist_ok=True)

# FastAPI app
app = FastAPI(title="GenAI JDK Uplift Tool")

# ESSVT Configuration - COMMENTED OUT FOR LOCAL-ONLY MODE
# ESSVT_CONFIG = {
#     "enabled": os.getenv("ESSVT_ENABLED", "false").lower() == "true",
#     "base_url": os.getenv("ESSVT_BASE_URL", "https://essvt.hahn168.rnd.gic.ericsson.se"),
#     "username": os.getenv("ESSVT_USERNAME", ""),
#     "password": os.getenv("ESSVT_PASSWORD", ""),
#     "project_id": os.getenv("ESSVT_PROJECT_ID", ""),
#     "client_id": os.getenv("ESSVT_CLIENT_ID", "essvt-public")
# }



def log_summary(section, content):
    """Add a section to the summary log."""
    summary_log.append(f"\n{'=' * 50}")
    summary_log.append(f"  {section}")
    summary_log.append(f"{'=' * 50}")
    summary_log.append(content)

def save_summary():
    """Save the summary log to a file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"uplift_summary_{timestamp}.log"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(summary_log))
    
    print(f"\n📝 Summary saved to: {summary_file}")
    return summary_file

def run_command(command, capture_output=True):
    """Execute a command and return the result."""
    print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=capture_output, text=True, check=False)
        if result.returncode != 0:
            print(f"Warning: Command returned non-zero exit code {result.returncode}")
            if capture_output:
                print(f"Stderr: {result.stderr}")
        return result.stdout if capture_output else None, result.stderr if capture_output else None, result.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return None, str(e), 1

def reset_repositories():
    """Reset repositories and output directories to legacy versions."""
    print("\n🔄 Resetting repositories and output directories...")
    reset_summary = []
    
    try:
        # Clear output directories
        output_dirs = ['baseline_output', 'essvt_output', 'final_output']
        for output_dir in output_dirs:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"Clearing {output_dir}...")
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
            reset_summary.append(f"✓ Cleared directory: {output_dir}")
        
        # Remove repositories/output directory if it exists
        if os.path.exists('repositories/output'):
            shutil.rmtree('repositories/output')
            reset_summary.append(f"✓ Removed temporary repositories/output directory")
        
        # Reset ESSVT repository
        print("Resetting ESSVT repository...")
        # Ensure repository directories exist
        os.makedirs("repositories/ESSVT/src/com/example/server", exist_ok=True)
        
        # Remove .class files and summary files
        removed_files = 0
        for root, dirs, files in os.walk('repositories/ESSVT'):
            for file in files:
                if file.endswith('.class') or file.endswith('_uplift_summary.txt'):
                    os.remove(os.path.join(root, file))
                    removed_files += 1
        reset_summary.append(f"✓ Removed {removed_files} generated files from ESSVT repository")
        
        # Copy legacy TestUtil.java to ESSVT
        if os.path.exists('legacy_code/TestUtil.java'):
            shutil.copy('legacy_code/TestUtil.java', 'repositories/ESSVT/src/com/example/server/TestUtil.java')
            reset_summary.append(f"✓ Restored legacy TestUtil.java")
        
        # Copy legacy DivisionTest.java to ESSVT
        if os.path.exists('legacy_code/DivisionTest.java'):
            shutil.copy('legacy_code/DivisionTest.java', 'repositories/ESSVT/src/com/example/server/DivisionTest.java')
            reset_summary.append(f"✓ Restored legacy DivisionTest.java")
        
        # Copy legacy tests.robot to ESSVT
        if os.path.exists('legacy_code/tests.robot'):
            shutil.copy('legacy_code/tests.robot', 'repositories/ESSVT/tests.robot')
            reset_summary.append(f"✓ Restored legacy tests.robot")
        
        # Reset source-code repository
        print("Resetting source-code repository...")
        # Ensure repository directories exist
        os.makedirs("repositories/source-code/src/com/example/server", exist_ok=True)
        
        # Remove .class files and any accidentally created Java files
        removed_files = 0
        for root, dirs, files in os.walk('repositories/source-code'):
            for file in files:
                if file.endswith('.class') or (file.endswith('.java') and file not in ['Main.java']):
                    os.remove(os.path.join(root, file))
                    removed_files += 1
        reset_summary.append(f"✓ Removed {removed_files} generated files from source-code repository")
        
        # Copy legacy Main.java to source-code
        if os.path.exists('legacy_code/Main.java'):
            shutil.copy('legacy_code/Main.java', 'repositories/source-code/src/com/example/server/Main.java')
            reset_summary.append(f"✓ Restored legacy Main.java")
        
        print("✅ Repositories and output directories reset successfully")
        reset_summary.append("\nRepositories and output directories reset successfully.")
        log_summary("REPOSITORY RESET", "\n".join(reset_summary))
        return True
    except Exception as e:
        error_msg = f"❌ Error resetting repositories: {e}"
        print(error_msg)
        reset_summary.append(error_msg)
        log_summary("REPOSITORY RESET", "\n".join(reset_summary))
        return False

def run_tests(environment, output_dir):
    """Run Robot Framework tests in the specified Docker environment."""
    print(f"\n=== Running tests in {environment} environment ===")
    test_summary = []
    test_summary.append(f"Environment: {environment}")
    test_summary.append(f"Output directory: {output_dir}")
    
    # Send status update to frontend
    stage_id = "baseline_tests"
    if environment == "uplift_env" and output_dir == "essvt_output":
        stage_id = "essvt_uplifted_tests"
    elif environment == "uplift_env" and output_dir == "final_output":
        stage_id = "final_tests"
    
    send_event(stage_id, "status", "running")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Run Robot Framework tests using docker-compose
    command = [
        "docker-compose", "run", "--rm",
        "-v", f"{os.path.abspath(output_dir)}:/app/output",
        environment,
        "python", "-m", "robot.run", "--outputdir", "/app/output", "/app/ESSVT/tests.robot"
    ]
    
    stdout, stderr, returncode = run_command(command)
    
    if stderr:
        test_summary.append(f"\nErrors during test execution:")
        test_summary.append(stderr)
        send_event(stage_id, "log", stderr)
    
    output_xml_path = os.path.join(output_dir, "output.xml")
    if os.path.exists(output_xml_path):
        print(f"Test results saved to: {output_xml_path}")
        
        # Parse test results for summary
        try:
            tree = ET.parse(output_xml_path)
            root = tree.getroot()
            stats = root.find('.//total/stat')
            pass_count = int(stats.get('pass', 0))
            fail_count = int(stats.get('fail', 0))
            
            test_summary.append(f"\nTest Results:")
            test_summary.append(f"- Tests passed: {pass_count}")
            test_summary.append(f"- Tests failed: {fail_count}")
            
            summary_text = f"Test Results: {pass_count} passed, {fail_count} failed"
            send_event(stage_id, "summary", summary_text)
            
            # Get details of failed tests
            if fail_count > 0:
                test_summary.append("\nFailed Tests:")
                for test in root.findall('.//test'):
                    status = test.find('status')
                    if status is not None and status.get('status') == 'FAIL':
                        test_name = test.get('name')
                        message = status.text or "No error message"
                        test_summary.append(f"- {test_name}: {message}")
                        send_event(stage_id, "log", f"Failed Test: {test_name} - {message}")
            
            # Create report links
            report_path = os.path.join(output_dir, "report.html")
            log_path = os.path.join(output_dir, "log.html")
            
            # Make paths relative for the frontend
            report_links = {
                "report": f"/{output_dir}/report.html",
                "log": f"/{output_dir}/log.html"
            }
            send_event(stage_id, "report_link", json.dumps(report_links))
            
            # Mark as completed
            send_event(stage_id, "status", "completed")
            
        except Exception as e:
            test_summary.append(f"\nError parsing test results: {e}")
            send_event(stage_id, "log", f"Error parsing test results: {e}")
            send_event(stage_id, "status", "error")
        
        return output_xml_path, "\n".join(test_summary)
    else:
        error_msg = f"Warning: output.xml not found in {output_dir}"
        print(error_msg)
        test_summary.append(f"\n{error_msg}")
        send_event(stage_id, "log", error_msg)
        send_event(stage_id, "status", "error")
        return None, "\n".join(test_summary)

def find_files_by_extension(repo_path, extensions):
    """Find all files with specified extensions in the repository."""
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        # Skip hidden directories and build directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', '__pycache__', 'node_modules', '.git']]
        for file in filenames:
            if any(file.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, file))
    
    # Remove duplicates
    return list(set(files))

def find_java_files(repo_path):
    """Find all Java files in the repository."""
    return find_files_by_extension(repo_path, ['.java'])

def find_python_files(repo_path):
    """Find all Python files in the repository."""
    return find_files_by_extension(repo_path, ['.py'])

def get_file_type(file_path):
    """Determine the type of file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.java':
        return 'java'
    elif ext == '.py':
        return 'python'
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        return 'javascript'
    elif ext in ['.cpp', '.cc', '.cxx', '.c']:
        return 'cpp'
    else:
        return 'unknown'

def uplift_adaptation_pod_modules(repo_path, uplift_config):
    """Uplift specific adaptation pod modules."""
    print(f"\n=== Uplifting adaptation pod modules: {repo_path} ===")
    uplift_summary = []
    uplift_summary.append(f"Repository: {repo_path}")
    uplift_summary.append(f"Uplift Type: {uplift_config.get('type', 'unknown')}")
    uplift_summary.append(f"Target Version: {uplift_config.get('target_version', 'unknown')}")
    
    selected_modules = uplift_config.get('selected_modules', [])
    if not selected_modules:
        message = "No modules selected for uplift"
        print(message)
        uplift_summary.append(f"\n{message}")
        send_event("uplifting_python", "log", message)
        send_event("uplifting_python", "status", "error")
        return False
    
    uplift_summary.append(f"\nSelected modules: {', '.join(selected_modules)}")
    send_event("uplifting_python", "log", f"Selected modules: {', '.join(selected_modules)}")
    
    success_count = 0
    total_modules = len(selected_modules)
    
    for module in selected_modules:
        module_path = os.path.join(repo_path, module)
        if not os.path.exists(module_path):
            print(f"Module path does not exist: {module_path}")
            continue
            
        print(f"\nProcessing module: {module}")
        uplift_summary.append(f"\n--- Processing module: {module} ---")
        send_event("uplifting_python", "log", f"\nProcessing module: {module}")
        
        # Find Python files in the module
        python_files = find_python_files(module_path)
        
        if not python_files:
            print(f"No Python files found in module: {module}")
            continue
            
        for file_path in python_files:
            print(f"Processing file: {file_path}")
            try:
                # Read original code
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_code = f.read()
                
                # Create analysis for Python file
                analysis_findings = f"Python code analysis for {module} module to Python {uplift_config.get('target_version', '3.9')}"
                
                # Get LLM suggestion
                updated_code, change_summary = get_llm_suggestion(
                    original_code, 
                    analysis_findings, 
                    uplift_config.get('target_version', '3.9'), 
                    selected_libraries
                )
                
                if updated_code:
                    # Save updated code
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_code)
                    
                    # Send LLM change event
                    llm_change_data = {
                        "title": f"Uplifted {os.path.basename(file_path)}",
                        "description": f"Successfully modernized Python file in {module} module",
                        "file": file_path,
                        "stage": "uplifting_python",
                        "details": change_summary,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    send_llm_change_event(llm_change_data)
                    
                    print(f"Successfully uplifted: {file_path}")
                    uplift_summary.append(f"\n✓ Successfully uplifted: {file_path}")
                    send_event("uplifting_python", "log", f"✓ Successfully uplifted: {file_path}")
                    success_count += 1
                else:
                    error_msg = f"Failed to uplift: {file_path}"
                    print(error_msg)
                    uplift_summary.append(f"\n❌ {error_msg}")
                    send_event("uplifting_python", "log", f"❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                print(error_msg)
                uplift_summary.append(f"\n❌ {error_msg}")
                send_event("uplifting_python", "log", f"❌ {error_msg}")
    
    result_msg = f"\nUplift completed: {success_count} files successfully uplifted across {total_modules} modules"
    print(result_msg)
    uplift_summary.append(result_msg)
    send_event("uplifting_python", "summary", result_msg)
    
    if success_count > 0:
        send_event("uplifting_python", "status", "completed")
    else:
        send_event("uplifting_python", "status", "error")
    
    log_summary(f"ADAPTATION POD UPLIFT", "\n".join(uplift_summary))
    return success_count > 0

def uplift_repository(repo_path, uplift_config):
    """Uplift files in a repository based on configuration."""
    print(f"\n=== Uplifting repository: {repo_path} ===")
    uplift_summary = []
    uplift_summary.append(f"Repository: {repo_path}")
    uplift_summary.append(f"Uplift Type: {uplift_config.get('type', 'unknown')}")
    uplift_summary.append(f"Target Version: {uplift_config.get('target_version', 'unknown')}")
    
    # Determine stage ID based on repository and uplift type
    uplift_type = uplift_config.get('type', 'java')
    if uplift_type == 'java':
        stage_id = "uplifting_essvt" if "ESSVT" in repo_path else "uplifting_source"
    else:
        stage_id = f"uplifting_{uplift_type}"
    
    send_event(stage_id, "status", "running")
    
    # Special handling for adaptation pod
    if uplift_type == 'python' and uplift_config.get('selected_modules'):
        return uplift_adaptation_pod_modules(repo_path, uplift_config)
    
    # Find files based on uplift type
    files_to_uplift = []
    if uplift_type == 'java':
        files_to_uplift = find_java_files(repo_path)
        file_extensions = ['.java']
    elif uplift_type == 'python':
        files_to_uplift = find_python_files(repo_path)
        file_extensions = ['.py']
    else:
        # For unknown types, try to find any files
        files_to_uplift = find_files_by_extension(repo_path, ['.java', '.py', '.js', '.ts', '.cpp', '.c'])
        file_extensions = ['.java', '.py', '.js', '.ts', '.cpp', '.c']
    
    if not files_to_uplift:
        message = f"No {uplift_type} files found in {repo_path}"
        print(message)
        uplift_summary.append(f"\n{message}")
        send_event(stage_id, "log", message)
        send_event(stage_id, "status", "error")
        log_summary(f"UPLIFT: {os.path.basename(repo_path).upper()}", "\n".join(uplift_summary))
        return False
    
    uplift_summary.append(f"\nFound {len(files_to_uplift)} {uplift_type} files to uplift:")
    send_event(stage_id, "log", f"Found {len(files_to_uplift)} {uplift_type} files to uplift")
    for file_path in files_to_uplift:
        uplift_summary.append(f"- {file_path}")
        send_event(stage_id, "log", f"- {file_path}")
    
    success_count = 0
    total_files = len(files_to_uplift)
    
    for file_path in files_to_uplift:
        print(f"\nProcessing: {file_path}")
        uplift_summary.append(f"\n--- Processing: {file_path} ---")
        send_event(stage_id, "log", f"\nProcessing: {file_path}")
        
        try:
            # Read original code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Get file type
            file_type = get_file_type(file_path)
            
            # Analyze code based on file type
            if file_type == 'java':
                modernizer_findings = analyze_with_modernizer(file_path, uplift_config.get('target_version', '17'))
                if modernizer_findings is None:
                    modernizer_findings = "Modernizer analysis unavailable"
            else:
                # For non-Java files, create a simple analysis
                modernizer_findings = f"Code analysis for {file_type} file to {uplift_config.get('target_version', 'latest')}"
            
            print(f"Analysis findings: {modernizer_findings}")
            uplift_summary.append(f"\nAnalysis findings:")
            uplift_summary.append(modernizer_findings)
            send_event(stage_id, "log", f"Analysis findings: {modernizer_findings}")
            
            # Get LLM suggestion with RAG context
            updated_code, change_summary = get_llm_suggestion(
                original_code, 
                modernizer_findings, 
                uplift_config.get('target_version', 'latest'), 
                selected_libraries,
                file_type
            )
            
            if updated_code:
                # Save updated code
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_code)
                
                # Send LLM change event to frontend
                llm_change_data = {
                    "title": f"Uplifted {os.path.basename(file_path)}",
                    "description": f"Successfully modernized {file_type} file to {uplift_config.get('target_version', 'latest')}",
                    "file": file_path,
                    "stage": stage_id,
                    "details": change_summary,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                send_llm_change_event(llm_change_data)
                
                # Save change summary to our uplift summary
                uplift_summary.append(f"\nLLM Change Summary:")
                uplift_summary.append(change_summary)
                send_event(stage_id, "log", f"LLM Change Summary: {change_summary}")
                
                print(f"Successfully uplifted: {file_path}")
                uplift_summary.append(f"\n✓ Successfully uplifted: {file_path}")
                send_event(stage_id, "log", f"✓ Successfully uplifted: {file_path}")
                success_count += 1
            else:
                error_msg = f"Failed to uplift: {file_path}"
                print(error_msg)
                uplift_summary.append(f"\n❌ {error_msg}")
                send_event(stage_id, "log", f"❌ {error_msg}")
                
                # Send LLM change event for error
                llm_change_data = {
                    "title": f"Failed to uplift {os.path.basename(file_path)}",
                    "description": f"Failed to modernize {file_type} file to {uplift_config.get('target_version', 'latest')}",
                    "file": file_path,
                    "stage": stage_id,
                    "details": error_msg,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                send_llm_change_event(llm_change_data)
                
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            print(error_msg)
            uplift_summary.append(f"\n❌ {error_msg}")
            send_event(stage_id, "log", f"❌ {error_msg}")
            
            # Send LLM change event for exception
            llm_change_data = {
                "title": f"Error processing {os.path.basename(file_path)}",
                "description": f"Exception occurred while processing file",
                "file": file_path,
                "stage": stage_id,
                "details": error_msg,
                "timestamp": datetime.datetime.now().isoformat()
            }
            send_llm_change_event(llm_change_data)
    
    result_msg = f"\nUplift completed: {success_count}/{total_files} files successfully uplifted"
    print(result_msg)
    uplift_summary.append(result_msg)
    send_event(stage_id, "summary", f"Uplift completed: {success_count}/{total_files} files successfully uplifted")
    
    if success_count > 0:
        send_event(stage_id, "status", "completed")
    else:
        send_event(stage_id, "status", "error")
    
    log_summary(f"UPLIFT: {os.path.basename(repo_path).upper()}", "\n".join(uplift_summary))
    return success_count > 0

def compare_robot_outputs(baseline_output_path, new_output_path):
    """Compare Robot Framework output.xml files to check for differences."""
    print(f"\n=== Comparing test outputs ===")
    print(f"Baseline: {baseline_output_path}")
    print(f"New: {new_output_path}")
    
    comparison_summary = []
    comparison_summary.append(f"Baseline: {baseline_output_path}")
    comparison_summary.append(f"New: {new_output_path}")
    
    if not os.path.exists(baseline_output_path):
        error_msg = f"Error: Baseline output file not found: {baseline_output_path}"
        print(error_msg)
        comparison_summary.append(f"\n❌ {error_msg}")
        return False, "\n".join(comparison_summary)
    
    if not os.path.exists(new_output_path):
        error_msg = f"Error: New output file not found: {new_output_path}"
        print(error_msg)
        comparison_summary.append(f"\n❌ {error_msg}")
        return False, "\n".join(comparison_summary)
    
    try:
        # Parse baseline results
        baseline_tree = ET.parse(baseline_output_path)
        baseline_root = baseline_tree.getroot()
        baseline_stats = baseline_root.find('.//total/stat')
        baseline_pass = int(baseline_stats.get('pass', 0))
        baseline_fail = int(baseline_stats.get('fail', 0))
        
        # Parse new results
        new_tree = ET.parse(new_output_path)
        new_root = new_tree.getroot()
        new_stats = new_root.find('.//total/stat')
        new_pass = int(new_stats.get('pass', 0))
        new_fail = int(new_stats.get('fail', 0))
        
        print(f"Baseline results: {baseline_pass} passed, {baseline_fail} failed")
        print(f"New results: {new_pass} passed, {new_fail} failed")
        
        comparison_summary.append(f"\nBaseline results: {baseline_pass} passed, {baseline_fail} failed")
        comparison_summary.append(f"New results: {new_pass} passed, {new_fail} failed")
        
        # Find which tests changed status
        if baseline_pass != new_pass or baseline_fail != new_fail:
            comparison_summary.append("\nTests with changed status:")
            
            baseline_tests = {}
            for test in baseline_root.findall('.//test'):
                name = test.get('name')
                status = test.find('status').get('status')
                baseline_tests[name] = status
            
            for test in new_root.findall('.//test'):
                name = test.get('name')
                status = test.find('status').get('status')
                if name in baseline_tests and baseline_tests[name] != status:
                    comparison_summary.append(f"- {name}: {baseline_tests[name]} → {status}")
                    if status == 'FAIL':
                        message = test.find('status').text or "No error message"
                        comparison_summary.append(f"  Error: {message}")
        
        # Compare results
        if baseline_pass == new_pass and baseline_fail == new_fail:
            print("✅ Test results are identical - uplift successful!")
            comparison_summary.append("\n✅ Test results are identical - uplift successful!")
            return True, "\n".join(comparison_summary)
        else:
            print("❌ Test results differ - uplift may have introduced issues")
            comparison_summary.append("\n❌ Test results differ - uplift may have introduced issues")
            return False, "\n".join(comparison_summary)
            
    except Exception as e:
        error_msg = f"Error comparing outputs: {e}"
        print(error_msg)
        comparison_summary.append(f"\n❌ {error_msg}")
        return False, "\n".join(comparison_summary)

def send_event(stage, event_type, payload):
    """Send an event to the frontend via the event queue."""
    event = {
        "stage": stage,
        "type": event_type,
        "payload": payload
    }
    event_queue.put(event)
    # Force a small delay to ensure events are processed in order
    time.sleep(0.05)

def send_llm_change_event(change_data):
    """Send an LLM change event to the frontend."""
    event = {
        "stage": "llm_changes",
        "type": "llm_change",
        "payload": change_data
    }
    event_queue.put(event)
    # Force a small delay to ensure events are processed in order
    time.sleep(0.05)

def uplift_process():
    """Run the complete uplift process with web interface support."""
    global process_running, current_stage, process_status, uplift_config
    
    if process_running:
        print("Process is already running")
        return
    
    process_running = True
    current_stage = "starting"
    process_status = "RUNNING"
    
    try:
        # Clear any previous events
        while not event_queue.empty():
            event_queue.get()
        
        # Get uplift configuration
        uplift_type = uplift_config.get('type', 'java')
        target_version = uplift_config.get('target_version', '17')
        source_path = uplift_config.get('source_path', 'repositories/ESSVT')
        
        # Define stages based on uplift type
        if uplift_type == 'java':
            stages = ["baseline_tests", "uplifting_essvt", "essvt_uplifted_tests", "uplifting_source", "final_tests"]
        elif uplift_type == 'python':
            stages = ["baseline_tests", "uplifting_python", "python_uplifted_tests", "uplifting_source", "final_tests"]
        else:
            stages = ["baseline_tests", f"uplifting_{uplift_type}", f"{uplift_type}_uplifted_tests", "uplifting_source", "final_tests"]
        
        # Send initial stage setup
        for stage in stages:
            send_event(stage, "status", "pending")
        
        # Step 1: Run baseline tests on production environment
        print(f"\n📋 Step 1: Running baseline tests for {uplift_type}...")
        send_event("baseline_tests", "status", "running")
        baseline_output, baseline_summary = run_tests("production_env", "baseline_output")
        log_summary("BASELINE TEST EXECUTION", baseline_summary)
        if not baseline_output:
            print("❌ Failed to run baseline tests")
            log_summary("UPLIFT SIMULATION ERROR", "Failed to run baseline tests.")
            send_event("baseline_tests", "status", "error")
            process_status = "FINISHED"
            return
        
        # Explicitly mark baseline tests as completed
        send_event("baseline_tests", "status", "completed")
        
        # Check if process was canceled
        if process_status == "CANCELED":
            log_summary("UPLIFT SIMULATION", "Process was canceled by user")
            send_event("system", "process_status", "finished")
            return
        
        # Step 2: Uplift test code
        print(f"\n🔧 Step 2: Uplifting {uplift_type} test code...")
        test_stage = f"uplifting_{uplift_type}"
        send_event(test_stage, "status", "running")
        
        test_config = {
            'type': uplift_type,
            'target_version': target_version,
            'source_path': source_path
        }
        
        if not uplift_repository(source_path, test_config):
            print(f"❌ Failed to uplift {uplift_type} code")
            log_summary("UPLIFT SIMULATION ERROR", f"Failed to uplift {uplift_type} code.")
            send_event(test_stage, "status", "error")
            process_status = "FINISHED"
            return
        
        # Explicitly mark ESSVT uplift as completed
        send_event("uplifting_essvt", "status", "completed")
        
        # Check if process was canceled
        if process_status == "CANCELED":
            log_summary("UPLIFT SIMULATION", "Process was canceled by user")
            send_event("system", "process_status", "finished")
            return
        
        # Step 3: Test uplifted ESSVT against original source code
        print("\n🧪 Step 3: Testing uplifted ESSVT...")
        send_event("essvt_uplifted_tests", "status", "running")
        essvt_output, essvt_test_summary = run_tests("uplift_env", "essvt_output")
        log_summary("ESSVT UPLIFTED TEST EXECUTION", essvt_test_summary)
        if not essvt_output:
            print("❌ Failed to run ESSVT tests")
            log_summary("UPLIFT SIMULATION ERROR", "Failed to run ESSVT tests.")
            send_event("essvt_uplifted_tests", "status", "error")
            process_status = "FINISHED"
            return
        
        # Step 4: Compare ESSVT test results
        print("\n📊 Step 4: Comparing ESSVT test results...")
        essvt_success, essvt_comparison = compare_robot_outputs(baseline_output, essvt_output)
        log_summary("ESSVT TEST COMPARISON", essvt_comparison)
        
        # Explicitly mark ESSVT tests as completed
        send_event("essvt_uplifted_tests", "status", "completed")
        
        # Check if process was canceled
        if process_status == "CANCELED":
            log_summary("UPLIFT SIMULATION", "Process was canceled by user")
            send_event("system", "process_status", "finished")
            return
        
        # Step 5: Uplift source code
        print("\n🔧 Step 5: Uplifting source code...")
        send_event("uplifting_source", "status", "running")
        if not uplift_repository("repositories/source-code", "17"):
            print("❌ Failed to uplift source code")
            log_summary("UPLIFT SIMULATION ERROR", "Failed to uplift source code.")
            send_event("uplifting_source", "status", "error")
            process_status = "FINISHED"
            return
        
        # Explicitly mark source code uplift as completed
        send_event("uplifting_source", "status", "completed")
        
        # Check if process was canceled
        if process_status == "CANCELED":
            log_summary("UPLIFT SIMULATION", "Process was canceled by user")
            send_event("system", "process_status", "finished")
            return
        
        # Step 6: Final test with uplifted ESSVT and uplifted source code
        print("\n🧪 Step 6: Final testing with uplifted code...")
        send_event("final_tests", "status", "running")
        final_output, final_test_summary = run_tests("uplift_env", "final_output")
        log_summary("FINAL TEST EXECUTION", final_test_summary)
        if not final_output:
            print("❌ Failed to run final tests")
            log_summary("UPLIFT SIMULATION ERROR", "Failed to run final tests.")
            send_event("final_tests", "status", "error")
            process_status = "FINISHED"
            return
        
        # Step 7: Compare final results
        print("\n📊 Step 7: Comparing final test results...")
        final_success, final_comparison = compare_robot_outputs(baseline_output, final_output)
        log_summary("FINAL TEST COMPARISON", final_comparison)
        
        # Explicitly mark final tests as completed
        send_event("final_tests", "status", "completed")
        
        # Add ESSVT validation after ESSVT uplifted tests - COMMENTED OUT FOR LOCAL-ONLY MODE
        # if ESSVT_CONFIG["enabled"]:
        #     print("\n🌐 Step 4.5: Running ESSVT validation...")
        #     current_stage = "essvt_validation"
        #     send_event("essvt_validation", "status", "running")
        #     
        #     essvt_success = run_essvt_tests("repositories/ESSVT", "ESSVT-Validation", "essvt_validation")
        #     
        #     if essvt_success:
        #         send_event("essvt_validation", "status", "completed")
        #         send_event("essvt_validation", "summary", "✅ ESSVT validation completed successfully")
        #         
        #         # Wait for first execution to complete before second validation
        #         print("⏳ Waiting for ESSVT execution to complete before final validation...")
        #         send_event("essvt_validation", "log", "⏳ Waiting for ESSVT execution to complete...")
        #         time.sleep(120)  # Wait 2 minutes
        #     else:
        #         send_event("essvt_validation", "status", "error")
        #         send_event("essvt_validation", "summary", "❌ ESSVT validation failed")
        
        # Add final ESSVT validation after final tests - COMMENTED OUT FOR LOCAL-ONLY MODE
        # if ESSVT_CONFIG["enabled"] and essvt_success:  # Only run if first ESSVT validation succeeded
        #     print("\n🌐 Step 7.5: Running final ESSVT validation...")
        #     current_stage = "final_essvt_validation"
        #     send_event("final_essvt_validation", "status", "running")
        #     
        #     final_essvt_success = run_essvt_tests("repositories/source-code", "Final-Validation", "final_essvt_validation")
        #     
        #     if final_essvt_success:
        #         send_event("final_essvt_validation", "status", "completed")
        #         send_event("final_essvt_validation", "summary", "✅ Final ESSVT validation completed successfully")
        #     else:
        #         send_event("final_essvt_validation", "status", "error")
        #         send_event("final_essvt_validation", "summary", "❌ Final ESSVT validation failed")
        
        # Final report
        print("\n" + "="*60)
        print("🎯 FINAL UPLIFT SIMULATION REPORT")
        print("="*60)
        
        final_report = []
        if essvt_success and final_success:
            success_msg = "✅ SUCCESS: Java JDK uplift completed successfully!"
            print(success_msg)
            final_report.append(success_msg)
            final_report.append("   - All test results match baseline")
            final_report.append("   - Code has been successfully uplifted to JDK 17")
        else:
            failure_msg = "❌ FAILURE: Java JDK uplift encountered issues"
            print(failure_msg)
            final_report.append(failure_msg)
            if not essvt_success:
                essvt_fail_msg = "   - ESSVT test uplift validation failed"
                print(essvt_fail_msg)
                final_report.append(essvt_fail_msg)
            if not final_success:
                final_fail_msg = "   - Final validation failed"
                print(final_fail_msg)
                final_report.append(final_fail_msg)
            check_msg = "   - Check summary file for details"
            print(check_msg)
            final_report.append(check_msg)
        
        print("="*60)
        log_summary("FINAL UPLIFT SIMULATION REPORT", "\n".join(final_report))
        
        # Save summary to file
        summary_file = save_summary()
        print(f"Review the detailed summary in {summary_file} for more information.")
        
        process_status = "FINISHED"
        
        # Send event to notify frontend that process is complete
        send_event("system", "process_status", "finished")
    
    except Exception as e:
        print(f"Error in uplift process: {e}")
        log_summary("UPLIFT SIMULATION ERROR", f"Unexpected error: {e}")
        process_status = "FINISHED"
        
        # Send event to notify frontend that process has errored
        send_event("system", "process_status", "finished")

# ESSVT Functions - COMMENTED OUT FOR LOCAL-ONLY MODE
# def get_essvt_token():
#     """Get authentication token from ESSVT"""
#     auth_url = f"{ESSVT_CONFIG['base_url']}/auth/realms/essvt/protocol/openid-connect/token"
#     
#     auth_headers = {
#         "Content-Type": "application/x-www-form-urlencoded"
#     }
#     
#     auth_payload = {
#         "grant_type": "password",
#         "client_id": ESSVT_CONFIG["client_id"],
#         "username": ESSVT_CONFIG["username"],
#         "password": ESSVT_CONFIG["password"]
#     }
#     
#     try:
#         response = requests.post(auth_url, headers=auth_headers, data=auth_payload, verify=False)
#         
#         if response.status_code == 200:
#             token = response.json()["access_token"]
#             print(f"✅ ESSVT authentication successful")
#             return token
#         else:
#             print(f"❌ ESSVT authentication failed: {response.status_code}")
#             print(f"Response: {response.text}")
#             return None
#             
#     except Exception as e:
#         print(f"❌ Error getting ESSVT token: {e}")
#         return None

# def create_test_package_for_essvt(repo_path, output_path):
#     """Create a ZIP package for ESSVT upload"""
#     print(f"📦 Creating ESSVT test package from {repo_path}")
#     
#     try:
#         # Debug: Check what files exist before packaging
#         print(f"🔍 Scanning directory: {repo_path}")
#         for root, dirs, files in os.walk(repo_path):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 print(f"  Found: {file_path}")
#         
#         with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#             robot_file_found = False
#             
#             # Add all files from the repository
#             for root, dirs, files in os.walk(repo_path):
#                 for file in files:
#                     file_path = os.path.join(root, file)
#                     arc_name = os.path.relpath(file_path, repo_path)
#                     zipf.write(file_path, arc_name)
#                     print(f"📄 Added to ZIP: {arc_name}")
#                     
#                     if file.endswith('.robot'):
#                         robot_file_found = True
#             
#             # If no robot file found, add one from legacy_code or create minimal one
#             if not robot_file_found:
#                 legacy_robot = 'legacy_code/tests.robot'
#                 if os.path.exists(legacy_robot):
#                     zipf.write(legacy_robot, 'tests.robot')
#                     print(f"📄 Added to ZIP: tests.robot (from legacy_code)")
#                 else:
#                     # Create minimal robot file for ESSVT
#                     minimal_robot_content = """*** Settings ***
# Documentation     ESSVT Validation Test Suite for JDK Uplift
# Library           BuiltIn
# 
# *** Test Cases ***
# ESSVT Validation Test
#     [Documentation]    Basic test to verify ESSVT integration works
#     [Tags]             validation
#     Log To Console     ESSVT validation test executing
#     Should Be True     ${True}    ESSVT integration test
#     Log To Console     ESSVT validation completed successfully
# 
# Java Compilation Check
#     [Documentation]    Verify Java files can be processed
#     [Tags]             java
#     Log To Console     Checking Java compilation capability
#     Should Be True     ${True}    Java compilation validation
#     Log To Console     Java compilation check passed
# """
#                     zipf.writestr('tests.robot', minimal_robot_content)
#                     print(f"📄 Added to ZIP: tests.robot (minimal validation)")
#         
#         # Debug: Verify ZIP contents
#         print(f"🔍 Verifying ZIP contents:")
#         with zipfile.ZipFile(output_path, 'r') as zipf:
#             for name in zipf.namelist():
#                 print(f"  ✓ ZIP contains: {name}")
#                 
#         print(f"✅ Test package created: {output_path}")
#         return True
#         
#     except Exception as e:
#         print(f"❌ Error creating test package: {e}")
#         return False

# def upload_to_essvt(zip_path, token, stage_id):
#     """Upload test package to ESSVT project"""
#     url = f"{ESSVT_CONFIG['base_url']}/api/v1/projects/{ESSVT_CONFIG['project_id']}/content"
#     
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
#     
#     print(f"⬆️ Uploading {os.path.basename(zip_path)} to ESSVT...")
#     send_event(stage_id, "log", f"Uploading {os.path.basename(zip_path)} to ESSVT project...")
#     
#     try:
#         with open(zip_path, "rb") as f:
#             files = {'filename': f}
#             response = requests.put(url, headers=headers, files=files, verify=False)
#             
#         if response.status_code in [200, 201, 204]:
#             print(f"✅ Upload successful")
#             send_event(stage_id, "log", "✅ Upload to ESSVT successful")
#             return True
#         else:
#             error_msg = f"Upload failed: {response.status_code} - {response.text}"
#             print(f"❌ {error_msg}")
#             send_event(stage_id, "log", f"❌ {error_msg}")
#             return False
#             
#     except Exception as e:
#         error_msg = f"Error uploading to ESSVT: {e}"
#         print(f"❌ {error_msg}")
#         send_event(stage_id, "log", f"❌ {error_msg}")
#         return False

# def create_essvt_order(token, order_name, stage_id):
#     """Create an order in ESSVT"""
#     url = f"{ESSVT_CONFIG['base_url']}/api/v1/orders"
#     
#     payload = {
#         "orderName": order_name,
#         "description": f"JDK Uplift Test Order - {order_name}",
#         "projectId": ESSVT_CONFIG["project_id"],
#         "executor": "robot",
#         "pabotOptions": [],
#         "robotOptions": ["--loglevel DEBUG"],
#         "robotVariables": [],
#         "testDataType": "suite",
#         "testDataList": []  # ← Fix: Empty array instead of array with empty object
#     }
#     
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
#     
#     print(f"📋 Creating ESSVT order: {order_name}")
#     send_event(stage_id, "log", f"Creating ESSVT order: {order_name}")
#     
#     try:
#         response = requests.post(url, headers=headers, json=payload, verify=False)
#         
#         if response.status_code == 201:
#             order_id = response.json().get('orderId')
#             print(f"✅ Order created with ID: {order_id}")
#             send_event(stage_id, "log", f"✅ Order created with ID: {order_id}")
#             return order_id
#         else:
#             error_msg = f"Order creation failed: {response.status_code} - {response.text}"
#             print(f"❌ {error_msg}")
#             send_event(stage_id, "log", f"❌ {error_msg}")
#             return None
#             
#     except Exception as e:
#         error_msg = f"Error creating ESSVT order: {e}"
#         print(f"❌ {error_msg}")
#         send_event(stage_id, "log", f"❌ {error_msg}")
#         return None

# def create_essvt_execution(token, order_id, execution_name, stage_id):
#     """Create execution from ESSVT order"""
#     url = f"{ESSVT_CONFIG['base_url']}/api/v1/executions/orderStart"
#     
#     # Generate unique execution name with timestamp
#     import time
#     unique_execution_name = f"{execution_name}-{int(time.time())}"
#     
#     payload = {
#         "orderId": order_id,
#         "executionName": unique_execution_name,  # Use unique name
#         "autoStart": "true",
#         "retry": {
#             "autoRetry": True,
#             "rerunFailed": False,
#             "mergeResult": True,
#             "maxRetryCount": 1
#         }
#     }
#     
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
#     
#     print(f"🚀 Creating ESSVT execution: {unique_execution_name}")
#     send_event(stage_id, "log", f"Creating ESSVT execution: {unique_execution_name}")
#     
#     try:
#         response = requests.post(url, headers=headers, json=payload, verify=False)
#         
#         if response.status_code in [201, 202]:  # Accept both 201 and 202
#             execution_id = response.json().get('executionId')
#             print(f"✅ Execution created with ID: {execution_id}")
#             send_event(stage_id, "log", f"✅ Execution created with ID: {execution_id}")
#             return execution_id
#         else:
#             error_msg = f"Execution creation failed: {response.status_code} - {response.text}"
#             print(f"❌ {error_msg}")
#             send_event(stage_id, "log", f"❌ {error_msg}")
#             return None
#             
#     except Exception as e:
#         error_msg = f"Error creating ESSVT execution: {e}"
#         print(f"❌ {error_msg}")
#         send_event(stage_id, "log", f"❌ {error_msg}")
#         return None

# def monitor_essvt_execution(token, execution_id, stage_id, timeout_minutes=30):
#     """Monitor ESSVT execution until completion"""
#     url = f"{ESSVT_CONFIG['base_url']}/api/v1/executions/{execution_id}"
#     
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
#     
#     print(f"⏳ Monitoring ESSVT execution: {execution_id}")
#     send_event(stage_id, "log", f"Monitoring ESSVT execution: {execution_id}")
#     
#     import time
#     start_time = time.time()
#     timeout_seconds = timeout_minutes * 60
#     
#     while True:
#         try:
#             if time.time() - start_time > timeout_seconds:
#                 error_msg = f"Execution monitoring timeout after {timeout_minutes} minutes"
#                 print(f"⏰ {error_msg}")
#                 send_event(stage_id, "log", f"⏰ {error_msg}")
#                 return None, "TIMEOUT"
#             
#             response = requests.get(url, headers=headers, verify=False)
#             
#             if response.status_code == 200:
#                 execution_data = response.json()
#                 status = execution_data.get('status', 'UNKNOWN')
#                 
#                 print(f"📊 Execution status: {status}")
#                 send_event(stage_id, "log", f"Execution status: {status}")
#                 
#                 if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
#                     # Get test results
#                     passed = execution_data.get('passedTests', 0)
#                     failed = execution_data.get('failedTests', 0)
#                     total = execution_data.get('totalTests', 0)
#                     
#                     result_summary = f"ESSVT Results: {passed} passed, {failed} failed out of {total} total"
#                     print(f"📋 {result_summary}")
#                     send_event(stage_id, "log", result_summary)
#                     
#                     return execution_data, status
#                     
#                 # Wait before next check
#                 time.sleep(30)
#                 
#             else:
#                 error_msg = f"Error checking execution status: {response.status_code}"
#                 print(f"❌ {error_msg}")
#                 send_event(stage_id, "log", f"❌ {error_msg}")
#                 return None, "ERROR"
#                 
#         except Exception as e:
#             error_msg = f"Error monitoring execution: {e}"
#             print(f"❌ {error_msg}")
#             send_event(stage_id, "log", f"❌ {error_msg}")
#             return None, "ERROR"

# def run_essvt_tests(repo_path, test_name, stage_id):
#     """Complete ESSVT test workflow"""
#     if not ESSVT_CONFIG["enabled"]:
#         print("ESSVT is disabled, skipping...")
#         return True
#     
#     try:
#         # Step 1: Get authentication token
#         token = get_essvt_token()
#         if not token:
#             return False
#         
#         # Step 2: Create test package
#         import time
#         timestamp = int(time.time())
#         zip_path = f"temp_{test_name}-{timestamp}.zip"
#         
#         if not create_test_package_for_essvt(repo_path, zip_path):
#             return False
#         
#         # Step 3: Upload to ESSVT
#         if not upload_to_essvt(zip_path, token, stage_id):
#             os.remove(zip_path)
#             return False
#         
#         # Step 4: Create order with unique name
#         order_name = f"JDK-Uplift-{test_name}-{timestamp}"
#         order_id = create_essvt_order(token, order_name, stage_id)
#         if not order_id:
#             os.remove(zip_path)
#             return False
#         
#         # Step 5: Create and start execution with unique name
#         execution_name = f"Execution-{test_name}"  # Unique timestamp added in function
#         execution_id = create_essvt_execution(token, order_id, execution_name, stage_id)
#         if not execution_id:
#             os.remove(zip_path)
#             return False
#         
#         # Step 6: Monitor execution (optional - can be implemented later)
#         # execution_data, final_status = monitor_essvt_execution(token, execution_id, stage_id)
#         
#         # Cleanup
#         os.remove(zip_path)
#         
#         # For now, consider ESSVT validation successful if execution was created
#         return True
#         
#     except Exception as e:
#         error_msg = f"ESSVT test execution failed: {e}"
#         print(f"❌ {error_msg}")
#         send_event(stage_id, "log", f"❌ {error_msg}")
#         return False

# def wait_for_project_available(token, stage_id, max_wait_minutes=10):
#     """Wait for ESSVT project to be available (no running executions)"""
#     url = f"{ESSVT_CONFIG['base_url']}/api/v1/projects/{ESSVT_CONFIG['project_id']}"
#     
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
#     
#     for attempt in range(max_wait_minutes):
#         try:
#             response = requests.get(url, headers=headers, verify=False)
#             if response.status_code == 200:
#                 project_data = response.json()
#                 # Check if there are running executions
#                 running_executions = project_data.get('runningExecutions', [])
#                 if not running_executions:
#                     return True
#                 
#                 send_event(stage_id, "log", f"⏳ Waiting for {len(running_executions)} running execution(s) to complete...")
#                 time.sleep(60)  # Wait 1 minute
#             else:
#                 send_event(stage_id, "log", f"❌ Error checking project status: {response.status_code}")
#                 return False
#                 
#         except Exception as e:
#             send_event(stage_id, "log", f"❌ Error checking project availability: {e}")
#             return False
#     
#     return False  # Timeout

# Update the get_rag_context function to use the correct RAG query endpoint
def get_rag_context_wrapper(query, selected_libraries):
    """Wrapper function to maintain backward compatibility with existing calls."""
    return get_rag_context(query=query, selected_libraries=selected_libraries)

def get_rag_context(query, selected_libraries=None):
    """
    Get RAG context using the new rag_utils functions.
    This maintains backward compatibility with the existing interface.
    """
    try:
        # Create a summary of the modernization needs
        guidance_result = extract_java_guidance(
            code_issue=query,
            context=f"Selected libraries: {selected_libraries}" if selected_libraries else ""
        )
        
        if guidance_result.get("guidance_found"):
            # Format the guidance for the LLM prompt
            context_parts = []
            context_parts.append(f"GUIDANCE SUMMARY: {guidance_result['summary']}")
            
            if guidance_result.get("detailed_guidance"):
                context_parts.append("\nDETAILED GUIDANCE:")
                for item in guidance_result["detailed_guidance"][:3]:  # Limit to top 3
                    source = item.get("source", "Unknown")
                    content = item.get("content", "")[:300]  # Limit content length
                    context_parts.append(f"- From {source}: {content}")
            
            libraries_used = guidance_result.get("libraries_searched", [])
            if libraries_used:
                context_parts.append(f"\nSources: {', '.join(libraries_used[:3])}")
            
            return "\n".join(context_parts)
        else:
            return "No specific RAG guidance found for this modernization scenario."
            
    except Exception as e:
        print(f"Warning: Error getting RAG context: {e}")
        return "RAG context unavailable due to error."

# Also add a route to handle the Chrome DevTools request to reduce log noise
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    """Handle Chrome DevTools request (prevents 404 in logs)"""
    return JSONResponse(content={}, status_code=404)

# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the index.html file."""
    with open("index.html", "r", encoding="utf-8") as f:  # Add encoding="utf-8"
        return f.read()

@app.get("/favicon.ico")
async def get_favicon():
    """Serve the favicon."""
    return FileResponse("ericsson.ico")

@app.post("/start")
async def start_process(request: Request):
    """Start the uplift process."""
    global process_status, process_thread, uplift_config
    
    if process_status == "RUNNING":
        return JSONResponse(content={"success": False, "error": "Process already running"})
    
    try:
        # Get configuration from request
        data = await request.json()
        mode = data.get('mode', 'jdk')
        
        # Set uplift configuration based on mode
        if mode == 'jdk':
            uplift_config = {
                'type': 'java',
                'target_version': '17',
                'source_path': 'repositories/ESSVT'
            }
        elif mode == 'adaptation_pod':
            # For adaptation pod, we need to handle the selected modules
            selected_modules = data.get('selected_modules', [])
            uplift_config = {
                'type': 'python',
                'target_version': '3.9',
                'source_path': 'cec-adaptation-pod-main',
                'selected_modules': selected_modules
            }
        else:
            # Default to Java
            uplift_config = {
                'type': 'java',
                'target_version': '17',
                'source_path': 'repositories/ESSVT'
            }
        
        # Clear the event queue
        while not event_queue.empty():
            event_queue.get()
        
        # Start the process in a separate thread
        process_thread = threading.Thread(target=uplift_process)
        process_thread.daemon = True
        process_thread.start()
        
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        return JSONResponse(content={"success": False, "error": f"Failed to start process: {str(e)}"})

@app.post("/cancel")
async def cancel_process():
    """Cancel the uplift process."""
    global process_status
    
    if process_status != "RUNNING":
        # If no process is running, send event to update UI state
        send_event("system", "process_status", "finished")
        return JSONResponse(content={"success": False, "error": "No process running"})
    
    process_status = "CANCELED"
    return JSONResponse(content={"success": True})

@app.post("/reset")
async def reset_process():
    """Reset the uplift environment."""
    global process_status
    
    if process_status == "RUNNING":
        return JSONResponse(content={"success": False, "error": "Cannot reset while process is running"})
    
    success = reset_repositories()
    process_status = "IDLE"
    
    # Send event to reset UI
    send_event("system", "reset", "Environment reset completed")
    
    return JSONResponse(content={"success": success})

@app.get("/api/libraries")
async def get_libraries():
    """Get available libraries from RAG API."""
    try:
        # Check if token is configured
        if not LLM_API_TOKEN:
            return JSONResponse(
                content={"error": "LLM_API_TOKEN not configured"},
                status_code=500
            )
        
        # Use the unified function
        libraries = get_available_libraries()
        
        if libraries:
            return JSONResponse(content={"search_filters": libraries})
        else:
            return JSONResponse(
                content={"error": "Failed to fetch libraries"},
                status_code=500
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error fetching libraries: {str(e)}"},
            status_code=500
        )

@app.post("/api/select-libraries")
async def select_libraries(request: Request):
    """Update selected libraries for RAG context."""
    global selected_libraries
    try:
        data = await request.json()
        selected_libraries = data.get("libraries", [])
        return JSONResponse(content={"message": f"Selected {len(selected_libraries)} libraries"})
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error updating libraries: {str(e)}"},
            status_code=500
        )

@app.get("/api/selected-libraries")
async def get_selected_libraries():
    """Get currently selected libraries."""
    return JSONResponse(content={"libraries": selected_libraries})

@app.get("/stream")
async def event_stream(request: Request):
    """Server-sent events stream."""
    async def event_generator():
        # Send initial connection established event
        yield json.dumps({"type": "connection", "payload": "established"})
        
        # Keep track of last event time to detect stalled connections
        last_event_time = asyncio.get_event_loop().time()
        
        while True:
            if await request.is_disconnected():
                break
                
            # Check for new events
            if not event_queue.empty():
                event = event_queue.get()
                yield json.dumps(event)
                last_event_time = asyncio.get_event_loop().time()
            else:
                # Send heartbeat every 5 seconds if no events to keep connection alive
                current_time = asyncio.get_event_loop().time()
                if current_time - last_event_time > 5:
                    yield json.dumps({"type": "heartbeat", "payload": str(current_time)})
                    last_event_time = current_time
            
            await asyncio.sleep(0.1)
    
    return EventSourceResponse(event_generator())

# Serve static files from directories
app.mount("/baseline_output", StaticFiles(directory="baseline_output"), name="baseline_output")
app.mount("/essvt_output", StaticFiles(directory="essvt_output"), name="essvt_output")
app.mount("/final_output", StaticFiles(directory="final_output"), name="final_output")

def main():
    """Legacy CLI entry point."""
    print("This script now provides a web interface. Run with --web to start the web server.")
    print("For CLI mode, use --cli")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cli":
            # Run in CLI mode
            reset_repositories()
            uplift_process()
        elif sys.argv[1] == "--web":
            # Run in web mode - this is handled by the if __name__ == "__main__" block
            pass
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --cli for command line mode or --web for web interface")
    else:
        print("No arguments provided. Use --cli for command line mode or --web for web interface")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main()
    else:
        # Start the web server
        print("Starting web server at http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)

# Add this endpoint after your existing API routes:

@app.post("/api/preview-prompt")
async def preview_prompt(request: Request):
    """Preview the enhanced prompt that would be sent to LLM."""
    try:
        data = await request.json()
        java_code = data.get("code", "// Sample Java code")
        modernizer_findings = data.get("findings", "No modernizer findings")
        target_jdk = data.get("target_jdk", "17")
        
        # Get RAG context using the same logic as the uplift process
        rag_context = ""
        if selected_libraries:
            try:
                rag_context = get_rag_context(
                    f"Java {target_jdk} modernization", 
                    selected_libraries
                )
            except Exception as e:
                rag_context = f"RAG context error: {e}"
        
        # Build the exact same prompt that would be sent to LLM
        context_section = ""
        if rag_context and rag_context.strip():
            context_section = f"""
RELEVANT CONTEXT FROM ERICSSON PRODUCT LIBRARIES:
The following context has been retrieved from Ericsson product libraries to guide the modernization:

{rag_context}

Use this context to understand Ericsson-specific patterns and requirements when modernizing the code.
Follow any specific migration patterns or best practices mentioned in the context.
"""
        else:
            context_section = """
Note: No Ericsson-specific context was retrieved. Proceed with standard Java modernization patterns.
"""
        
        preview_prompt = f"""You are a Java expert specializing in CONSERVATIVE code modernization from older Java versions to newer ones.

CRITICAL REQUIREMENTS:
1. MAINTAIN EXACT FUNCTIONALITY - Do NOT fix bugs, errors, or improve logic
2. PRESERVE ALL EXISTING BEHAVIOR - Even if the code appears wrong or suboptimal
3. ONLY modernize APIs, syntax, and deprecated elements for Java {target_jdk} compatibility
4. If code doesn't compile due to missing dependencies, leave it as-is
5. If code has logical errors, preserve those errors exactly

The following Java code needs MINIMAL updates for Java {target_jdk} compatibility.
Modernizer static analysis found these modernization opportunities:

<modernizer_findings>
{modernizer_findings}
</modernizer_findings>

{context_section}

Your task is to ONLY:
- Replace deprecated APIs with their modern equivalents (same behavior)
- Update syntax that won't compile in Java {target_jdk}
- Address specific issues from Modernizer findings
- Consider Ericsson-specific patterns from the provided context
- Keep ALL other code exactly as-is, including any bugs or compilation issues

Format your response as:

<change_summary>
[Brief summary of ONLY the modernization changes made, referencing Modernizer findings. If no changes needed, state "No modernization required."]
</change_summary>

<updated_code>
```java
[Updated Java code with MINIMAL changes for Java {target_jdk} compatibility]
```
</updated_code>

Original Java code:
```java
{java_code}
```"""
        
        return JSONResponse(content={
            "success": True,
            "prompt": preview_prompt,
            "rag_context": rag_context,
            "context_section": context_section,
            "selected_libraries": selected_libraries,
            "target_jdk": target_jdk,
            "prompt_length": len(preview_prompt),
            "rag_context_length": len(rag_context) if rag_context else 0
        })
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": f"Error generating prompt preview: {str(e)}"},
            status_code=500
        )