#!/usr/bin/env python3
"""
Test script to verify LLM response format fix and debug API response structure.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LLM_API_URL = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/llm/generate"
LLM_MODEL = os.getenv("LLM_MODEL", "Mistral-12b")
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN", "")

def test_llm_api_response():
    """Test the LLM API and check the response format."""
    
    if not LLM_API_TOKEN:
        print("❌ LLM_API_TOKEN not set. Please set it in your .env file.")
        return False
    
    # Simple test prompt
    test_prompt = """
You are a helpful assistant. Please respond with a simple "Hello, World!" message.

Format your response as:
<test_response>
Hello, World!
</test_response>
"""
    
    try:
        headers = {
            "Authorization": f"Bearer {LLM_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "prompt": test_prompt,
            "temperature": 0.1,
            "max_tokens": 100
        }
        
        print(f"🔍 Testing LLM API with model: {LLM_MODEL}")
        print(f"🔍 API URL: {LLM_API_URL}")
        print(f"🔍 Payload keys: {list(payload.keys())}")
        
        response = requests.post(LLM_API_URL, headers=headers, json=payload, verify=False)
        
        print(f"🔍 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"🔍 Response structure: {list(result.keys())}")
            
            # Check for documented API response format
            print(f"🔍 Expected fields: message, status, time_elapsed, completions, model")
            
            if 'completions' in result:
                print(f"✅ Found 'completions' format with {len(result['completions'])} items")
                if len(result['completions']) > 0:
                    print(f"✅ Completion text: {result['completions'][0][:100]}...")
            else:
                print("❌ Missing 'completions' field (expected per API documentation)")
            
            if 'message' in result:
                print(f"✅ API message: {result['message']}")
            if 'status' in result:
                print(f"✅ API status: {result['status']}")
            if 'time_elapsed' in result:
                print(f"✅ Time elapsed: {result['time_elapsed']}")
            
            # Test the response parsing logic based on documented format
            llm_response = None
            
            # Primary: Use 'completions' format as documented in API spec
            if 'completions' in result and len(result['completions']) > 0:
                llm_response = result['completions'][0].strip()
                print(f"✅ Successfully extracted from 'completions' field")
            
            # Fallback: Try 'choices' format for compatibility
            elif 'choices' in result and len(result['choices']) > 0:
                if 'message' in result['choices'][0]:
                    llm_response = result['choices'][0]['message']['content']
                else:
                    llm_response = result['choices'][0].get('text', '')
                print(f"⚠️  Using fallback 'choices' format")
            
            if llm_response:
                print(f"✅ Successfully extracted response: {llm_response[:200]}...")
                return True
            else:
                print("❌ Failed to extract response from any format")
                print(f"🔍 Full response: {json.dumps(result, indent=2)}")
                return False
                
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LLM API: {e}")
        return False

if __name__ == "__main__":
    print("=== LLM API Response Format Test ===")
    success = test_llm_api_response()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The API response format fix should work correctly.")
    else:
        print("\n❌ Test failed!")
        print("Please check your API token and network connection.") 