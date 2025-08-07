import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RAG API Configuration
RAG_API_URL = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/rag/query"
RAG_FILTERS_URL = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/rag/search_filters"
RAG_API_TOKEN = os.getenv("RAG_API_TOKEN", os.getenv("LLM_API_TOKEN", ""))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_available_libraries():
    """
    Get available libraries from the RAG filters API (dynamic, real-time).
    This calls the actual ELI API to get current CPI libraries.
    """
    if not RAG_API_TOKEN:
        logger.error("RAG_API_TOKEN not configured")
        return {"error": "RAG API token not configured"}
    
    try:
        headers = {
            "Authorization": f"Bearer {RAG_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        params = {
            "user_id": "system",
            "customer_profile_id": "ericssonuser"
        }
        
        logger.info("Fetching available libraries from RAG filters API...")
        response = requests.get(RAG_FILTERS_URL, headers=headers, params=params, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            search_filters = data.get("search_filters", {})
            
            logger.info(f"Successfully retrieved {len(search_filters)} library categories from RAG API")
            
            # Return the actual libraries from the API
            return search_filters
            
        else:
            logger.error(f"RAG Filters API error: {response.status_code} - {response.text[:200]}")
            # Fallback to minimal proven libraries only if API fails
            return get_fallback_libraries()
            
    except Exception as e:
        logger.error(f"RAG Filters API exception: {e}")
        # Fallback to minimal proven libraries only if API fails
        return get_fallback_libraries()

def get_fallback_libraries():
    """
    Minimal fallback libraries (only if RAG API is completely unavailable).
    These are the proven libraries from your testing.
    """
    return {
        "Proven Java Libraries (Fallback)": {
            "EN/LZN 741 0077 R32A": "Charging Control Node (CCN) 6.17.0 - Proven Java content",
            "EN/LZN 702 0372 R2A": "JavaSIP 4.1 - Proven Java content",
            "EN/LZN 741 0171 R32A": "Online Charging Control (OCC) 3.21.0 - Proven Java content"
        }
    }

def query_rag_api(query, max_evidences=5, library_priority="high_priority"):
    """
    Query the RAG API with real Ericsson Java libraries.
    
    Args:
        query (str): The search query
        max_evidences (int): Maximum number of evidences to return
        library_priority (str): Priority level - "high_priority", "secondary", "fallback", or "all"
    
    Returns:
        dict: RAG API response containing evidences and generated answer
    """
    if not RAG_API_TOKEN:
        logger.error("RAG_API_TOKEN or LLM_API_TOKEN not configured")
        return {"evidences": [], "answer": "RAG API token not configured", "error": True}
    
    # Get libraries based on priority
    java_libraries = get_ericsson_java_libraries()
    
    if library_priority == "high_priority":
        libraries = java_libraries["high_priority"]
    elif library_priority == "secondary":
        libraries = java_libraries["high_priority"] + java_libraries["secondary"]
    elif library_priority == "fallback":
        libraries = java_libraries["fallback"]
    elif library_priority == "all":
        libraries = (java_libraries["high_priority"] + 
                    java_libraries["secondary"] + 
                    java_libraries["fallback"])
    else:
        libraries = java_libraries["high_priority"]  # Default
    
    # Prepare RAG request (using proven working configuration)
    rag_request = {
        "index_name": "*",
        "query": query,
        "top_k": 10,
        "num_rag_evidences": max_evidences,
        "rerank": True,
        "generate_answer": True,
        "user_id": "system",
        "customer_profile_id": "ericssonuser", 
        "client": "jdk-uplift-tool",
        "cpi_library_id": libraries
    }
    
    headers = {
        "Authorization": f"Bearer {RAG_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Querying RAG API with {len(libraries)} libraries: {query}")
        response = requests.post(RAG_API_URL, headers=headers, json=rag_request, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            evidences = data.get("evidences", [])
            answer = data.get("answer", "")
            
            logger.info(f"RAG query successful: {len(evidences)} evidences found")
            
            # If no results with high priority, try secondary libraries
            if not evidences and library_priority == "high_priority":
                logger.info("No results with high priority libraries, trying secondary...")
                return query_rag_api(query, max_evidences, "secondary")
            
            # If still no results with secondary, try without library filtering
            if not evidences and library_priority == "secondary":
                logger.info("No results with secondary libraries, trying without filtering...")
                return query_rag_api_no_filter(query, max_evidences)
            
            return {
                "evidences": evidences,
                "answer": answer,
                "libraries_used": libraries,
                "query": query,
                "success": True
            }
        else:
            logger.error(f"RAG API error: {response.status_code} - {response.text[:200]}")
            return {
                "evidences": [],
                "answer": f"RAG API error: {response.status_code}",
                "error": True,
                "libraries_used": libraries
            }
            
    except Exception as e:
        logger.error(f"RAG API exception: {e}")
        return {
            "evidences": [],
            "answer": f"RAG API exception: {str(e)}",
            "error": True,
            "libraries_used": libraries
        }

def query_rag_api_no_filter(query, max_evidences=5):
    """
    Query RAG API without library filtering as fallback.
    
    Args:
        query (str): The search query
        max_evidences (int): Maximum number of evidences to return
    
    Returns:
        dict: RAG API response
    """
    rag_request = {
        "index_name": "*",
        "query": query,
        "top_k": 10,
        "num_rag_evidences": max_evidences,
        "rerank": True,
        "generate_answer": True,
        "user_id": "system",
        "customer_profile_id": "ericssonuser",
        "client": "jdk-uplift-tool"
        # No cpi_library_id filter
    }
    
    headers = {
        "Authorization": f"Bearer {RAG_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Querying RAG API without library filtering: {query}")
        response = requests.post(RAG_API_URL, headers=headers, json=rag_request, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            evidences = data.get("evidences", [])
            answer = data.get("answer", "")
            
            logger.info(f"RAG query (no filter) successful: {len(evidences)} evidences found")
            
            return {
                "evidences": evidences,
                "answer": answer,
                "libraries_used": "all_libraries",
                "query": query,
                "success": True,
                "fallback_mode": True
            }
        else:
            logger.error(f"RAG API error (no filter): {response.status_code}")
            return {
                "evidences": [],
                "answer": f"RAG API error: {response.status_code}",
                "error": True
            }
            
    except Exception as e:
        logger.error(f"RAG API exception (no filter): {e}")
        return {
            "evidences": [],
            "answer": f"RAG API exception: {str(e)}",
            "error": True
        }

def extract_java_guidance(code_issue, context=""):
    """
    Extract Java modernization guidance by querying what content actually exists.
    Instead of asking for specific modernization, ask about Java topics that exist.
    """
    # Define queries based on what Java content actually exists in Ericsson libraries
    base_java_queries = [
        "Java collections",                    # ✅ Proven to work (8 evidences found)
        "Java security",                       # ✅ Found in CCN library
        "Java environment",                    # ✅ Found in CCN library  
        "Java performance",                    # ✅ Likely in performance-focused libraries
        "Java memory management",              # ✅ Found garbage collection content
        "Java threading concurrency",         # ✅ May exist in server libraries
        "Java API design patterns",           # ✅ May exist in API libraries
        "Java configuration",                 # ✅ May exist in OaM libraries
    ]
    
    # Also try code-issue specific queries if they're about specific Java features
    specific_queries = []
    code_lower = code_issue.lower()
    
    if "vector" in code_lower or "arraylist" in code_lower or "collection" in code_lower:
        specific_queries.extend(["Java collections Vector", "Java List Vector"])
    
    if "deprecated" in code_lower:
        specific_queries.extend(["Java deprecated", "Java API deprecated"])
    
    if "security" in code_lower:
        specific_queries.extend(["Java security", "Java certificate"])
    
    if "thread" in code_lower or "synchronized" in code_lower:
        specific_queries.extend(["Java threading", "Java synchronization"])
    
    # Try specific queries first, then general Java topics
    all_queries = specific_queries + base_java_queries
    
    all_evidences = []
    all_guidance = []
    query_results = {}
    
    for query in all_queries[:4]:  # Limit to first 4 queries to avoid too many API calls
        try:
            logger.info(f"Querying for Java content: {query}")
            rag_response = query_rag_api(query, max_evidences=3, library_priority="high_priority")
            
            if not rag_response.get("error"):
                evidences = rag_response.get("evidences", [])
                if evidences:
                    all_evidences.extend(evidences)
                    query_results[query] = len(evidences)
                    logger.info(f"Found {len(evidences)} evidences for '{query}'")
                else:
                    logger.info(f"No evidences found for '{query}'")
            
            # Don't overwhelm the API - small delay between queries
            import time
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error querying '{query}': {e}")
            continue
    
    # If we found content, process it
    if all_evidences:
        # Remove duplicates based on doc_text
        seen_content = set()
        unique_evidences = []
        for evidence in all_evidences:
            content_snippet = evidence.get("doc_text", "")[:100]  # First 100 chars as key
            if content_snippet not in seen_content:
                seen_content.add(content_snippet)
                unique_evidences.append(evidence)
        
        # Process evidences to extract actionable guidance
        guidance_items = []
        for evidence in unique_evidences[:5]:  # Top 5 unique evidences
            doc_text = evidence.get("doc_text", "")
            library_title = evidence.get("cpi_library_title", "Unknown Library")
            section_title = evidence.get("section_title", "Unknown Section")
            score = evidence.get("score", 0)
            
            guidance_items.append({
                "source": f"{library_title} - {section_title}",
                "content": doc_text[:400] + "..." if len(doc_text) > 400 else doc_text,
                "relevance_score": score,
                "library": library_title
            })
        
        return {
            "guidance_found": True,
            "summary": f"Found guidance on {len(unique_evidences)} Java topics.",
            "detailed_guidance": guidance_items,
            "query_used": ", ".join(all_queries),
            "libraries_searched": [evidence.get("cpi_library_title") for evidence in unique_evidences],
            "total_evidences": len(unique_evidences)
        }
    else:
        return {
            "guidance_found": False,
            "message": "No guidance found for the specified Java issue",
            "query_used": ", ".join(all_queries),
            "libraries_searched": [],
            "total_evidences": 0
        }

def test_rag_connection():
    """Test RAG API connection with a simple query."""
    test_query = "Java collections best practices"
    result = query_rag_api(test_query, max_evidences=2, library_priority="high_priority")
    
    if result.get("error"):
        return False, f"RAG API connection failed: {result['answer']}"
    
    evidences = result.get("evidences", [])
    if evidences:
        return True, f"RAG API working - found {len(evidences)} evidences"
    else:
        return True, "RAG API connected but no test content found"

# Backwards compatibility - keep existing function name
def get_rag_guidance(query, max_results=5):
    """
    Legacy function for backwards compatibility.
    """
    result = query_rag_api(query, max_evidences=max_results)
    
    if result.get("error"):
        return []
    
    evidences = result.get("evidences", [])
    
    # Convert to legacy format
    guidance_items = []
    for evidence in evidences:
        guidance_items.append({
            "content": evidence.get("doc_text", ""),
            "source": evidence.get("cpi_library_title", "Unknown"),
            "section": evidence.get("section_title", "Unknown"),
            "relevance": evidence.get("score", 0)
        })
    
    return guidance_items

def get_ericsson_java_libraries():
    """
    Get Java-relevant libraries dynamically from RAG API.
    Returns prioritized libraries based on proven Java content.
    """
    try:
        # Get all available libraries from RAG API
        all_libraries = get_available_libraries()
        
        if "error" in all_libraries:
            # Fallback to proven libraries if API unavailable
            return get_proven_java_libraries()
        
        # Extract Java-related libraries from the dynamic response
        java_libraries = {
            "high_priority": [],
            "secondary": [],
            "fallback": []
        }
        
        # Define Java-related categories and keywords
        java_categories = ["CAL Store - CBA", "CPI Store - Ericsson Charging 22.11"]
        java_keywords = ["java", "charging", "oam", "sip", "ccn", "occ"]
        
        for category, libraries in all_libraries.items():
            if not isinstance(libraries, dict):
                continue
                
            for lib_id, lib_title in libraries.items():
                # Check if library is likely to contain Java content
                is_java_related = (
                    any(keyword in lib_title.lower() for keyword in java_keywords) or
                    category in java_categories or
                    "java" in lib_id.lower()
                )
                
                if is_java_related:
                    # Prioritize based on proven libraries from testing
                    if lib_id in ["EN/LZN 741 0077 R32A", "EN/LZN 702 0372 R2A", "EN/LZN 741 0171 R32A"]:
                        java_libraries["high_priority"].append(lib_id)
                    elif "java" in lib_title.lower() or "charging" in lib_title.lower():
                        java_libraries["secondary"].append(lib_id)
                    else:
                        java_libraries["fallback"].append(lib_id)
        
        # Ensure we have at least the proven libraries
        if not java_libraries["high_priority"]:
            proven_libs = get_proven_java_libraries()
            java_libraries["high_priority"] = proven_libs["high_priority"]
        
        return java_libraries
        
    except Exception as e:
        logger.error(f"Error getting dynamic Java libraries: {e}")
        return get_proven_java_libraries()

def get_proven_java_libraries():
    """
    Fallback to the proven libraries from your testing.
    Only used when dynamic API calls fail.
    """
    return {
        "high_priority": [
            "EN/LZN 741 0077 R32A",   # Charging Control Node (CCN) 6.17.0 - PROVEN
            "EN/LZN 702 0372 R2A",    # JavaSIP 4.1 - PROVEN
            "EN/LZN 741 0171 R32A",   # Online Charging Control (OCC) 3.21.0 - PROVEN
        ],
        "secondary": [
            "EN/LZN 702 0336 R2A",    # JavaOaM 6.1
            "EN/LZN 741 0076 R32A",   # Charging Control Node (CCN) 6.17.0
            "EN/LZN 765 0164/9 P35C", # vMTAS
        ],
        "fallback": [
            "EN/LZN 703 0289 R98A",   # Ericsson Orchestrator EVNFM 23.6.2
            "EN/LZN 702 0520/1 R116A" # Cloud Core Exposure Server (CCES)
        ]
    }