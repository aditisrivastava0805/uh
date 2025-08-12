#!/usr/bin/env python3
"""
Local configuration for development without Ericsson internal network access.
This file provides fallback API configurations when the internal hostname is unreachable.
"""

# Local Development Configuration
LOCAL_CONFIG = {
    # Fallback API URLs for local development
    "rag_api_url": "http://localhost:8000/api/rag/query",
    "rag_filters_url": "http://localhost:8000/api/rag/search_filters",
    "llm_api_url": "http://localhost:8000/api/llm/generate",
    
    # Alternative: Use public API services (uncomment if you have access)
    # "rag_api_url": "https://api.openai.com/v1/chat/completions",
    # "rag_filters_url": "https://api.openai.com/v1/models",
    # "llm_api_url": "https://api.openai.com/v1/chat/completions",
    
    # Environment settings
    "environment": "local",
    "debug": True,
    "use_fallback": True
}

# Function to get configuration
def get_local_config():
    """Get local configuration settings."""
    return LOCAL_CONFIG

# Function to check if we should use fallback
def should_use_fallback():
    """Check if we should use fallback configuration."""
    return LOCAL_CONFIG.get("use_fallback", True)

if __name__ == "__main__":
    print("Local Configuration:")
    print("=" * 50)
    for key, value in LOCAL_CONFIG.items():
        print(f"{key}: {value}")
    
    print(f"\nUse fallback: {should_use_fallback()}") 