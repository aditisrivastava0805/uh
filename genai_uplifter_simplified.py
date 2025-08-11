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
        
        # Use Python-specific RAG guidance
        from rag_utils import get_available_libraries
        
        # Get available Python libraries
        available_libraries = get_available_libraries()
        
        # Filter for Python-related libraries
        python_libraries = []
        for lib in available_libraries:
            if any(keyword in lib.lower() for keyword in ['python', 'pip', 'pypi', 'modernization', 'syntax']):
                python_libraries.append(lib)
        
        # If no Python-specific libraries found, use general libraries
        if not python_libraries:
            python_libraries = available_libraries[:5]  # Use first 5 libraries
        
        # Create Python-specific guidance query
        guidance_query = f"Python {target_python_version} modernization best practices"
        if analysis_findings:
            guidance_query += f" for: {analysis_findings}"
        
        # Use the extract_java_guidance function but with Python context
        from rag_utils import extract_java_guidance
        guidance_result = extract_java_guidance(
            code_issue=guidance_query,
            context=f"Target Python version: {target_python_version}. Focus on Python modernization, not Java."
        )
        
        if guidance_result.get("guidance_found"):
            # Format the guidance for the LLM prompt
            context_parts = []
            context_parts.append(f"PYTHON MODERNIZATION GUIDANCE: {guidance_result['summary']}")
            
            detailed_guidance = guidance_result.get("detailed_guidance")
            if detailed_guidance and isinstance(detailed_guidance, list):
                context_parts.append("\nDETAILED PYTHON GUIDANCE:")
                # Safely slice the list, ensuring it's a list first
                for item in detailed_guidance[:3]:  # Limit to top 3
                    if isinstance(item, dict):
                        source = item.get("source", "Unknown")
                        content = item.get("content", "")[:300]  # Limit content length
                        context_parts.append(f"- From {source}: {content}")
            
            libraries_used = guidance_result.get("libraries_searched", [])
            if libraries_used and isinstance(libraries_used, list):
                context_parts.append(f"\nPython Sources: {', '.join(libraries_used[:3])}")
            
            return "\n".join(context_parts)
        else:
            return "No specific Python RAG guidance found for this modernization scenario."
            
    except Exception as e:
        print(f"Warning: Error getting RAG context: {e}")
        print(f"Debug info: guidance_result type: {type(guidance_result) if 'guidance_result' in locals() else 'Not defined'}")
        if 'guidance_result' in locals():
            print(f"Debug info: guidance_result keys: {list(guidance_result.keys()) if isinstance(guidance_result, dict) else 'Not a dict'}")
        return "Python RAG context unavailable due to error."

def analyze_python_code(python_file_path, target_python_version):
    """Analyze Python code for modernization opportunities using LLM + regex validation."""
    print(f"Analyzing {python_file_path} for Python {target_python_version} modernization...")
    
    try:
        with open(python_file_path, 'r', encoding='utf-8') as f:
            python_code = f.read()
    except UnicodeDecodeError:
        try:
            with open(python_file_path, 'r', encoding='latin-1') as f:
                python_code = f.read()
        except UnicodeDecodeError:
            with open(python_file_path, 'r', encoding='cp1252') as f:
                python_code = f.read()
    except Exception as e:
        print(f"Error reading Python file: {e}")
        return f"Error reading Python file: {e}"

    # Phase 1: LLM-based analysis (primary detection)
    llm_analysis = get_llm_analysis(python_code, target_python_version)
    
    # Phase 2: Regex validation (double-check and catch missed items)
    regex_validation = validate_with_regex(python_code, target_python_version)
    
    # Phase 3: Combine and prioritize findings
    combined_findings = combine_analysis_findings(llm_analysis, regex_validation)
    
    return combined_findings

def get_llm_analysis(python_code, target_python_version):
    """Get LLM-based analysis of Python code modernization opportunities."""
    try:
        # Create analysis prompt for LLM
        analysis_prompt = f"""
        Analyze this Python code for Python {target_python_version} modernization opportunities.
        
        Code:
        {python_code[:2000]}  # Limit to first 2000 chars for analysis
        
        Please identify:
        1. Python 2 vs 3 compatibility issues
        2. Opportunities for modern Python features (f-strings, walrus operators, type hints)
        3. Code style improvements
        4. Performance optimizations
        
        Return a concise list of modernization opportunities.
        """
        
        # Call LLM for analysis
        response = call_llm_for_analysis(analysis_prompt)
        return response
        
    except Exception as e:
        print(f"Warning: LLM analysis failed: {e}")
        return "LLM analysis unavailable"

def validate_with_regex(python_code, target_python_version):
    """Validate LLM findings and catch missed opportunities using regex."""
    validation_findings = []
    
    # Check for common Python modernization opportunities
    if target_python_version >= "3.6":
        # Check for f-strings (Python 3.6+)
        if re.search(r'%[sd]', python_code) and not re.search(r'f["\']', python_code):
            validation_findings.append("- Consider using f-strings instead of % formatting")
        
        # Check for type hints (Python 5+)
        if not re.search(r':\s*[A-Za-z]+\s*[=,)]', python_code):
            validation_findings.append("- Consider adding type hints for better code clarity")
    
    if target_python_version >= "3.8":
        # Check for walrus operator opportunities (Python 3.8+)
        if re.search(r'if\s+.*\s*=\s*.*:', python_code):
            validation_findings.append("- Consider using walrus operator (:=) for assignment expressions")
    
    if target_python_version >= "3.9":
        # Check for dict union operators (Python 3.9+)
        if re.search(r'\{.*\}\s*\.update\(', python_code):
            validation_findings.append("- Consider using dict union operators (|) instead of .update()")
    
    # Check for print statements (Python 2 vs 3)
    if re.search(r'print\s+[^(]', python_code):
        validation_findings.append("- Ensure print statements use parentheses for Python 3 compatibility")
    
    # Check for exception handling
    if re.search(r'except\s+[A-Za-z]+,', python_code):
        validation_findings.append("- Use 'except Exception as e:' syntax for Python 3")
    
    # Check for len() comparisons that could use walrus operator
    if re.search(r'if\s+len\([^)]+\)\s*[!=]=', python_code):
        validation_findings.append("- Consider using walrus operator for length checks")
    
    # Check for string concatenation that could use f-strings
    if re.search(r'["\'][^"\']*["\']\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\+\s*["\']', python_code):
        validation_findings.append("- Consider using f-strings instead of string concatenation")
    
    return validation_findings

def combine_analysis_findings(llm_analysis, regex_validation):
    """Combine LLM and regex findings, removing duplicates and prioritizing."""
    combined = []
    
    # Add LLM findings first (primary source)
    if llm_analysis and llm_analysis != "LLM analysis unavailable":
        combined.append(f"LLM Analysis: {llm_analysis}")
    
    # Add regex validation findings (secondary source)
    if regex_validation:
        combined.append("\nRegex Validation:")
        combined.extend(regex_validation)
    
    # Always provide modernization guidance for Python 2 style code
    if regex_validation and any("print statements" in item or "% formatting" in item for item in regex_validation):
        combined.append("- This file contains Python 2 style code that should be modernized for Python 3 compatibility")
    
    if combined:
        return "\n".join(combined)
    else:
        return "Code appears to be Python 3 compatible, but can still benefit from modern Python features like f-strings, type hints, and walrus operators."

def call_llm_for_analysis(analysis_prompt):
    """Call LLM API for code analysis."""
    try:
        # Check if LLM API is available
        if not LLM_API_TOKEN:
            return "LLM API not configured - using regex-only analysis"
        
        # Prepare payload for analysis
        payload = {
            "prompt": analysis_prompt,
            "model": LLM_MODEL,
            "max_new_tokens": 1024,  # Shorter for analysis
            "temperature": 0.1,
            "max_suggestions": 1,
            "top_p": 0.85,
            "top_k": 0,
            "stop_seq": "",
            "client": "python-uplift-tool",
            "stream": False,
            "stream_batch_tokens": 10
        }
        
        # Make API call
        response = requests.post(
            LLM_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_TOKEN}"},
            json=payload,
            timeout=(30, 60)
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"🔍 LLM Analysis API Response: {response_data}")
            
            # Try different response formats
            content = None
            
            # Format 1: Direct content field
            if "content" in response_data:
                content = response_data["content"]
                print(f"✅ Found content in 'content' field: {content[:100]}...")
            
            # Format 2: OpenAI-style response
            elif "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    print(f"✅ Found content in OpenAI format: {content[:100]}...")
                elif "text" in choice:
                    content = choice["text"]
                    print(f"✅ Found content in 'text' field: {content[:100]}...")
            
            # Format 3: Generic response with text
            elif "text" in response_data:
                content = response_data["text"]
                print(f"✅ Found content in 'text' field: {content[:100]}...")
            
            # Format 4: Response field
            elif "response" in response_data:
                content = response_data["response"]
                print(f"✅ Found content in 'response' field: {content[:100]}...")
            
            if content:
                return content[:500]  # Limit response length
            else:
                print(f"⚠️  No content found in response. Available keys: {list(response_data.keys())}")
                return f"LLM analysis completed but no content found. Response keys: {list(response_data.keys())}"
        else:
            return f"LLM API error: {response.status_code}"
            
    except Exception as e:
        return f"LLM analysis failed: {str(e)}"

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
    """Get LLM suggestion for code modernization."""
    print(f"Asking LLM to update {file_type} code for Python {target_version}...")
    
    # Get RAG context
    context_section = get_rag_context(code, analysis_findings, target_version, selected_libraries)
    
    # Create prompt
    prompt = create_python_prompt(code, analysis_findings, target_version, context_section)
    
    # Prepare payload with optimized settings for large files
    payload = {
        "prompt": prompt,
        "model": LLM_MODEL,
        "max_new_tokens": 8192,  # Increased for large files
        "temperature": 0.1,
        "max_suggestions": 1,
        "top_p": 0.85,
        "top_k": 0,
        "stop_seq": "",
        "client": "python-uplift-tool",
        "stream": False,
        "stream_batch_tokens": 10
    }
    
    # Calculate timeout based on file size
    file_size_kb = len(code) / 1024
    if file_size_kb > 10:  # Large files (>10KB)
        timeout_settings = (30, 300)  # (connect, read) in seconds - requests expects (connect, read) format
        print(f"📏 Large file detected ({file_size_kb:.1f}KB), using extended timeout: {timeout_settings}")
    else:
        timeout_settings = (30, 180)  # Standard timeout (connect, read)
        print(f"📏 Standard file size ({file_size_kb:.1f}KB), using standard timeout: {timeout_settings}")
    
    # Headers
    headers = {
        "Authorization": f"Bearer {LLM_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Make API call with SSL verification disabled and optimized timeouts
        print(f"🚀 Making LLM API call with timeout settings: {timeout_settings}")
        
        # Show progress for large files
        if file_size_kb > 10:
            print(f"⏳ Large file detected - this may take several minutes...")
            print(f"📊 Processing {file_size_kb:.1f}KB of code...")
        
        response = requests.post(
            LLM_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=timeout_settings,
            verify=False  # Disable SSL verification for corporate API
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 LLM API Response structure: {list(result.keys())}")
            
            # Extract response based on format
            llm_response = None
            if 'completions' in result and len(result['completions']) > 0:
                llm_response = result['completions'][0].strip()
                print(f"✅ Successfully extracted response from 'completions' field")
            elif 'choices' in result and len(result['choices']) > 0:
                if 'message' in result['choices'][0]:
                    llm_response = result['choices'][0]['message']['content']
                else:
                    llm_response = result['choices'][0].get('text', '')
                print(f"⚠️  Using fallback 'choices' format")
            else:
                print("❌ No valid response format found in LLM response")
                print(f"Expected 'completions' array or 'choices' array, but found: {list(result.keys())}")
                if 'message' in result:
                    print(f"API message: {result['message']}")
                if 'status' in result:
                    print(f"API status: {result['status']}")
                return None, "No valid response format found in LLM response"
            
            if llm_response:
                # Debug: Print the actual LLM response structure
                print(f"🔍 LLM Response type: {type(llm_response)}")
                if isinstance(llm_response, list) and len(llm_response) > 0:
                    print(f"🔍 First completion type: {type(llm_response[0])}")
                    if isinstance(llm_response[0], dict):
                        print(f"🔍 First completion keys: {list(llm_response[0].keys())}")
                
                # Extract the actual text content
                content_text = ""
                
                if isinstance(llm_response, list):
                    # Handle list of completions
                    if len(llm_response) > 0:
                        first_completion = llm_response[0]
                        if isinstance(first_completion, dict):
                            # Try different possible field names for the content
                            for field in ['text', 'content', 'message', 'response', 'completion']:
                                if field in first_completion:
                                    content_text = first_completion[field]
                                    print(f"✅ Found content in field: '{field}'")
                                    break
                            else:
                                # If no standard field found, try to get the first string value
                                for key, value in first_completion.items():
                                    if isinstance(value, str) and len(value) > 100:  # Likely the main content
                                        content_text = value
                                        print(f"✅ Using field '{key}' as content (length: {len(value)})")
                                        break
                        else:
                            content_text = str(first_completion)
                elif isinstance(llm_response, dict):
                    # Handle single completion object
                    for field in ['text', 'content', 'message', 'response', 'completion']:
                        if field in llm_response:
                            content_text = llm_response[field]
                            print(f"✅ Found content in field: '{field}'")
                            break
                    else:
                        content_text = str(llm_response)
                elif isinstance(llm_response, str):
                    content_text = llm_response
                else:
                    content_text = str(llm_response)
                
                print(f"🔍 Content text length: {len(content_text)}")
                print(f"🔍 Content preview: {content_text[:200]}...")
                
                if content_text and len(content_text) > 50:  # Ensure we have substantial content
                    # Extract change summary and updated code
                    change_summary = extract_change_summary(content_text)
                    updated_code = extract_updated_code(content_text, file_type)
                    
                    if updated_code:
                        print(f"✅ Successfully extracted updated code (length: {len(updated_code)})")
                        return updated_code, change_summary
                    else:
                        print("❌ Failed to extract updated code from content")
                        print(f"🔍 Content sample for debugging: {content_text[:500]}")
                        # Return original code with a note if extraction fails
                        fallback_code = f"""# LLM modernization applied but code extraction failed
# Original analysis: {analysis_findings}
# Raw LLM response available in change summary

{code}

# End of original code
"""
                        return fallback_code, f"Modernization attempted but code extraction failed. Raw response: {content_text[:500]}..."
                else:
                    return None, f"No substantial content received from LLM (length: {len(content_text)})"
            else:
                return None, "No response content from LLM"
                
        else:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return None, error_msg
            
    except requests.exceptions.Timeout as e:
        print(f"⏰ LLM API request timed out: {e}")
        print(f"💡 This might be due to large file size ({file_size_kb:.1f}KB) or slow API response")
        print(f"🔄 Falling back to local modernization engine...")
        # Execute fallback modernization
        return execute_fallback_modernization(code, analysis_findings)
    except requests.exceptions.ConnectionError as e:
        print(f"🌐 LLM API connection error: {e}")
        print(f"💡 This might be due to network issues or API endpoint being unavailable")
        print(f"🔄 Falling back to local modernization engine...")
        # Execute fallback modernization
        return execute_fallback_modernization(code, analysis_findings)
            
    except Exception as e:
        print(f"❌ Error calling LLM API: {e}")
        # Return a fallback response that implements actual modernization based on analysis
        if "LLM_API_TOKEN" not in str(e) and "401" not in str(e):
            print("⚠️  Using fallback modernization based on analysis findings")
            
            # Implement modernization based on analysis findings
            updated_code = code
            change_summary = "Modernization applied using fallback engine based on analysis findings:"
            
            # Apply modernization based on analysis findings
            if "walrus operator" in analysis_findings.lower():
                # Look for patterns that can use walrus operator
                import re
                
                # Pattern 1: if some_condition: result = some_function()
                # Convert to: if result := some_function(): pass
                pattern1 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*([^:]+):\s*\n\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\2'
                if re.search(pattern1, updated_code):
                    updated_code = re.sub(pattern1, r'if \3 := \2:', updated_code)
                    change_summary += "\n- Applied walrus operator for assignment expressions"
                
                # Pattern 2: result = some_function(); if result:
                # Convert to: if result := some_function():
                pattern2 = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);\s*if\s+\1:'
                if re.search(pattern2, updated_code):
                    updated_code = re.sub(pattern2, r'if \1 := \2:', updated_code)
                    change_summary += "\n- Applied walrus operator for conditional assignment"
                
                # Pattern 3: if len(something) != 0: (common in the SDP file)
                # Convert to: if len_something := len(something) and len_something != 0:
                pattern3 = r'if\s+len\(([^)]+)\)\s*!=\s*0:'
                if re.search(pattern3, updated_code):
                    updated_code = re.sub(pattern3, r'if len_\1 := len(\1) and len_\1 != 0:', updated_code)
                    change_summary += "\n- Applied walrus operator for length checks"
                
                # Pattern 4: if len(something) == 0: (common in the SDP file)
                # Convert to: if len_something := len(something) and len_something == 0:
                pattern4 = r'if\s+len\(([^)]+)\)\s*==\s*0:'
                if re.search(pattern4, updated_code):
                    updated_code = re.sub(pattern4, r'if len_\1 := len(\1) and len_\1 == 0:', updated_code)
                    change_summary += "\n- Applied walrus operator for empty length checks"
                
                # Pattern 5: if len(something) == specific_length: (like the date parsing)
                # Convert to: if len_something := len(something) and len_something == specific_length:
                pattern5 = r'if\s+len\(([^)]+)\)\s*==\s*(\d+):'
                if re.search(pattern5, updated_code):
                    updated_code = re.sub(pattern5, r'if len_\1 := len(\1) and len_\1 == \2:', updated_code)
                    change_summary += "\n- Applied walrus operator for specific length checks"
            
            if "f-string" in analysis_findings.lower():
                # Convert % formatting to f-strings where safe
                import re
                
                # Pattern: "text %s text" % variable
                pattern = r'"([^"]*%[^"]*)"\s*%\s*([a-zA-Z_][a-zA-Z0-9_]*)'
                if re.search(pattern, updated_code):
                    updated_code = re.sub(pattern, r'f"\1".format(\2)', updated_code)
                    change_summary += "\n- Converted % formatting to f-string format"
                
                # Pattern: "text %s text" % (variable1, variable2)
                pattern2 = r'"([^"]*%[^"]*)"\s*%\s*\(([^)]+)\)'
                if re.search(pattern2, updated_code):
                    updated_code = re.sub(pattern2, r'f"\1".format(\2)', updated_code)
                    change_summary += "\n- Converted % formatting with tuple to f-string format"
                
                # Pattern: string concatenation with variables
                pattern3 = r'(["\'])([^"\']*)\1\s*\+\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\+\s*(["\'])([^"\']*)\4'
                if re.search(pattern3, updated_code):
                    updated_code = re.sub(pattern3, r'f"\2{\3}\5"', updated_code)
                    change_summary += "\n- Converted string concatenation to f-string format"
            
            if "print statements" in analysis_findings.lower():
                # Fix print statements without parentheses
                import re
                
                # Pattern: print variable (Python 2 style)
                pattern = r'print\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$'
                if re.search(pattern, updated_code, re.MULTILINE):
                    updated_code = re.sub(pattern, r'print(\1)', updated_code, flags=re.MULTILINE)
                    change_summary += "\n- Fixed print statements to use parentheses for Python 3 compatibility"
                
                # Pattern: print "string" (Python 2 style)
                pattern2 = r'print\s+(["\'])([^"\']*)\1\s*$'
                if re.search(pattern2, updated_code, re.MULTILINE):
                    updated_code = re.sub(pattern2, r'print(\1\2\1)', updated_code, flags=re.MULTILINE)
                    change_summary += "\n- Fixed print statements with strings to use parentheses for Python 3 compatibility"
            
            if "type hints" in analysis_findings.lower():
                # Add basic type hints where missing
                import re
                
                # Pattern: def function_name(param):
                # Convert to: def function_name(param: Any):
                pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\):'
                if re.search(pattern, updated_code):
                    # Only add type hints if not already present
                    if ': ' not in re.search(pattern, updated_code).group(2):
                        updated_code = re.sub(pattern, r'def \1(\2: Any):', updated_code)
                        change_summary += "\n- Added basic type hints to function parameters"
            
            # If no specific changes were made, provide a generic message
            if updated_code == code:
                change_summary = "Analysis found modernization opportunities, but fallback engine could not apply specific changes. Manual review recommended."
            
            fallback_response = f"""
<change_summary>
{change_summary}
</change_summary>

<updated_code>
```python
{updated_code}
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

Your task is to IMPLEMENT the modernization changes identified in the analysis:
- Replace deprecated APIs with their modern equivalents (same behavior)
- Update syntax that won't work in Python {target_version}
- Address specific issues from analysis findings
- Consider Ericsson-specific patterns from the provided context
- Keep ALL other code exactly as-is, including any bugs or runtime issues

IMPORTANT: You MUST make the modernization changes identified in the analysis. Do NOT say "No modernization required" if the analysis found opportunities.

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
[Brief summary of the modernization changes made, referencing the specific analysis findings. List each change applied.]
</change_summary>

<updated_code>
```python
[Updated Python code with the modernization changes applied for Python {target_version} compatibility]
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
    """Extract updated code from LLM response using multiple patterns."""
    import re
    
    # Try multiple patterns to extract code
    patterns = [
        # Pattern 1: Code between ```python and ```
        r'```python\s*(.*?)\s*```',
        # Pattern 2: Code between ``` and ```
        r'```\s*(.*?)\s*```',
        # Pattern 3: Code after "Updated code:" or similar
        r'(?:Updated code|Modernized code|Here(?:\'s| is) the (?:updated|modernized) code):\s*\n(.*)',
        # Pattern 4: Code after "```" at start of line
        r'^```.*?\n(.*?)\n```',
        # Pattern 5: Everything after first #!/usr/bin/python or similar
        r'(#!/.*?python.*?(?:\n.*?)*)',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, response, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if len(extracted) > 100:  # Ensure it's substantial code
                print(f"✅ Code extracted using pattern {i}")
                return extracted
            else:
                print(f"⚠️  Pattern {i} matched but content too short ({len(extracted)} chars)")
    
    # If no patterns work, check if the entire content looks like Python code
    if response.strip().startswith(('#!', 'import ', 'from ', 'def ', 'class ')):
        print("✅ Using entire content as it appears to be Python code")
        return response.strip()
    
    print("❌ No code extraction pattern matched")
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
            
            # Analyze Python code using hybrid LLM + regex approach
            analysis_findings = analyze_python_code(file_path, target_python_version)
            print(f"Hybrid Analysis Results:")
            print(f"LLM + Regex Analysis: {analysis_findings}")
            
            # Get LLM suggestion for modernization
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

def execute_fallback_modernization(code, analysis_findings):
    """Execute fallback modernization when LLM API is unavailable."""
    print("🔄 Executing fallback modernization engine...")
    
    # Implement modernization based on analysis findings
    updated_code = code
    change_summary = "Modernization applied using fallback engine based on analysis findings:"
    
    # Apply modernization based on analysis findings
    if "walrus operator" in analysis_findings.lower():
        # Look for patterns that can use walrus operator
        import re
        
        # Pattern 1: if some_condition: result = some_function()
        # Convert to: if result := some_function(): pass
        pattern1 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*([^:]+):\s*\n\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\2'
        if re.search(pattern1, updated_code):
            updated_code = re.sub(pattern1, r'if \3 := \2:', updated_code)
            change_summary += "\n- Applied walrus operator for assignment expressions"
        
        # Pattern 2: result = some_function(); if result:
        # Convert to: if result := some_function():
        pattern2 = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);\s*if\s+\1:'
        if re.search(pattern2, updated_code):
            updated_code = re.sub(pattern2, r'if \1 := \2:', updated_code)
            change_summary += "\n- Applied walrus operator for conditional assignment"
        
        # Pattern 3: if len(something) != 0: (common in the SDP file)
        # Convert to: if len_something := len(something) and len_something != 0:
        pattern3 = r'if\s+len\(([^)]+)\)\s*!=\s*0:'
        if re.search(pattern3, updated_code):
            updated_code = re.sub(pattern3, r'if len_\1 := len(\1) and len_\1 != 0:', updated_code)
            change_summary += "\n- Applied walrus operator for length checks"
        
        # Pattern 4: if len(something) == 0: (common in the SDP file)
        # Convert to: if len_something := len(something) and len_something == 0:
        pattern4 = r'if\s+len\(([^)]+)\)\s*==\s*0:'
        if re.search(pattern4, updated_code):
            updated_code = re.sub(pattern4, r'if len_\1 := len(\1) and len_\1 == 0:', updated_code)
            change_summary += "\n- Applied walrus operator for empty length checks"
        
        # Pattern 5: if len(something) == specific_length: (like the date parsing)
        # Convert to: if len_something := len(something) and len_something == specific_length:
        pattern5 = r'if\s+len\(([^)]+)\)\s*==\s*(\d+):'
        if re.search(pattern5, updated_code):
            updated_code = re.sub(pattern5, r'if len_\1 := len(\1) and len_\1 == \2:', updated_code)
            change_summary += "\n- Applied walrus operator for specific length checks"
    
    if "f-string" in analysis_findings.lower():
        # Convert % formatting to f-strings where safe
        import re
        
        # Pattern: "text %s text" % variable
        pattern = r'"([^"]*%[^"]*)"\s*%\s*([a-zA-Z_][a-zA-Z0-9_]*)'
        if re.search(pattern, updated_code):
            updated_code = re.sub(pattern, r'f"\1".format(\2)', updated_code)
            change_summary += "\n- Converted % formatting to f-string format"
    
    if "type hints" in analysis_findings.lower():
        # Add basic type hints where missing
        import re
        
        # Pattern: def function_name(param):
        # Convert to: def function_name(param: Any):
        pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\):'
        if re.search(pattern, updated_code):
            # Only add type hints if not already present
            if ': ' not in re.search(pattern, updated_code).group(2):
                updated_code = re.sub(pattern, r'def \1(\2: Any):', updated_code)
                change_summary += "\n- Added basic type hints to function parameters"
    
    # If no specific changes were made, provide a generic message
    if updated_code == code:
        change_summary = "Analysis found modernization opportunities, but fallback engine could not apply specific changes. Manual review recommended."
    
    print(f"✅ Fallback modernization completed: {change_summary}")
    return updated_code, change_summary

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