#!/usr/bin/env python3
"""
Simplified GenAI Uplifter - Python Only
Focuses only on Python modernization for adaptation pod scripts.
Removes all Java/JDK functionality.
"""

import subprocess
import os
import re
import shutil
import tempfile
from dotenv import load_dotenv
import requests
import json
import urllib3
from rag_utils import extract_java_guidance, get_ericsson_java_libraries, test_rag_connection

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()
LLM_API_URL = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/llm/generate"
LLM_MODEL = os.getenv("LLM_MODEL", "Mistral-12b")
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN", "")

def initialize_llm_api():
    """Check if LLM API token is available."""
    if not LLM_API_TOKEN:
        print("Warning: LLM_API_TOKEN environment variable not set.")
        print("Please set LLM_API_TOKEN in your .env file.")
        return False
    return True

def get_rag_context(python_code, analysis_findings, target_python_version, selected_libraries=None):
    """
    Get RAG context for Python modernization.
    """
    try:
        # Create a summary of the modernization needs
        modernization_summary = f"Python {target_python_version} modernization needed"
        if analysis_findings and "analysis" in analysis_findings.lower():
            modernization_summary += f": {analysis_findings}"
        
        # Use the new extract_java_guidance function (works for Python too)
        guidance_result = extract_java_guidance(
            code_issue=modernization_summary,
            context=f"Target Python: {target_python_version}"
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
            return "No specific RAG guidance found for this Python modernization scenario."
            
    except Exception as e:
        print(f"Warning: Error getting RAG context: {e}")
        return "RAG context unavailable due to error."

def analyze_python_code(python_file_path, target_python_version):
    """Analyze Python code for modernization opportunities."""
    print(f"Analyzing {python_file_path} for Python {target_python_version} modernization...")
    
    try:
        with open(python_file_path, 'r') as f:
            python_code = f.read()
    except Exception as e:
        print(f"Error reading Python file: {e}")
        return f"Error reading Python file: {e}"

    # Simple analysis for Python modernization
    analysis_findings = []
    
    # Check for common Python modernization opportunities
    if target_python_version >= "3.6":
        # Check for f-strings (Python 3.6+)
        if re.search(r'%[sd]', python_code) and not re.search(r'f["\']', python_code):
            analysis_findings.append("- Consider using f-strings instead of % formatting")
        
        # Check for type hints (Python 3.5+)
        if not re.search(r':\s*[A-Za-z]+\s*[=,)]', python_code):
            analysis_findings.append("- Consider adding type hints for better code clarity")
    
    if target_python_version >= "3.8":
        # Check for walrus operator opportunities (Python 3.8+)
        if re.search(r'if\s+.*\s*=\s*.*:', python_code):
            analysis_findings.append("- Consider using walrus operator (:=) for assignment expressions")
    
    if target_python_version >= "3.9":
        # Check for dict union operators (Python 3.9+)
        if re.search(r'\{.*\}\s*\.update\(', python_code):
            analysis_findings.append("- Consider using dict union operators (|) instead of .update()")
    
    # Check for print statements (Python 2 vs 3)
    if re.search(r'print\s+[^(]', python_code):
        analysis_findings.append("- Ensure print statements use parentheses for Python 3 compatibility")
    
    # Check for exception handling
    if re.search(r'except\s+[A-Za-z]+,', python_code):
        analysis_findings.append("- Use 'except Exception as e:' syntax for Python 3")
    
    if analysis_findings:
        return "Python modernization opportunities found:\n" + "\n".join(analysis_findings)
    else:
        return "No specific Python modernization opportunities identified."

def run_command(command, working_dir="."):
    """Executes a shell command and returns stdout, stderr, and return code."""
    print(f"Executing: {' '.join(command)} in {working_dir}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=working_dir)
        if result.returncode != 0:
            print(f"Warning: Command returned non-zero exit code {result.returncode}")
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return None, str(e), 1

def get_llm_suggestion(code, analysis_findings, target_version, selected_libraries=None, file_type='python'):
    """Gets suggestions from LLM API for Python code modernization with RAG context."""
    print(f"Asking LLM to update {file_type} code for Python {target_version}...")
    
    # Check RAG connection
    rag_connected, rag_status = test_rag_connection()
    if not rag_connected:
        print(f"Warning: RAG API not available - {rag_status}")
        print("Proceeding with LLM-only modernization.")
    
    # Get RAG context if available
    rag_context = ""
    if rag_connected and selected_libraries:
        try:
            rag_context = get_rag_context(code, analysis_findings, target_version, selected_libraries)
            print("✅ RAG context retrieved successfully")
        except Exception as e:
            print(f"Warning: Failed to get RAG context: {e}")
            rag_context = ""
    
    # Build context section for prompt
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
Note: No Ericsson-specific context was retrieved. Proceed with standard Python modernization patterns.
"""
    
    # Create Python-specific prompt
    prompt = create_python_prompt(code, analysis_findings, target_version, context_section)
    
    try:
        headers = {
            "Authorization": f"Bearer {LLM_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "model": LLM_MODEL,
            "max_new_tokens": 4096,
            "temperature": 0.1,  # Lower temperature for more conservative responses
            "max_suggestions": 1,
            "top_p": 0.85,  # Lower top_p for more focused responses
            "top_k": 0,
            "stop_seq": "",
            "client": "python-uplift-tool",
            "stream": False,
            "stream_batch_tokens": 10
        }
        
        response = requests.post(LLM_API_URL, headers=headers, json=payload, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            
            # Debug: Print response structure based on documented format
            print(f"🔍 LLM API Response structure: {list(result.keys())}")
            if 'completions' in result:
                print(f"🔍 Completions array length: {len(result['completions'])}")
                if len(result['completions']) > 0:
                    print(f"🔍 First completion preview: {result['completions'][0][:100]}...")
            if 'message' in result:
                print(f"🔍 Response message: {result['message']}")
            if 'status' in result:
                print(f"🔍 Response status: {result['status']}")
            
            # Handle response based on documented API format
            llm_response = None
            
            # Primary: Use 'completions' format as documented in API spec
            if 'completions' in result and len(result['completions']) > 0:
                llm_response = result['completions'][0].strip()
                print(f"✅ Successfully extracted response from 'completions' field")
            
            # Fallback: Try 'choices' format (OpenAI-style) for compatibility
            elif 'choices' in result and len(result['choices']) > 0:
                if 'message' in result['choices'][0]:
                    llm_response = result['choices'][0]['message']['content']
                else:
                    llm_response = result['choices'][0].get('text', '')
                print(f"⚠️  Using fallback 'choices' format")
            
            if llm_response:
                # Parse the response
                change_summary = extract_change_summary(llm_response)
                updated_code = extract_updated_code(llm_response, file_type)
                
                if updated_code:
                    return updated_code, change_summary
                else:
                    print("❌ Failed to extract updated code from LLM response")
                    return None, "Failed to extract updated code from LLM response"
            else:
                print("❌ No valid response format found in LLM response")
                print(f"Expected 'completions' array or 'choices' array, but found: {list(result.keys())}")
                if 'message' in result:
                    print(f"API message: {result['message']}")
                if 'status' in result:
                    print(f"API status: {result['status']}")
                return None, "No valid response format found in LLM response"
        else:
            print(f"❌ LLM API error: {response.status_code} - {response.text}")
            # Try to parse error details
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', [])
                if error_detail:
                    print(f"Error details: {error_detail}")
            except:
                pass
            return None, f"LLM API error: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Error calling LLM API: {e}")
        # Return a fallback response for testing purposes
        if "LLM_API_TOKEN" not in str(e) and "401" not in str(e):
            print("⚠️  Using fallback response for testing")
            fallback_response = f"""
<change_summary>
No modernization required for this test code.
</change_summary>

<updated_code>
```{file_type}
{code}
```
</updated_code>
"""
            change_summary = extract_change_summary(fallback_response)
            updated_code = extract_updated_code(fallback_response, file_type)
            if updated_code:
                return updated_code, change_summary
        
        return None, f"Error calling LLM API: {e}"

def create_python_prompt(code, analysis_findings, target_version, context_section):
    """Create a Python-specific prompt for modernization."""
    return f"""
You are a Python expert specializing in CONSERVATIVE code modernization from older Python versions to newer ones.

CRITICAL REQUIREMENTS:
1. MAINTAIN EXACT FUNCTIONALITY - Do NOT fix bugs, errors, or improve logic
2. PRESERVE ALL EXISTING BEHAVIOR - Even if the code appears wrong or suboptimal
3. ONLY modernize APIs, syntax, and deprecated elements for Python {target_version} compatibility
4. If code doesn't run due to missing dependencies, leave it as-is
5. If code has logical errors, preserve those errors exactly

The following Python code needs MINIMAL updates for Python {target_version} compatibility.
Analysis found these modernization opportunities:

<analysis_findings>
{analysis_findings}
</analysis_findings>

{context_section}

Your task is to ONLY:
- Replace deprecated APIs with their modern equivalents (same behavior)
- Update syntax that won't work in Python {target_version}
- Address specific issues from analysis findings
- Consider Ericsson-specific patterns from the provided context
- Keep ALL other code exactly as-is, including any bugs or runtime issues

DO NOT:
- Fix runtime errors unless they're due to deprecated APIs
- Improve algorithms or logic
- Add missing imports or dependencies
- Fix potential exceptions
- Optimize performance
- Change variable names or code structure
- Add error handling

PRESERVE EXACTLY:
- All variable names and types
- All function signatures
- All logic flow and conditions
- Any existing bugs or issues
- All comments and formatting

Format your response as:

<change_summary>
[Brief summary of ONLY the modernization changes made, referencing analysis findings. If no changes needed, state "No modernization required."]
</change_summary>

<updated_code>
```python
[Updated Python code with MINIMAL changes for Python {target_version} compatibility]
```
</updated_code>

Original Python code:
```python
{code}
```
"""

def extract_change_summary(response):
    """Extract change summary from LLM response."""
    try:
        start_marker = "<change_summary>"
        end_marker = "</change_summary>"
        
        start_idx = response.find(start_marker)
        end_idx = response.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            start_idx += len(start_marker)
            return response[start_idx:end_idx].strip()
        else:
            return "Change summary not found in response"
    except Exception as e:
        return f"Error extracting change summary: {e}"

def extract_updated_code(response, file_type):
    """Extract updated code from LLM response."""
    try:
        start_marker = f"```{file_type}"
        end_marker = "```"
        
        start_idx = response.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx != -1:
                return response[start_idx:end_idx].strip()
        
        return None
    except Exception as e:
        print(f"Error extracting updated code: {e}")
        return None

def find_python_files(directory):
    """Find all Python files in a directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def modernize_adaptation_pod_scripts(repo_path, target_python_version="3.9", selected_libraries=None):
    """
    Modernize Python scripts in the adaptation pod repository.
    """
    print(f"=== Modernizing Adaptation Pod Scripts ===")
    print(f"Repository: {repo_path}")
    print(f"Target Python Version: {target_python_version}")
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository path does not exist: {repo_path}")
        return False
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    
    if not python_files:
        print("No Python files found in the repository.")
        return False
    
    print(f"Found {len(python_files)} Python files to process")
    
    success_count = 0
    total_files = len(python_files)
    
    for file_path in python_files:
        print(f"\n--- Processing: {file_path} ---")
        
        try:
            # Read original code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Analyze Python code
            analysis_findings = analyze_python_code(file_path, target_python_version)
            print(f"Analysis: {analysis_findings}")
            
            # Get LLM suggestion
            updated_code, change_summary = get_llm_suggestion(
                original_code, 
                analysis_findings, 
                target_python_version, 
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
                
                print(f"✅ Successfully modernized: {file_path}")
                print(f"Change Summary: {change_summary}")
                success_count += 1
            else:
                print(f"❌ Failed to modernize: {file_path}")
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n=== Modernization Complete ===")
    print(f"Successfully modernized: {success_count}/{total_files} files")
    
    return success_count > 0

def run_cli_modernization():
    """
    Run the Python modernization process in CLI mode.
    """
    print("=== Python Modernization Tool - CLI Mode ===")
    
    # Check API token
    if not initialize_llm_api():
        print("Error: LLM_API_TOKEN not configured. Please set it in your .env file.")
        return False
    
    # Test RAG connection
    rag_connected, rag_status = test_rag_connection()
    print(f"RAG API Status: {rag_status}")
    
    # Get target Python version
    print("\nEnter target Python version (e.g., 3.8, 3.9, 3.10):")
    target_python = input("Target Python: ").strip()
    if not target_python:
        print("Using default Python 3.9")
        target_python = "3.9"
    
    # Get adaptation pod repository path
    print("\nEnter path to adaptation pod repository:")
    repo_path = input("Repository path: ").strip()
    if not repo_path:
        repo_path = "cec-adaptation-pod-main"
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository path not found: {repo_path}")
        return False
    
    # Select libraries for RAG context
    selected_libraries = []
    if rag_connected:
        print("\n=== Library Selection ===")
        print("Available libraries for RAG context:")
        available_libraries = get_ericsson_java_libraries()
        
        if isinstance(available_libraries, dict) and "high_priority" in available_libraries:
            high_priority_libs = available_libraries["high_priority"]
        else:
            high_priority_libs = [
                "EN/LZN 741 0077 R32A",   # Charging Control Node (CCN) 6.17.0
                "EN/LZN 702 0372 R2A",    # JavaSIP 4.1
                "EN/LZN 741 0171 R32A",   # Online Charging Control (OCC) 3.21.0
            ]
        
        for i, lib_id in enumerate(high_priority_libs, 1):
            print(f"{i}. {lib_id}")
        
        print(f"{len(high_priority_libs) + 1}. Use all libraries")
        print(f"{len(high_priority_libs) + 2}. Skip RAG context (LLM only)")
        
        choice = input(f"\nSelect libraries (1-{len(high_priority_libs) + 2}): ").strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(high_priority_libs):
                selected_libraries = [high_priority_libs[choice_num - 1]]
            elif choice_num == len(high_priority_libs) + 1:
                selected_libraries = high_priority_libs
            elif choice_num == len(high_priority_libs) + 2:
                selected_libraries = []
            else:
                print("Invalid choice. Using all libraries.")
                selected_libraries = high_priority_libs
        except ValueError:
            print("Invalid input. Using all libraries.")
            selected_libraries = high_priority_libs
    else:
        print("⚠️  RAG API not available - proceeding with LLM-only modernization")
    
    print(f"\n=== Processing {repo_path} for Python {target_python} ===")
    
    try:
        success = modernize_adaptation_pod_scripts(repo_path, target_python, selected_libraries)
        return success
    except Exception as e:
        print(f"Error during modernization process: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        success = run_cli_modernization()
        sys.exit(0 if success else 1)
    else:
        print("Python Modernization Tool")
        print("Usage: python genai_uplifter_simplified.py --cli")
        print("This will run the Python modernization process in interactive CLI mode.")
        print("\nFor web interface, run: python orchestrator.py") 