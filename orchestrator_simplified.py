#!/usr/bin/env python3
"""
Simplified Orchestrator - Python Only
Focuses only on Python modernization for adaptation pod scripts.
Removes all Java/JDK functionality.
"""

import subprocess
import os
import sys
import shutil
import datetime
from genai_uplifter_simplified import analyze_python_code, get_llm_suggestion
from rag_utils import get_available_libraries
from genai_uplifter_simplified import initialize_llm_api, analyze_python_code, get_llm_suggestion
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
process_running = False
current_stage = "idle"
process_status = "IDLE"
event_queue = queue.Queue()
process_thread = None
selected_libraries = []
uplift_config = {}

# Create output directories if they don't exist
os.makedirs("baseline_output", exist_ok=True)
os.makedirs("final_output", exist_ok=True)

# FastAPI app
app = FastAPI(title="Python Modernization Tool")

def log_summary(section, content):
    """Add a section to the summary log."""
    summary_log.append(f"\n{'=' * 50}")
    summary_log.append(f"  {section}")
    summary_log.append(f"{'=' * 50}")
    summary_log.append(content)

def save_summary():
    """Save the summary log to a file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"modernization_summary_{timestamp}.log"
    
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
        output_dirs = ['baseline_output', 'final_output']
        for output_dir in output_dirs:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Clear contents
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            reset_summary.append(f"✓ Cleared {output_dir}")
        
        # Reset adaptation pod repository if it exists
        adaptation_pod_path = "cec-adaptation-pod-main"
        if os.path.exists(adaptation_pod_path):
            # Remove backup files
            for root, dirs, files in os.walk(adaptation_pod_path):
                for file in files:
                    if file.endswith('.backup'):
                        backup_file = os.path.join(root, file)
                        try:
                            os.remove(backup_file)
                            reset_summary.append(f"✓ Removed backup: {backup_file}")
                        except Exception as e:
                            reset_summary.append(f"⚠️  Could not remove backup: {backup_file} - {e}")
        
        reset_summary.append("✓ Reset completed successfully")
        log_summary("RESET", "\n".join(reset_summary))
        return True
        
    except Exception as e:
        error_msg = f"Error during reset: {e}"
        print(error_msg)
        reset_summary.append(f"❌ {error_msg}")
        log_summary("RESET ERROR", "\n".join(reset_summary))
        return False

def find_python_files(repo_path):
    """Find all Python files in a repository recursively."""
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def get_file_type(file_path):
    """Determine file type based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.py':
        return 'python'
    else:
        return 'unknown'

def modernize_adaptation_pod_scripts(repo_path, uplift_config):
    """Modernize Python scripts in the adaptation pod repository."""
    print(f"\n=== Modernizing Adaptation Pod Scripts ===")
    print(f"Repository: {repo_path}")
    print(f"Target Python Version: {uplift_config.get('target_version', '3.9')}")
    
    uplift_summary = []
    uplift_summary.append(f"Repository: {repo_path}")
    uplift_summary.append(f"Uplift Type: {uplift_config.get('type', 'python')}")
    uplift_summary.append(f"Target Version: {uplift_config.get('target_version', '3.9')}")
    
    send_event("modernizing_python", "status", "running")
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    
    if not python_files:
        message = f"No Python files found in {repo_path}"
        print(message)
        uplift_summary.append(f"\n{message}")
        send_event("modernizing_python", "log", message)
        send_event("modernizing_python", "status", "error")
        return False
    
    print(f"Found {len(python_files)} Python files to process")
    uplift_summary.append(f"\nFound {len(python_files)} Python files to process")
    send_event("modernizing_python", "log", f"Found {len(python_files)} Python files to process")
    
    success_count = 0
    total_files = len(python_files)
    
    for file_path in python_files:
        print(f"\n--- Processing: {file_path} ---")
        uplift_summary.append(f"\n--- Processing: {file_path} ---")
        send_event("modernizing_python", "log", f"Processing: {file_path}")
        
        try:
            # Read original code with fallback encoding
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_code = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        original_code = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='cp1252') as f:
                        original_code = f.read()
            
            # Analyze Python code
            analysis_findings = analyze_python_code(file_path, uplift_config.get('target_version', '3.9'))
            print(f"Analysis: {analysis_findings}")
            uplift_summary.append(f"Analysis: {analysis_findings}")
            send_event("modernizing_python", "log", f"Analysis: {analysis_findings}")
            
            # Get LLM suggestion
            updated_code, change_summary = get_llm_suggestion(
                original_code, 
                analysis_findings, 
                uplift_config.get('target_version', '3.9'), 
                selected_libraries,
                'python'
            )
            
            if updated_code:
                # Create backup
                backup_file = file_path + ".backup"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_code)
                print(f"Backup created: {backup_file}")
                
                # Save updated code
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_code)
                
                # Send LLM change event
                llm_change_data = {
                    "title": f"Modernized {os.path.basename(file_path)}",
                    "description": f"Successfully modernized Python file to {uplift_config.get('target_version', '3.9')}",
                    "file": file_path,
                    "stage": "modernizing_python",
                    "details": change_summary,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                send_llm_change_event(llm_change_data)
                
                print(f"✅ Successfully modernized: {file_path}")
                uplift_summary.append(f"\n✅ Successfully modernized: {file_path}")
                uplift_summary.append(f"Change Summary: {change_summary}")
                send_event("modernizing_python", "log", f"✅ Successfully modernized: {file_path}")
                success_count += 1
            else:
                error_msg = f"Failed to modernize: {file_path}"
                print(error_msg)
                uplift_summary.append(f"\n❌ {error_msg}")
                send_event("modernizing_python", "log", f"❌ {error_msg}")
                
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            print(error_msg)
            uplift_summary.append(f"\n❌ {error_msg}")
            send_event("modernizing_python", "log", f"❌ {error_msg}")
    
    result_msg = f"\nModernization completed: {success_count}/{total_files} files successfully modernized"
    print(result_msg)
    uplift_summary.append(result_msg)
    send_event("modernizing_python", "summary", result_msg)
    
    if success_count > 0:
        send_event("modernizing_python", "status", "completed")
    else:
        send_event("modernizing_python", "status", "error")
    
    log_summary("PYTHON MODERNIZATION", "\n".join(uplift_summary))
    return success_count > 0

def send_event(stage, event_type, payload):
    """Send an event to the frontend."""
    event_data = {
        "stage": stage,
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.datetime.now().isoformat()
    }
    event_queue.put(event_data)
    print(f"🔍 Sending event: {stage} - {event_type}: {payload}")

def send_llm_change_event(change_data):
    """Send LLM change event to frontend."""
    event_data = {
        "stage": "llm_changes",
        "type": "change",
        "payload": change_data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    event_queue.put(event_data)

def modernization_process():
    """Main modernization process."""
    global process_running, current_stage, process_status
    
    try:
        process_running = True
        process_status = "RUNNING"
        current_stage = "starting"
        
        send_event("process", "status", "started")
        send_event("process", "log", "Starting Python modernization process...")
        
        # Reset repositories
        current_stage = "resetting"
        send_event("resetting", "status", "running")
        send_event("resetting", "log", "Resetting repositories...")
        
        if not reset_repositories():
            send_event("resetting", "status", "error")
            send_event("resetting", "log", "Failed to reset repositories")
            return False
        
        send_event("resetting", "status", "completed")
        send_event("resetting", "log", "✓ Repositories reset successfully")
        
        # Modernize adaptation pod scripts
        current_stage = "modernizing_python"
        send_event("modernizing_python", "status", "running")
        send_event("modernizing_python", "log", "Starting Python modernization...")
        
        adaptation_pod_path = "cec-adaptation-pod-main"
        if not os.path.exists(adaptation_pod_path):
            send_event("process", "status", "error")
            send_event("process", "log", f"Adaptation pod repository not found: {adaptation_pod_path}")
            return False
        
        success = modernize_adaptation_pod_scripts(adaptation_pod_path, uplift_config)
        
        if success:
            current_stage = "completed"
            process_status = "COMPLETED"
            send_event("modernizing_python", "status", "completed")
            send_event("completed", "status", "completed")
            send_event("completed", "log", "✓ Python modernization completed successfully")
        else:
            current_stage = "error"
            process_status = "ERROR"
            send_event("modernizing_python", "status", "error")
            send_event("completed", "status", "error")
            send_event("completed", "log", "❌ Python modernization failed")
        
        return success
        
    except Exception as e:
        current_stage = "error"
        process_status = "ERROR"
        error_msg = f"Error during modernization process: {e}"
        print(error_msg)
        send_event("modernizing_python", "status", "error")
        send_event("completed", "status", "error")
        send_event("completed", "log", f"❌ {error_msg}")
        return False
    finally:
        process_running = False

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main HTML page."""
    with open("index_simplified.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon."""
    return FileResponse("ericsson.ico")

@app.post("/start")
async def start_process(request: Request):
    """Start the modernization process."""
    global process_running, process_thread, uplift_config, selected_libraries
    
    if process_running:
        return JSONResponse({"status": "error", "message": "Process already running"})
    
    try:
        data = await request.json()
        uplift_config = data.get("uplift_config", {})
        selected_libraries = data.get("selected_libraries", [])
        
        print(f"Starting modernization with config: {uplift_config}")
        print(f"Selected libraries: {selected_libraries}")
        
        # Start process in background thread
        process_thread = threading.Thread(target=modernization_process)
        process_thread.daemon = True
        process_thread.start()
        
        return JSONResponse({"status": "started", "message": "Modernization process started"})
        
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error starting process: {e}"})

@app.post("/cancel")
async def cancel_process():
    """Cancel the running process."""
    global process_running, process_status
    
    if not process_running:
        return JSONResponse({"status": "error", "message": "No process running"})
    
    process_status = "CANCELLED"
    send_event("process", "status", "cancelled")
    send_event("process", "log", "Process cancelled by user")
    
    return JSONResponse({"status": "cancelled", "message": "Process cancelled"})

@app.post("/reset")
async def reset_process():
    """Reset the process state."""
    global process_running, process_status, current_stage
    
    if process_running:
        return JSONResponse({"status": "error", "message": "Cannot reset while process is running"})
    
    process_status = "IDLE"
    current_stage = "idle"
    
    # Reset repositories
    success = reset_repositories()
    
    if success:
        send_event("resetting", "status", "completed")
        send_event("resetting", "log", "Process reset successfully")
        return JSONResponse({"status": "reset", "message": "Process reset successfully"})
    else:
        return JSONResponse({"status": "error", "message": "Failed to reset process"})

@app.get("/api/libraries")
async def get_libraries():
    """Get available libraries for RAG context."""
    try:
        libraries = get_available_libraries()
        return JSONResponse({"status": "success", "libraries": libraries})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error getting libraries: {e}"})

@app.post("/api/select-libraries")
async def select_libraries(request: Request):
    """Select libraries for RAG context."""
    global selected_libraries
    
    try:
        data = await request.json()
        selected_libraries = data.get("libraries", [])
        return JSONResponse({"status": "success", "message": f"Selected {len(selected_libraries)} libraries"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error selecting libraries: {e}"})

@app.get("/api/selected-libraries")
async def get_selected_libraries():
    """Get currently selected libraries."""
    return JSONResponse({"status": "success", "libraries": selected_libraries})

@app.post("/api/test-events")
async def test_events():
    """Test endpoint to verify event system is working."""
    send_event("resetting", "status", "running")
    send_event("resetting", "log", "Test event - resetting stage")
    send_event("modernizing_python", "status", "running")
    send_event("modernizing_python", "log", "Test event - modernizing stage")
    send_event("completed", "status", "completed")
    send_event("completed", "log", "Test event - completed stage")
    return JSONResponse({"status": "success", "message": "Test events sent"})

@app.get("/stream")
async def event_stream(request: Request):
    """Stream events to the frontend."""
    
    async def event_generator():
        # Send initial connection established event
        yield {
            "event": "connected",
            "data": json.dumps({
                "message": "Event stream connected",
                "timestamp": datetime.datetime.now().isoformat()
            })
        }
        
        # Send current process status
        yield {
            "event": "status",
            "data": json.dumps({
                "running": process_running,
                "status": process_status,
                "stage": current_stage,
                "timestamp": datetime.datetime.now().isoformat()
            })
        }
        
        # Stream events from queue
        while True:
            try:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Get event from queue with timeout
                try:
                    event_data = event_queue.get(timeout=1)
                    yield {
                        "event": event_data["type"],
                        "data": json.dumps(event_data)
                    }
                except queue.Empty:
                    # Send heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    }
                    
            except Exception as e:
                print(f"Error in event stream: {e}")
                break
    
    return EventSourceResponse(event_generator())

def main():
    """Main function to run the FastAPI server."""
    print("=== Python Modernization Tool ===")
    print("Starting web server...")
    
    # Check if LLM API is configured
    if not initialize_llm_api():
        print("Warning: LLM_API_TOKEN not configured. Some features may not work.")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 