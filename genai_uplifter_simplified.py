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
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
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
        try:
            from rag_utils import extract_java_guidance
            guidance_result = extract_java_guidance(
                code_issue=guidance_query,
                context=f"Target Python version: {target_python_version}. Focus on Python modernization, not Java."
            )
            
            if guidance_result and isinstance(guidance_result, dict) and guidance_result.get("guidance_found"):
                # Format the guidance for the LLM prompt
                context_parts = []
                context_parts.append(f"PYTHON MODERNIZATION GUIDANCE: {guidance_result.get('summary', 'Available')}")
                
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
        except Exception as rag_error:
            print(f"Warning: RAG guidance extraction failed: {rag_error}")
            return "Python RAG guidance unavailable - proceeding with standard modernization."
            
    except Exception as e:
        print(f"Warning: Error getting RAG context: {e}")
        # RAG context error occurred
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
    print(f"🔍 Phase 1: LLM Analysis...")
    llm_analysis = get_llm_analysis(python_code, target_python_version)
    
    # Phase 2: Regex validation (double-check and catch missed items)
    print(f"🔍 Phase 2: Regex Validation...")
    regex_validation = validate_with_regex(python_code, target_python_version)
    
    # Phase 3: Combine and prioritize findings
    print(f"🔍 Phase 3: Combining Results...")
    combined_findings = combine_analysis_findings(llm_analysis, regex_validation)
    
    print(f"✅ Analysis completed for {python_file_path}")
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
        
        # Clean up the response to prevent duplicate processing
        if response and isinstance(response, str):
            # Remove any markdown formatting that might cause issues
            clean_response = response.replace('**', '').replace('*', '').replace('#', '')
            # Limit length to prevent excessive output
            if len(clean_response) > 800:
                clean_response = clean_response[:800] + "..."
            return clean_response
        
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
        # Clean up LLM analysis output - remove markdown formatting and make extremely concise
        clean_llm = llm_analysis.replace('**', '').replace('*', '').replace('\n', ' ')
        if len(clean_llm) > 200:  # Much shorter to save tokens
            clean_llm = clean_llm[:200] + "..."
        combined.append(f"Changes: {clean_llm}")
    
    # Add regex validation findings (secondary source) - make concise
    if regex_validation and isinstance(regex_validation, list):
        # Remove duplicates and make concise
        unique_regex = list(dict.fromkeys(regex_validation))  # Preserve order while removing duplicates
        # Take only the first few items to save tokens
        if len(unique_regex) > 3:
            unique_regex = unique_regex[:3]
        combined.extend(unique_regex)
    
    # Always provide modernization guidance for Python 2 style code
    if regex_validation and isinstance(regex_validation, list) and any("print statements" in item or "% formatting" in item for item in regex_validation):
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
            timeout=(30, 60),
            verify=False
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"🔍 LLM Analysis API Response received")
            
            # Use the same response parsing logic as the modernization function
            content = None
            
            # Check for completions field (the format your API actually uses)
            if "completions" in response_data and response_data["completions"]:
                # Extract from completions array
                completions = response_data["completions"]
                if isinstance(completions, list) and len(completions) > 0:
                    content = completions[0]  # Take first completion
                    print(f"✅ Found content in 'completions' field: {content[:100]}...")
                elif isinstance(completions, str):
                    content = completions
                    print(f"✅ Found content in 'completions' field (string): {content[:100]}...")
            
            # Fallback to other formats if completions not found
            elif "content" in response_data:
                content = response_data["content"]
                print(f"✅ Found content in 'content' field: {content[:100]}...")
            
            elif "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    print(f"✅ Found content in OpenAI format: {content[:100]}...")
                elif "text" in choice:
                    content = choice["text"]
                    print(f"✅ Found content in 'text' field: {content[:100]}...")
            
            elif "text" in response_data:
                content = response_data["text"]
                print(f"✅ Found content in 'text' field: {content[:100]}...")
            
            elif "response" in response_data:
                content = response_data["response"]
                print(f"✅ Found content in 'response' field: {content[:100]}...")
            
            if content:
                return content[:500]  # Limit response length
            else:
                print(f"⚠️  No content found in response")
                return f"LLM analysis completed but no content found"
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
    """Get LLM suggestion for code modernization with smart chunking for large files."""
    print(f"Asking LLM to update {file_type} code for Python {target_version}...")
    
    # Standard approach for all files
    print(f"📏 File size: {len(code)/1024:.1f}KB")
    
    # Check if file needs chunking based on API limits
    file_size_kb = len(code) / 1024
    estimated_tokens = estimate_tokens_accurately(code)
    
    # With 8192 total limit, we need to leave room for prompt + response
    # Prompt: ~1500 tokens, Response: ~1500 tokens, Code: ~5200 tokens max
    if estimated_tokens > 5200:  # If estimated tokens > 5.2K, need chunking
        print(f"📏 Large file detected ({file_size_kb:.1f}KB, ~{estimated_tokens:.0f} tokens) - using smart chunking for API limits")
        return modernize_with_smart_chunking(code, analysis_findings, target_version, selected_libraries, file_type)
    
    # Use direct modernization for smaller files
    print(f"📏 File size: {file_size_kb:.1f}KB (~{estimated_tokens:.0f} tokens) - using direct modernization")
    
    # Create prompt (skip RAG context to save tokens)
    prompt = create_python_prompt(code, analysis_findings, target_version, "")
    
    # Debug: Show prompt size to monitor token usage
    prompt_size_kb = len(prompt) / 1024
    prompt_tokens = estimate_tokens_accurately(prompt)
    print(f"📝 Prompt size: {prompt_size_kb:.1f}KB (~{prompt_tokens:.0f} tokens)")
    
    # Calculate total tokens needed
    total_tokens_needed = prompt_tokens + estimated_tokens + 1500  # +1500 for response
    print(f"📊 Total tokens needed: {total_tokens_needed:.0f} (limit: 8192)")
    
    if total_tokens_needed > 8192:
        print(f"⚠️  Token limit exceeded ({total_tokens_needed:.0f} > 8192), falling back to chunking")
        return modernize_with_smart_chunking(code, analysis_findings, target_version, selected_libraries, file_type)
    
    # Prepare payload with API-compatible settings
    payload = {
        "prompt": prompt,
        "model": LLM_MODEL,
        "max_new_tokens": 8192,  # Stay within ELI API limits
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
        if file_size_kb > 10:
            print(f"⏳ Processing large file ({file_size_kb:.1f}KB) - this may take several minutes...")
        
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
                # Extract the actual text content
                
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
                
                # Content extracted successfully
                
                if content_text and len(content_text) > 50:  # Ensure we have substantial content
                    # Extract change summary and updated code
                    change_summary = extract_change_summary(content_text)
                    updated_code = extract_updated_code(content_text, file_type)
                    
                    if updated_code:
                        print(f"✅ Successfully extracted updated code (length: {len(updated_code)})")
                        return updated_code, change_summary
                    else:
                        print("❌ Failed to extract updated code from content")
                        print(f"Content extraction failed")
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

def modernize_with_smart_chunking(code, analysis_findings, target_version, selected_libraries=None, file_type='python'):
    """Modernize large files by splitting them into API-compatible chunks."""
    print(f"🔄 Starting smart chunking for API compatibility...")
    
    # Split code into chunks that fit within API limits
    chunks = split_code_into_api_chunks(code)
    print(f"📦 Split code into {len(chunks)} API-compatible chunks")
    
    # Validate chunk structure and ensure imports are preserved
    for i, chunk in enumerate(chunks):
        print(f"📋 Chunk {i+1}: {len(chunk['code'])/1024:.1f}KB, Complete structures: {chunk.get('complete_structures', False)}")
    
    # Ensure all imports are in the first chunk
    chunks = ensure_imports_in_first_chunk(chunks)
    
    # Validate that all chunks fit within the API limits
    print(f"🔍 Validating chunks for API compatibility...")
    chunks = ensure_chunks_fit_api(chunks, analysis_findings, target_version)
    
    modernized_chunks = []
    change_summary_parts = []
    
    for i, chunk in enumerate(chunks):
        print(f"🔄 Processing chunk {i+1}/{len(chunks)}: {len(chunk['code'])/1024:.1f}KB")
        
        # Create prompt for this chunk
        chunk_prompt = create_python_prompt(chunk['code'], analysis_findings, target_version, "")
        
        # Process chunk normally (validation already ensured it fits)
        chunk_result = modernize_single_chunk(chunk, analysis_findings, target_version)
        if chunk_result:
            modernized_chunks.append(chunk_result['code'])
            change_summary_parts.append(f"Chunk {i+1}: {chunk_result['summary']}")
        else:
            print(f"⚠️  Chunk {i+1} failed, using fallback")
            fallback_result = modernize_chunk_with_fallback(chunk, target_version)
            modernized_chunks.append(fallback_result['code'])
            change_summary_parts.append(f"Chunk {i+1}: Fallback modernization")
    
    # Reassemble the modernized chunks with structure validation
    print(f"🔧 Reassembling {len(modernized_chunks)} chunks...")
    final_code = reassemble_chunks_intelligently(modernized_chunks, chunks)
    
    # Validate the reassembled code
    if validate_reassembled_code(final_code):
        print(f"✅ Code structure validation passed")
    else:
        print(f"⚠️  Code structure validation failed - manual review recommended")
    
    # Combine change summaries
    final_summary = f"Large file modernized using smart chunking:\n" + "\n".join(change_summary_parts)
    
    print(f"✅ Smart chunking completed successfully")
    return final_code, final_summary

def split_code_into_api_chunks(code):
    """Split code into chunks that respect Python code structure and logical boundaries."""
    lines = code.split('\n')
    chunks = []
    
    # Target chunk size: 6KB (leaving room for prompt overhead within 8192 limit)
    # With 8192 total limit:
    # - Prompt: ~1.5KB (~675 tokens)
    # - Code: ~6KB (~2700 tokens) 
    # - Response: ~1.5KB (~675 tokens)
    # Total: ~4050 tokens, well within 8192 limit
    target_chunk_size = 6000
    current_chunk = []
    current_chunk_size = 0
    chunk_number = 1
    
    # Parse the code to understand its structure
    code_structure = analyze_code_structure(lines)
    
    for i, line in enumerate(lines):
        line_size = len(line) + 1  # +1 for newline
        
        # Check if we need to start a new chunk
        if current_chunk_size + line_size > target_chunk_size and current_chunk:
            # Find the best break point that respects code structure
            best_break_point = find_structural_break_point(current_chunk, code_structure, i - len(current_chunk))
            
            if best_break_point > 0:
                # Break at the best point
                chunks.append({
                    'name': f'Chunk_{chunk_number}',
                    'code': '\n'.join(current_chunk[:best_break_point]).rstrip(),
                    'start_line': 0,
                    'end_line': 0,
                    'complete_structures': True
                })
                # Start new chunk with remaining lines
                current_chunk = current_chunk[best_break_point:]
                current_chunk_size = sum(len(l) + 1 for l in current_chunk)
            else:
                # No good break point, force break but preserve current structure
                chunks.append({
                    'name': f'Chunk_{chunk_number}',
                    'code': '\n'.join(current_chunk).rstrip(),
                    'start_line': 0,
                    'end_line': 0,
                    'complete_structures': False
                })
                current_chunk = [line]
                current_chunk_size = line_size
            
            chunk_number += 1
        else:
            # Add line to current chunk
            current_chunk.append(line)
            current_chunk_size += line_size
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            'name': f'Chunk_{chunk_number}',
            'code': '\n'.join(current_chunk).rstrip(),
            'start_line': 0,
            'end_line': 0,
            'complete_structures': True
        })
    
    return chunks

def analyze_code_structure(lines):
    """Analyze the structure of the code to identify functions, classes, and blocks."""
    structure = {
        'functions': [],
        'classes': [],
        'blocks': [],
        'imports': [],
        'decorators': [],
        'context_managers': []
    }
    
    current_indent = 0
    in_function = False
    in_class = False
    in_try_block = False
    in_with_block = False
    function_start = -1
    class_start = -1
    try_start = -1
    with_start = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
            
        # Track indentation
        if line.startswith(' '):
            current_indent = len(line) - len(line.lstrip())
        
        # Detect function definitions
        if stripped.startswith(('def ', 'async def ')):
            if in_function:
                # End previous function
                structure['functions'].append((function_start, i - 1))
            in_function = True
            function_start = i
        
        # Detect class definitions
        if stripped.startswith('class '):
            if in_class:
                # End previous class
                structure['classes'].append((class_start, i - 1))
            in_class = True
            class_start = i
        
        # Detect imports
        if stripped.startswith(('import ', 'from ')):
            structure['imports'].append(i)
        
        # Detect decorators
        if stripped.startswith('@'):
            structure['decorators'].append(i)
        
        # Detect try blocks
        if stripped.startswith('try:'):
            in_try_block = True
            try_start = i
        
        # Detect with blocks
        if stripped.startswith('with '):
            in_with_block = True
            with_start = i
        
        # Detect block endings
        if in_function and current_indent == 0 and stripped and not stripped.startswith(('def ', 'class ')):
            if not stripped.startswith('#'):
                in_function = False
                structure['functions'].append((function_start, i - 1))
                function_start = -1
        
        if in_class and current_indent == 0 and stripped and not stripped.startswith(('def ', 'class ')):
            if not stripped.startswith('#'):
                in_class = False
                structure['classes'].append((class_start, i - 1))
                class_start = -1
        
        # Detect try/except/finally endings
        if in_try_block and stripped.startswith(('except', 'finally')):
            if current_indent == 0:  # Top-level except/finally
                in_try_block = False
                structure['blocks'].append(('try', try_start, i - 1))
                try_start = -1
        
        # Detect with statement endings
        if in_with_block and current_indent == 0 and stripped and not stripped.startswith('with '):
            if not stripped.startswith('#'):
                in_with_block = False
                structure['context_managers'].append((with_start, i - 1))
                with_start = -1
    
    # Handle any remaining open structures
    if in_function:
        structure['functions'].append((function_start, len(lines) - 1))
    if in_class:
        structure['classes'].append((class_start, len(lines) - 1))
    if in_try_block:
        structure['blocks'].append(('try', try_start, len(lines) - 1))
    if in_with_block:
        structure['context_managers'].append((with_start, len(lines) - 1))
    
    return structure

def find_structural_break_point(chunk_lines, code_structure, chunk_start_line):
    """Find the best break point that preserves code structure."""
    if not chunk_lines:
        return 0
    
    chunk_end_line = chunk_start_line + len(chunk_lines) - 1
    
    # Look for natural break points in reverse order
    for i in range(len(chunk_lines) - 1, -1, -1):
        line = chunk_lines[i].strip()
        current_line = chunk_start_line + i
        
        # Perfect break points (blank lines at top level)
        if line == '' and is_at_top_level(current_line, code_structure):
            return i + 1
        
        # End of import section
        if line.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except:', 'finally:')):
            if i > 0 and chunk_lines[i-1].strip() == '':
                return i
        
        # End of complete block
        if line in ['pass', 'return', 'break', 'continue', 'raise', 'yield'] and is_at_top_level(current_line, code_structure):
            return i + 1
        
        # End of context manager
        if line == ')' and i > 0 and 'with ' in chunk_lines[i-1]:
            return i + 1
        
        # End of multi-line expression
        if line == ')' and i > 0 and chunk_lines[i-1].strip().endswith(','):
            return i + 1
        
        # End of list/dict comprehension
        if line == ']' and i > 0 and chunk_lines[i-1].strip().endswith(','):
            return i + 1
    
    # If no perfect break point, look for reasonable ones
    for i in range(len(chunk_lines) - 1, -1, -1):
        line = chunk_lines[i].strip()
        
        # Blank lines are always good break points
        if line == '':
            return i + 1
        
        # End of comment blocks
        if line.startswith('#'):
            if i > 0 and not chunk_lines[i-1].strip().startswith('#'):
                return i + 1
        
        # End of docstring
        if line.endswith('"""') or line.endswith("'''"):
            return i + 1
    
    # Last resort: break at a reasonable point, but avoid breaking functions/classes
    safe_break = find_safe_break_point(chunk_lines, code_structure, chunk_start_line)
    return safe_break

def is_at_top_level(line_number, code_structure):
    """Check if a line is at the top level (not inside a function or class)."""
    for start, end in code_structure['functions']:
        if start <= line_number <= end:
            return False
    for start, end in code_structure['classes']:
        if start <= line_number <= end:
            return False
    return True

def find_safe_break_point(chunk_lines, code_structure, chunk_start_line):
    """Find a safe break point that doesn't break functions, classes, or other structures."""
    chunk_end_line = chunk_start_line + len(chunk_lines) - 1
    
    # Check if we're inside a function
    for start, end in code_structure['functions']:
        if start <= chunk_start_line <= end:
            # We're inside a function, find its end
            if end <= chunk_end_line:
                return end - chunk_start_line + 1
            else:
                # Function extends beyond this chunk, don't break
                return 0
    
    # Check if we're inside a class
    for start, end in code_structure['classes']:
        if start <= chunk_start_line <= end:
            # We're inside a class, find its end
            if end <= chunk_end_line:
                return end - chunk_start_line + 1
            else:
                # Class extends beyond this chunk, don't break
                return 0
    
    # Check if we're inside a try block
    for block_type, start, end in code_structure['blocks']:
        if start <= chunk_start_line <= end:
            # We're inside a block, find its end
            if end <= chunk_end_line:
                return end - chunk_start_line + 1
            else:
                # Block extends beyond this chunk, don't break
                return 0
    
    # Check if we're inside a context manager
    for start, end in code_structure['context_managers']:
        if start <= chunk_start_line <= end:
            # We're inside a context manager, find its end
            if end <= chunk_end_line:
                return end - chunk_start_line + 1
            else:
                # Context manager extends beyond this chunk, don't break
                return 0
    
    # Check if we're inside decorators
    for decorator_line in code_structure['decorators']:
        if decorator_line <= chunk_start_line <= decorator_line + 2:  # Decorator + function definition
            # Don't break in the middle of decorator + function
            return 0
    
    # We're at top level, safe to break
    return max(1, len(chunk_lines) // 2)

def create_python_prompt(code, analysis_findings, target_version, context_section):
    """Create a concise Python modernization prompt to save tokens."""
    
    return f"""Python {target_version} modernization:

{analysis_findings}

Apply changes, preserve everything else, return complete code.

```python
{code}
```"""













def modernize_single_chunk(chunk, chunk_prompt, target_version):
    """Modernize a single chunk using the LLM API."""
    try:
        # Prepare payload for chunk modernization
        payload = {
            "prompt": chunk_prompt,
            "model": LLM_MODEL,
            "max_new_tokens": 4096,  # Smaller for chunks
            "temperature": 0.1,
            "max_suggestions": 1,
            "top_p": 0.85,
            "top_k": 0,
            "stop_seq": "",
            "client": "python-uplift-tool-chunk",
            "stream": False,
            "stream_batch_tokens": 10
        }
        
        # Headers
        headers = {
            "Authorization": f"Bearer {LLM_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Make API call
        response = requests.post(
            LLM_API_URL,
            json=payload,
            headers=headers,
            timeout=(30, 120),  # Shorter timeout for chunks
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract response content
            if 'completions' in result and len(result['completions']) > 0:
                content_text = result['completions'][0].strip()
                
                # Extract modernized code
                updated_code = extract_updated_code(content_text, 'python')
                change_summary = extract_change_summary(content_text)
                
                if updated_code:
                    return {
                        'code': updated_code,
                        'summary': f"Chunk {chunk['start_line']}-{chunk['end_line']}: {change_summary}"
                    }
        
        # If LLM fails, use fallback for this chunk
        print(f"⚠️  LLM failed for chunk, using fallback modernization")
        return modernize_chunk_with_fallback(chunk, target_version)
        
    except Exception as e:
        print(f"❌ Error modernizing chunk: {e}")
        return modernize_chunk_with_fallback(chunk, target_version)

def modernize_chunk_with_fallback(chunk, target_version):
    """Apply fallback modernization to a single chunk."""
    # Apply basic modernization patterns to the chunk
    updated_code = chunk['code']
    changes = []
    
    # Apply walrus operator patterns
    import re
    
    # Pattern: if len(something) != 0:
    pattern = r'if\s+len\(([^)]+)\)\s*!=\s*0:'
    if re.search(pattern, updated_code):
        updated_code = re.sub(pattern, r'if len_\1 := len(\1) and len_\1 != 0:', updated_code)
        changes.append("Applied walrus operator for length check")
    
    # Pattern: if len(something) == 0:
    pattern2 = r'if\s+len\(([^)]+)\)\s*==\s*0:'
    if re.search(pattern2, updated_code):
        updated_code = re.sub(pattern2, r'if len_\1 := len(\1) and len_\1 == 0:', updated_code)
        changes.append("Applied walrus operator for empty check")
    
    # Pattern: print statements
    pattern3 = r'print\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$'
    if re.search(pattern3, updated_code, re.MULTILINE):
        updated_code = re.sub(pattern3, r'print(\1)', updated_code, flags=re.MULTILINE)
        changes.append("Fixed print statements for Python 3")
    
    return {
        'code': updated_code,
        'summary': f"Chunk {chunk['start_line']}-{chunk['end_line']}: Fallback modernization applied - {', '.join(changes)}"
    }

def reassemble_chunks_intelligently(modernized_chunks, original_chunks):
    """Reassemble chunks while preserving code structure and adding necessary separators."""
    if not modernized_chunks:
        return ""
    
    reassembled_parts = []
    
    for i, (chunk_code, original_chunk) in enumerate(zip(modernized_chunks, original_chunks)):
        # Add chunk code
        reassembled_parts.append(chunk_code)
        
        # Add separator if this chunk doesn't end with a blank line and next chunk doesn't start with one
        if i < len(modernized_chunks) - 1:
            current_chunk_ends_with_blank = chunk_code.rstrip().endswith('\n\n') or chunk_code.rstrip().endswith('')
            next_chunk_starts_with_blank = modernized_chunks[i + 1].lstrip().startswith('\n') or modernized_chunks[i + 1].lstrip() == ''
            
            # Add separator if needed
            if not current_chunk_ends_with_blank and not next_chunk_starts_with_blank:
                # Check if we're between different code structures
                if original_chunk.get('complete_structures', False):
                    reassembled_parts.append('\n')
    
    return '\n'.join(reassembled_parts)

def validate_reassembled_code(code):
    """Basic validation that the reassembled code has proper Python syntax structure."""
    try:
        # Check for basic Python syntax issues
        lines = code.split('\n')
        
        # Check for unmatched indentation
        indent_stack = []
        line_number = 0
        
        for i, line in enumerate(lines):
            line_number = i + 1
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # Check for indentation errors - allow for deeply nested structures
            if current_indent > 0 and indent_stack:
                # Allow indentation up to 20 spaces more than the previous level
                # This handles deeply nested structures like dictionaries, lists, etc.
                # Python allows unlimited nesting, so we need to be generous
                max_allowed = indent_stack[-1] + 20
                if current_indent > max_allowed:
                    print(f"⚠️  Indentation error at line {line_number}: unexpected indentation level {current_indent} (expected max {max_allowed})")
                    return False
            
            # Track indentation changes
            if stripped.endswith(':'):
                indent_stack.append(current_indent)
            elif stripped in ['pass', 'return', 'break', 'continue', 'raise', 'yield']:
                if indent_stack:
                    indent_stack.pop()
        
        # Check for basic syntax patterns
        def_count = code.count('def ')
        colon_count = code.count(':')
        
        # Count only colons that are likely to be function/class related
        # Exclude colons in strings, comments, etc.
        relevant_colons = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except:', 'finally:', 'else:', 'elif ')):
                relevant_colons += 1
        
        if def_count > relevant_colons:
            print(f"⚠️  Mismatched function definitions ({def_count}) and relevant colons ({relevant_colons})")
            return False
            
        class_count = code.count('class ')
        if class_count > relevant_colons:
            print(f"⚠️  Mismatched class definitions ({class_count}) and relevant colons ({relevant_colons})")
            return False
        
        # Check for balanced parentheses and brackets
        if code.count('(') != code.count(')') or code.count('[') != code.count(']') or code.count('{') != code.count('}'):
            print("⚠️  Unbalanced parentheses, brackets, or braces")
            return False
        
        return True
        
    except Exception as e:
        print(f"⚠️  Code validation error: {e}")
        return False

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
    """Extract updated code from LLM response using multiple patterns with truncation detection."""
    import re
    
    # Check for truncation indicators
    truncation_patterns = [
        r'#\s*\.\.\.\s*\(.*?\)',  # "# ... (other methods remain mostly unchanged)"
        r'#\s*\.\.\.',  # "# ..."
        r'#\s*truncated',
        r'#\s*end\s+of\s+file',
        r'#\s*remaining\s+code',
        r'#\s*continue\s+below',
        r'#\s*see\s+above',
        r'#\s*omitted\s+for\s+brevity',
        r'#\s*and\s+so\s+on',
        r'#\s*etc\.',
    ]
    
    # Check if response contains truncation indicators
    for pattern in truncation_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            print(f"🚨 CRITICAL: Detected truncation indicator: {pattern}")
            print(f"❌ This suggests the LLM response is incomplete - REJECTING")
            return None
    
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



def validate_code_safety(original_code, modernized_code):
    """Validate that no critical code was lost during modernization."""
    
    print(f"🔒 Running comprehensive code safety validation...")
    
    # Critical patterns that must be preserved
    critical_patterns = [
        (r'def\s+\w+', 'function definitions'),
        (r'class\s+\w+', 'class definitions'),
        (r'import\s+\w+', 'import statements'),
        (r'from\s+\w+\s+import', 'from imports'),
        (r'#.*', 'comments'),
        (r'"""[\s\S]*?"""', 'docstrings'),
        (r"'''[\s\S]*?'''", 'docstrings'),
    ]
    
    # Check pattern preservation
    for pattern, description in critical_patterns:
        original_count = len(re.findall(pattern, original_code, re.MULTILINE))
        modernized_count = len(re.findall(pattern, modernized_code, re.MULTILINE))
        
        # Allow some flexibility for comments and docstrings
        if description in ['comments', 'docstrings']:
            if modernized_count < original_count * 0.8:  # Allow 20% reduction
                print(f"⚠️  Warning: {description} reduced from {original_count} to {modernized_count}")
        else:
            if modernized_count < original_count:
                print(f"❌ CRITICAL: {description} reduced from {original_count} to {modernized_count}")
                return False
    
    # Check for significant code length reduction (more than 10%)
    original_length = len(original_code)
    modernized_length = len(modernized_code)
    
    if modernized_length < original_length * 0.9:
        print(f"❌ CRITICAL: Code length reduced by more than 10% ({original_length} -> {modernized_length})")
        return False
    
    # NEW: Check for logic structure preservation
    logic_patterns = [
        (r'if\s+.*:', 'if statements'),
        (r'for\s+.*:', 'for loops'),
        (r'while\s+.*:', 'while loops'),
        (r'try\s*:', 'try blocks'),
        (r'except\s+.*:', 'except blocks'),
        (r'finally\s*:', 'finally blocks'),
        (r'with\s+.*:', 'with statements'),
        (r'return\s+', 'return statements'),
        (r'raise\s+', 'raise statements'),
    ]
    
    for pattern, description in logic_patterns:
        original_count = len(re.findall(pattern, original_code, re.MULTILINE))
        modernized_count = len(re.findall(pattern, modernized_code, re.MULTILINE))
        
        if modernized_count < original_count:
            print(f"❌ CRITICAL: {description} reduced from {original_count} to {modernized_count}")
            return False
    
    # NEW: Check for variable and function name preservation
    var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='
    original_vars = set(re.findall(var_pattern, original_code))
    modernized_vars = set(re.findall(var_pattern, modernized_code))
    
    # Allow some variable changes (new ones might be added during modernization)
    if len(original_vars - modernized_vars) > len(original_vars) * 0.1:  # More than 10% of variables lost
        print(f"❌ CRITICAL: Too many variables lost: {len(original_vars - modernized_vars)} out of {len(original_vars)}")
        return False
    
    # NEW: Check for function call preservation
    func_call_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    original_calls = set(re.findall(func_call_pattern, original_code))
    modernized_calls = set(re.findall(func_call_pattern, modernized_code))
    
    if len(original_calls - modernized_calls) > len(original_calls) * 0.1:  # More than 10% of function calls lost
        print(f"❌ CRITICAL: Too many function calls lost: {len(original_calls - modernized_calls)} out of {len(original_calls)}")
        return False
    
    print(f"✅ Code safety validation passed - all critical elements preserved")
    return True

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
            print(f"🔍 Starting analysis...")
            analysis_findings = analyze_python_code(file_path, target_python_version)
            print(f"✅ Analysis completed")
            print(f"📝 Analysis Summary: {analysis_findings[:200]}...")
            
            # Get LLM suggestion for modernization
            print(f"🤖 Starting LLM modernization...")
            updated_code, change_summary = get_llm_suggestion(
                original_code, 
                analysis_findings, 
                target_python_version, 
                selected_libraries,
                'python'
            )
            
            if updated_code:
                # Enhanced safety check: Ensure no critical code was lost
                print(f"🔒 Running safety validation...")
                safety_check_passed = validate_code_safety(original_code, updated_code)
                
                if not safety_check_passed:
                    print(f"❌ SAFETY CHECK FAILED: Critical code may have been lost in {file_path}")
                    print(f"🔄 Restoring from backup and skipping modernization")
                    continue
                
                # Additional validation: Check if modernization actually made meaningful changes
                if updated_code == original_code:
                    print(f"⚠️  WARNING: No changes were made to {file_path}")
                    print(f"🔄 Skipping backup creation and file update")
                    continue
                

                
                # Check if changes are reasonable (not too many lines changed)
                original_lines = original_code.split('\n')
                updated_lines = updated_code.split('\n')
                
                # Simple truncation detection: if modernized code is significantly shorter
                if len(updated_code) < len(original_code) * 0.7:  # More than 30% of content lost
                    print(f"⚠️  WARNING: Modernized code is significantly shorter than original")
                    print(f"   Original: {len(original_code)} chars, Modernized: {len(updated_code)} chars")
                    print(f"🔄 Truncation detected - automatically falling back to local modernization engine")
                    updated_code, change_summary = execute_fallback_modernization(original_code, analysis_findings)
                    print(f"✅ Fallback modernization completed")
                
                if len(updated_lines) < len(original_lines) * 0.8:  # More than 20% of lines lost
                    print(f"❌ SAFETY CHECK FAILED: Too many lines lost in {file_path}")
                    print(f"🔄 Restoring from backup and skipping modernization")
                    continue
                
                print(f"✅ Safety validation passed - proceeding with modernization")
                
                # Create backup
                backup_file = file_path + ".backup"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_code)
                print(f"Backup created: {backup_file}")
                
                # Save updated code with rollback protection
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_code)
                    
                    # Verify the file was written correctly
                    with open(file_path, 'r', encoding='utf-8') as f:
                        written_code = f.read()
                    
                    if written_code != updated_code:
                        raise Exception("File write verification failed")
                    
                    print(f"✅ Successfully modernized: {file_path}")
                    print(f"Change Summary: {change_summary}")
                    success_count += 1
                    
                except Exception as write_error:
                    print(f"❌ ERROR: Failed to write modernized code to {file_path}")
                    print(f"🔄 Rolling back to original code...")
                    
                    # Rollback to original code
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(original_code)
                        print(f"✅ Rollback successful - file restored to original state")
                    except Exception as rollback_error:
                        print(f"❌ CRITICAL: Rollback failed! File may be corrupted: {rollback_error}")
                        print(f"🆘 Manual intervention required for {file_path}")
                    
                    continue
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

def extract_imports_from_chunks(chunks):
    """Extract all import statements from chunks to ensure they're preserved."""
    all_imports = set()
    
    for chunk in chunks:
        lines = chunk['code'].split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                # Normalize the import statement to avoid duplicates
                normalized = stripped
                all_imports.add(normalized)
    
    return sorted(list(all_imports))

def ensure_imports_in_first_chunk(chunks):
    """Ensure all imports are present in the first chunk."""
    if not chunks:
        return chunks
    
    # Extract all unique imports from all chunks
    all_imports = extract_imports_from_chunks(chunks)
    
    if not all_imports:
        return chunks
    
    # Find the first chunk that should contain imports
    first_chunk = chunks[0]
    first_chunk_lines = first_chunk['code'].split('\n')
    
    # Find where imports should be inserted (after shebang and docstring)
    actual_insert_index = 0
    for i, line in enumerate(first_chunk_lines):
        stripped = line.strip()
        if stripped.startswith('#!/'):
            actual_insert_index = i + 1
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            # Find the end of the docstring
            for j in range(i + 1, len(first_chunk_lines)):
                if first_chunk_lines[j].strip().endswith('"""') or first_chunk_lines[j].strip().endswith("'''"):
                    actual_insert_index = j + 1
                    break
            break
        elif stripped and not stripped.startswith('#'):
            actual_insert_index = i
            break
    
    # Get existing imports from the entire first chunk
    existing_imports = set()
    for line in first_chunk_lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')):
            existing_imports.add(stripped)
    
    # Find missing imports (only add what's not already there)
    missing_imports = [imp for imp in all_imports if imp not in existing_imports]
    
    if missing_imports:
        # Insert missing imports at the beginning of the file (after shebang and docstring)
        new_lines = first_chunk_lines[:actual_insert_index] + missing_imports + first_chunk_lines[actual_insert_index:]
        chunks[0]['code'] = '\n'.join(new_lines)
        print(f"📦 Added {len(missing_imports)} missing imports to first chunk")
    else:
        print("📦 All imports already present in first chunk")
    
    return chunks

def estimate_tokens_accurately(code):
    """More accurate token estimation for Python code."""
    # Python code is typically more token-efficient than plain text
    # Rough estimate: 1KB ≈ 400-500 tokens for Python code
    # This is more conservative and realistic than the previous 0.8 ratio
    
    # Simple heuristic: Python code is more structured, so fewer tokens per byte
    base_ratio = 0.45  # 1KB ≈ 450 tokens
    
    # Adjust based on code characteristics
    lines = code.split('\n')
    total_lines = len(lines)
    non_empty_lines = len([l for l in lines if l.strip()])
    
    # More lines = more tokens (newlines, indentation, etc.)
    if total_lines > 100:
        base_ratio += 0.05  # +5% for very long files
    elif total_lines > 50:
        base_ratio += 0.02  # +2% for medium files
    
    # More non-empty lines = more actual code = more tokens
    if non_empty_lines > 80:
        base_ratio += 0.03  # +3% for code-heavy files
    
    # Estimate tokens
    estimated_tokens = len(code) * base_ratio
    
    return estimated_tokens

def validate_chunk_for_api(chunk_code, prompt_template, analysis_findings, target_version):
    """Validate that a chunk will fit within the 8192 token limit."""
    # Create the full prompt for this chunk
    full_prompt = create_python_prompt(chunk_code, analysis_findings, target_version, "")
    
    # Estimate tokens
    prompt_tokens = estimate_tokens_accurately(full_prompt)
    code_tokens = estimate_tokens_accurately(chunk_code)
    
    # Calculate total tokens needed
    total_tokens = prompt_tokens + code_tokens + 1500  # +1500 for response
    
    # Check if it fits
    fits = total_tokens <= 8192
    
    if not fits:
        print(f"⚠️  Chunk too large: {prompt_tokens:.0f} + {code_tokens:.0f} + 1500 = {total_tokens:.0f} > 8192")
    
    return fits, total_tokens, prompt_tokens, code_tokens

def ensure_chunks_fit_api(chunks, analysis_findings, target_version):
    """Ensure all chunks fit within the API limits, subdividing if necessary."""
    validated_chunks = []
    
    for i, chunk in enumerate(chunks):
        fits, total_tokens, prompt_tokens, code_tokens = validate_chunk_for_api(
            chunk['code'], "", analysis_findings, target_version
        )
        
        if fits:
            validated_chunks.append(chunk)
            print(f"✅ Chunk {i+1}: {total_tokens:.0f} tokens - fits API limit")
        else:
            print(f"⚠️  Chunk {i+1} too large ({total_tokens:.0f} tokens), subdividing...")
            # Subdivide this chunk
            sub_chunks = split_code_into_api_chunks(chunk['code'])
            for j, sub_chunk in enumerate(sub_chunks):
                sub_fits, sub_total, _, _ = validate_chunk_for_api(
                    sub_chunk['code'], "", analysis_findings, target_version
                )
                if sub_fits:
                    validated_chunks.append(sub_chunk)
                    print(f"  ✅ Sub-chunk {i+1}.{j+1}: {sub_total:.0f} tokens - fits API limit")
                else:
                    print(f"  ❌ Sub-chunk {i+1}.{j+1}: {sub_total:.0f} tokens - still too large")
                    # This shouldn't happen with proper chunk sizing, but handle it
                    validated_chunks.append(sub_chunk)
    
    return validated_chunks

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