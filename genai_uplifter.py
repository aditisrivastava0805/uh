import subprocess
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import requests
import json
import urllib3
# Update the import to match your new rag_utils functions
from rag_utils import extract_java_guidance, get_ericsson_java_libraries, test_rag_connection

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()
LLM_API_URL = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/llm/generate"
LLM_MODEL = os.getenv("LLM_MODEL", "Mistral-12b")
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN", "")

# Maven POM Template
POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example.modernizer</groupId>
    <artifactId>modernizer-check</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>{java_version}</maven.compiler.source>
        <maven.compiler.target>{java_version}</maven.compiler.target>
        <modernizer.javaVersion>{java_version}</modernizer.javaVersion>
    </properties>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>${{maven.compiler.source}}</source>
                    <target>${{maven.compiler.target}}</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.gaul</groupId>
                <artifactId>modernizer-maven-plugin</artifactId>
                <version>2.7.0</version>
                <configuration>
                    <javaVersion>${{modernizer.javaVersion}}</javaVersion>
                    <failOnViolations>false</failOnViolations>
                </configuration>
                <executions>
                    <execution>
                        <id>modernizer</id>
                        <phase>verify</phase>
                        <goals>
                            <goal>modernizer</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
"""

def initialize_llm_api():
    """Check if LLM API token is available."""
    if not LLM_API_TOKEN:
        print("Warning: LLM_API_TOKEN environment variable not set.")
        print("Please set LLM_API_TOKEN in your .env file.")
        return False
    return True

def get_rag_context(java_code, modernizer_findings, target_jdk_version, selected_libraries=None):
    """
    Get RAG context using the new rag_utils functions.
    This maintains backward compatibility with the existing interface.
    """
    try:
        # Create a summary of the modernization needs
        modernization_summary = f"Java {target_jdk_version} modernization needed"
        if modernizer_findings and "violations" in modernizer_findings.lower():
            modernization_summary += f": {modernizer_findings}"
        
        # Use the new extract_java_guidance function
        guidance_result = extract_java_guidance(
            code_issue=modernization_summary,
            context=f"Target JDK: {target_jdk_version}"
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

def get_package_path(java_code):
    """Extracts package path from Java source code."""
    package_match = re.search(r"^\s*package\s+([\w.]+);", java_code, re.MULTILINE)
    return package_match.group(1).replace('.', '/') if package_match else ""

def get_class_name_from_source(java_code):
    """Extracts the main class name from Java source code."""
    match = re.search(r"public\s+class\s+([A-Za-z0-9_]+)", java_code) or re.search(r"class\s+([A-Za-z0-9_]+)", java_code)
    return match.group(1) if match else None

def analyze_with_modernizer(java_file_path, target_jdk_version):
    """Runs modernizer-maven-plugin to find API usage needing modernization."""
    print(f"Analyzing {java_file_path} with Modernizer for Java {target_jdk_version}...")
    
    # Check if Maven is available
    try:
        result = subprocess.run(["mvn", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return "Maven not found in PATH - Modernizer analysis skipped. Proceeding with LLM-only modernization."
    except FileNotFoundError:
        return "Maven not found in PATH - Modernizer analysis skipped. Proceeding with LLM-only modernization."
    
    try:
        with open(java_file_path, 'r') as f:
            java_code = f.read()
    except Exception as e:
        print(f"Error reading Java file: {e}")
        return f"Error reading Java file: {e}"

    temp_dir = tempfile.mkdtemp(prefix="modernizer_")
    print(f"Created temp directory: {temp_dir}")

    try:
        # Set up Maven project structure
        src_main_java_path = os.path.join(temp_dir, "src", "main", "java")
        package_path = get_package_path(java_code)
        target_dir = os.path.join(src_main_java_path, package_path) if package_path else src_main_java_path
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy Java file and create POM
        file_name = os.path.basename(java_file_path)
        shutil.copy(java_file_path, os.path.join(target_dir, file_name))
        with open(os.path.join(temp_dir, "pom.xml"), "w") as f:
            f.write(POM_TEMPLATE.format(java_version=target_jdk_version))

        # Run Maven
        stdout, stderr, returncode = run_command(["mvn", "-B", "clean", "verify"], working_dir=temp_dir)
        
        # Check for report or parse output for errors
        report_path = os.path.join(temp_dir, "target", "modernizer-report.xml")
        if os.path.exists(report_path):
            # Parse XML report
            tree = ET.parse(report_path)
            violations = []
            for violation in tree.findall(".//violation"):
                name = violation.find("name").text
                comment = violation.find("comment").text
                locations = []
                for loc in violation.findall(".//location"):
                    line = loc.get("lineNumber")
                    source_file = loc.get("sourceFile")
                    locations.append(f"at {source_file}:L{line}")
                violations.append(f"- {name}: {comment} ({', '.join(locations)})")
            
            return "Modernizer found no violations." if not violations else "Modernizer found the following issues:\n" + "\n".join(violations)
        else:
            # Try to extract errors from Maven output
            modernizer_errors = []
            for line in stdout.splitlines():
                if "[ERROR]" in line and "Prefer" in line:
                    error_parts = line.split(": ", 1)
                    if len(error_parts) > 1:
                        file_line = error_parts[0].split("/")[-1]
                        message = error_parts[1]
                        modernizer_errors.append(f"- {message} (at {file_line})")
            
            if modernizer_errors:
                return "Modernizer found the following issues:\n" + "\n".join(modernizer_errors)
            elif "No violations found" in stdout:
                return "Modernizer found no violations."
            else:
                return "Modernizer report not found. Check if Modernizer ran correctly."
    except Exception as e:
        return f"Error during Modernizer analysis: {e}"
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

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

def get_llm_suggestion(java_code, modernizer_findings, target_jdk_version, selected_libraries=None):
    """Gets suggestions from LLM API for code modernization with RAG context."""
    print(f"Asking LLM to update code for JDK {target_jdk_version}...")
    
    # Check RAG connection
    rag_connected, rag_status = test_rag_connection()
    if not rag_connected:
        print(f"Warning: RAG API not available - {rag_status}")
        print("Proceeding with LLM-only modernization.")
    
    # Get RAG context if available
    rag_context = ""
    if rag_connected and selected_libraries:
        try:
            rag_context = get_rag_context(java_code, modernizer_findings, target_jdk_version, selected_libraries)
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
Note: No Ericsson-specific context was retrieved. Proceed with standard Java modernization patterns.
"""
    
    prompt = f"""
You are a Java expert specializing in CONSERVATIVE code modernization from older Java versions to newer ones.

CRITICAL REQUIREMENTS:
1. MAINTAIN EXACT FUNCTIONALITY - Do NOT fix bugs, errors, or improve logic
2. PRESERVE ALL EXISTING BEHAVIOR - Even if the code appears wrong or suboptimal
3. ONLY modernize APIs, syntax, and deprecated elements for Java {target_jdk_version} compatibility
4. If code doesn't compile due to missing dependencies, leave it as-is
5. If code has logical errors, preserve those errors exactly

The following Java code needs MINIMAL updates for Java {target_jdk_version} compatibility.
Modernizer static analysis found these modernization opportunities:

<modernizer_findings>
{modernizer_findings}
</modernizer_findings>

{context_section}

Your task is to ONLY:
- Replace deprecated APIs with their modern equivalents (same behavior)
- Update syntax that won't compile in Java {target_jdk_version}
- Address specific issues from Modernizer findings
- Consider Ericsson-specific patterns from the provided context
- Keep ALL other code exactly as-is, including any bugs or compilation issues

DO NOT:
- Fix compilation errors unless they're due to deprecated APIs
- Improve algorithms or logic
- Add missing imports or dependencies
- Fix potential null pointer exceptions
- Optimize performance
- Change variable names or code structure
- Add error handling

PRESERVE EXACTLY:
- All variable names and types
- All method signatures
- All logic flow and conditions
- Any existing bugs or issues
- All comments and formatting

Format your response as:

<change_summary>
[Brief summary of ONLY the modernization changes made, referencing Modernizer findings. If no changes needed, state "No modernization required."]
</change_summary>

<updated_code>
```java
[Updated Java code with MINIMAL changes for Java {target_jdk_version} compatibility]
```
</updated_code>

Original Java code:
```java
{java_code}
```
"""
    
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
            "client": "jdk-uplift-tool",
            "stream": False,
            "stream_batch_tokens": 10
        }
        
        response = requests.post(LLM_API_URL, headers=headers, json=payload, verify=False)
        
        if response.status_code != 200:
            print(f"Error from LLM API: {response.status_code} - {response.text}")
            return None, f"Error from LLM API: {response.status_code} - {response.text}"
        
        # Safety checks here:
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            return None, f"Failed to parse JSON response: {e}"
            
        if "completions" not in response_json:
            print(f"No 'completions' key in response: {response_json}")
            return None, f"Unexpected API response format: {response_json}"
            
        if not response_json["completions"]:
            print("Empty completions array in response")
            return None, "No completions returned from LLM API"
            
        response_text = response_json["completions"][0].strip()
        
        # Safety check for empty response
        if not response_text:
            print("Empty response text from LLM")
            return None, "Empty response from LLM API"
        
        # Extract summary
        summary_match = re.search(r"<change_summary>(.*?)</change_summary>", response_text, re.DOTALL)
        change_summary = summary_match.group(1).strip() if summary_match else "LLM did not provide a structured summary."

        # Extract code
        code_match = re.search(r"<updated_code>\s*```java\n(.*?)\n```\s*</updated_code>", response_text, re.DOTALL)
        if code_match:
            updated_code = code_match.group(1).strip()
        else:
            # Try alternative code block formats
            code_block_match = re.search(r"```java\n(.*?)\n```", response_text, re.DOTALL)
            if code_block_match:
                updated_code = code_block_match.group(1).strip()
            else:
                # Last resort cleanup
                cleaned_response = re.sub(r"<change_summary>.*?</change_summary>", "", response_text, flags=re.DOTALL).strip()
                cleaned_response = re.sub(r"<updated_code>.*?</updated_code>", "", cleaned_response, flags=re.DOTALL).strip()
                
                if "```java" in cleaned_response:
                    updated_code = cleaned_response.split("```java", 1)[-1].split("```", 1)[0].strip()
                else:
                    updated_code = None
        
        return updated_code, change_summary
        
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None, f"Error calling LLM API: {e}"

def display_libraries_cli():
    """
    Display available libraries in CLI and allow user selection.
    This is only used for CLI mode - web interface handles library selection separately.
    """
    print("Available Java libraries for RAG context:")
    
    # Get the proven working libraries
    available_libraries = get_ericsson_java_libraries()
    
    # Handle different return types from get_ericsson_java_libraries()
    if isinstance(available_libraries, dict) and "high_priority" in available_libraries:
        high_priority_libs = available_libraries["high_priority"]
    else:
        # Fallback to hardcoded proven libraries
        high_priority_libs = [
            "EN/LZN 741 0077 R32A",   # Charging Control Node (CCN) 6.17.0
            "EN/LZN 702 0372 R2A",    # JavaSIP 4.1
            "EN/LZN 741 0171 R32A",   # Online Charging Control (OCC) 3.21.0
        ]
    
    # Display libraries with descriptions
    library_descriptions = {
        "EN/LZN 741 0077 R32A": "Charging Control Node (CCN) 6.17.0 - Has Java Security, Java Environment",
        "EN/LZN 702 0372 R2A": "JavaSIP 4.1 - Has Migration Scenarios with Java content",
        "EN/LZN 741 0171 R32A": "Online Charging Control (OCC) 3.21.0 - Java-heavy system",
        "EN/LZN 702 0336 R2A": "JavaOaM 6.1 - Java Operations & Maintenance",
        "EN/LZN 741 0076 R32A": "Charging Control Node (CCN) 6.17.0",
        "EN/LZN 765 0164/9 P35C": "vMTAS - Has some Java content"
    }
    
    print("\nProven Java libraries (recommended):")
    for i, lib_id in enumerate(high_priority_libs, 1):
        description = library_descriptions.get(lib_id, "Java library")
        print(f"{i}. {lib_id}: {description}")
    
    print(f"{len(high_priority_libs) + 1}. Use all proven libraries")
    print(f"{len(high_priority_libs) + 2}. Skip RAG context (LLM only)")
    
    while True:
        try:
            choice = input(f"\nSelect libraries (1-{len(high_priority_libs) + 2}), or comma-separated numbers: ").strip()
            
            if not choice:
                print("Using all proven libraries by default.")
                return high_priority_libs
            
            # Handle comma-separated choices
            if ',' in choice:
                choices = [int(x.strip()) for x in choice.split(',')]
                selected = []
                for c in choices:
                    if 1 <= c <= len(high_priority_libs):
                        selected.append(high_priority_libs[c-1])
                if selected:
                    print(f"Selected {len(selected)} libraries for RAG context.")
                    return selected
                else:
                    print("No valid libraries selected.")
                    continue
            
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(high_priority_libs):
                selected_lib = high_priority_libs[choice_num - 1]
                print(f"Selected library: {selected_lib}")
                return [selected_lib]
            elif choice_num == len(high_priority_libs) + 1:
                print("Using all proven Java libraries.")
                return high_priority_libs
            elif choice_num == len(high_priority_libs) + 2:
                print("Skipping RAG context - using LLM only.")
                return []
            else:
                print("Invalid choice. Please try again.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return []

def run_cli_uplift():
    """
    Run the uplift process in CLI mode with library selection.
    """
    print("=== JDK Uplift Tool - CLI Mode ===")
    
    # Check API token
    if not initialize_llm_api():
        print("Error: LLM_API_TOKEN not configured. Please set it in your .env file.")
        return False
    
    # Test RAG connection
    rag_connected, rag_status = test_rag_connection()
    print(f"RAG API Status: {rag_status}")
    
    # Get target JDK version
    print("\nEnter target JDK version (e.g., 11, 17, 21):")
    target_jdk = input("Target JDK: ").strip()
    if not target_jdk:
        print("Error: Target JDK version is required.")
        return False
    
    # Get Java file path
    print("\nEnter path to Java file to uplift:")
    java_file = input("Java file path: ").strip()
    if not java_file or not os.path.exists(java_file):
        print("Error: Java file not found.")
        return False
    
    # Select libraries for RAG context
    selected_libraries = []
    if rag_connected:
        print("\n=== Library Selection ===")
        selected_libraries = display_libraries_cli()
    else:
        print("⚠️  RAG API not available - proceeding with LLM-only modernization")
    
    print(f"\n=== Processing {java_file} for JDK {target_jdk} ===")
    
    try:
        # Read original code
        with open(java_file, 'r') as f:
            original_code = f.read()
        
        print(f"Original code length: {len(original_code)} characters")
        
        # Analyze with Modernizer
        print("\n--- Running Modernizer Analysis ---")
        modernizer_findings = analyze_with_modernizer(java_file, target_jdk)
        if modernizer_findings is None:
            modernizer_findings = "Modernizer analysis unavailable"
        
        print(f"Modernizer findings: {modernizer_findings}")
        
        # Get LLM suggestion with RAG context
        print("\n--- Getting LLM Suggestions ---")
        updated_code, change_summary = get_llm_suggestion(original_code, modernizer_findings, target_jdk, selected_libraries)
        
        if updated_code:
            # Create backup
            backup_file = java_file + ".backup"
            with open(backup_file, 'w') as f:
                f.write(original_code)
            print(f"Backup created: {backup_file}")
            
            # Save updated code
            with open(java_file, 'w') as f:
                f.write(updated_code)
            
            print(f"\n=== Results ===")
            print(f"Change Summary: {change_summary}")
            print(f"Updated file: {java_file}")
            print(f"Backup file: {backup_file}")
            
            return True
        else:
            print(f"\nError: Failed to get LLM suggestions")
            return False
            
    except Exception as e:
        print(f"Error during uplift process: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        success = run_cli_uplift()
        sys.exit(0 if success else 1)
    else:
        print("JDK Uplift Tool")
        print("Usage: python genai_uplifter.py --cli")
        print("This will run the uplift process in interactive CLI mode.")
        print("\nFor web interface, run: python orchestrator.py")